# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.models.sql.constants import MULTI, NO_RESULTS, SINGLE
from django.db.models.sql.compiler import SQLCompiler as BaseSQLCompiler
from django.db.models.sql.where import WhereNode
from django.db.models.lookups import Lookup
from django.db.utils import ProgrammingError

from rest_models.backend.exceptions import FakeDatabaseDbAPI2

logger = logging.getLogger(__name__)


class SQLCompiler(BaseSQLCompiler):
    def __init__(self, query, connection, using):
        """
        :param django.db.models.sql.query.Query query: the query
        :param rest_models.backend.base.DatabaseWrapper connection: the connection
        :param str using:
        """
        self.query = query
        self.connection = connection
        self.using = using
        self.quote_cache = {'*': '*'}
        # The select, klass_info, and annotations are needed by QuerySet.iterator()
        # these are set as a side-effect of executing the query. Note that we calculate
        # separately a list of extra select columns needed for grammatical correctness
        # of the query, but these columns are not included in self.select.
        self.select = None
        self.annotation_col_map = None
        self.klass_info = None
        self.subquery = False
        # check if this query is compatible with the fact the we don't support OR
        self.check_compatibility(query)

    def compile(self, node, select_format=False):
        return None

    def get_ressource_path(self, model):
        """
        return the ressource path relative to the base of the api.
        it use ressource_path and ressource_path, and fallback to the get_ressource_name()
        :param model: the model
        :return: the path of the ressource
        :rtype: str
        """
        return getattr(model.APIMeta, 'ressource_path', None) or self.get_ressource_name(model, False)

    def get_ressource_name(self, model, many=False):
        """
        return the name of the ressource on the server
        if multi is True, it's the url for the «many» models, so we add a «s».
        the resulotion try first to check the APIMeta resource_name and resource_name_plural. if it don't exists,
        it will guess the value from the model name.(lower)
        :param model: the model
        :param bool many: if true, the url of many results
        :return: the ressource name (plural if needed)
        :rtype: str
        """
        if many:
            return getattr(model.APIMeta, 'resource_name_plural', None) or model.__name__.lower() + 's'
        else:
            return getattr(model.APIMeta, 'resource_name', None) or model.__name__.lower()

    def check_compatibility(self, query):
        """
        check if the query is not using some feathure that we don't provide
        :param django.db.models.sql.query.Query query:
        :return: nothing
        :raise: NotSupportedError
        """
        if query.group_by is not None:
            raise FakeDatabaseDbAPI2.NotSupportedError('group by is not supported')
        if query.distinct:
            raise FakeDatabaseDbAPI2.NotSupportedError('distinct is not supported')
        # check where
        where_nodes = [query.where]
        while where_nodes:
            where = where_nodes.pop()
            is_and = where.connector == 'AND'
            is_negated = where.negated
            # AND xor negated
            if len(where.children) == 1 or (is_and and not is_negated):
                for child in where.children:
                    if isinstance(child, WhereNode):
                        where_nodes.append(child)
                    elif isinstance(child, Lookup):
                        if not child.rhs_is_direct_value():
                            raise FakeDatabaseDbAPI2.NotSupportedError(
                                "nested queryset is not supported"
                            )
                    else:
                        raise ProgrammingError("unknown type for compiling the query : %s."
                                               " expeced a Lookup or WhereNode" % child.__class__)
            else:

                reason = "NOT (.. AND ..)" if is_negated else "OR"
                raise FakeDatabaseDbAPI2.NotSupportedError(
                    "%s in queryset is not supported yet" % reason
                )

    def flaten_where_clause(self, where_node):
        """
        take the where_node, and flatend it into a list of (negated, lookup),
        :param WhereNode where_node:
        :return: the list of lookup, with a bool telling us if it's negated
        :rtype: list[tuple[bool, Lookup]]
        """
        res = []
        for child in where_node.children:
            if isinstance(child, WhereNode):
                res.extend(self.flaten_where_clause(child))
            else:
                res.append((where_node.negated, child))
        return res

    def build_filter_params(self, query):
        """
        build the GET parameters to pass for DREST alowing to filter the results.
        :param django.db.models.sql.query.Query query:
        :return: the dict to pass to params for requests to filter results
        :rtype: dict[unicode, unicode]
        """
        res = {}

        for negated, lookup in self.flaten_where_clause(query.where):  # type: bool, Lookup
            negated_mark = "-" if negated else ""
            field = lookup.lhs.field.name
            if lookup.lookup_name == 'exact':  # implicite lookup is not needed
                fieldname = field
            else:
                fieldname = "{field}.{lookup}".format(field=field, lookup=lookup.lookup_name)
            key = 'filter{%s%s}' % (negated_mark, fieldname)
            if isinstance(lookup.rhs, (tuple, list)):
                res.setdefault(key, []).extend(lookup.rhs)
            else:
                res.setdefault(key, []).append(lookup.rhs)
        return res

    def build_include_exclude_params(self, query):
        """
        build the parameters to eclude/include some data from the serializers
        :param django.db.models.sql.query.Query query:
        :return: the dict to pass to params for requests to exclude some fields
        :rtype: dict[unicode, unicode]
        """

        opts = query.get_meta()
        """:type: django.db.models.options.Options"""

        select_fields = {col.target.name for col, _, _ in self.select}
        model_fields = {f.name for f in opts.concrete_fields}
        if select_fields == model_fields:
            res = {
                'include[]': '*'
            }
        else:
            res = {
                'exclude[]': '*',
                'include[]': [col.field.name for col, _, _ in self.select]
            }
        return res

    def build_sort_params(self, query):
        """
        build the sort param from the order_by provided by the query
        :param django.db.models.sql.query.Query query:  the query to inspect
        :return: a dict with or without the sort[]
        :rtype: dict[str, str]
        """
        res = {}
        if query.order_by:
            res['sort[]'] = [lookup.replace('__', '.') for lookup in query.order_by]
        return res

    def build_params(self, query):
        params = {}
        params.update(self.build_filter_params(query))
        params.update(self.build_include_exclude_params(query))
        params.update(self.build_sort_params(query))
        return params

    # #####################################
    #       real query for select
    # #####################################

    def execute_sql(self, result_type=MULTI):
        self.setup_query()

    def results_iter(self, results=None):
        """
        Returns an iterator over the results from executing this query.
        """
        if self.query.model.__name__ == "ModelA":
            yield (13,)
            yield (14,)
            yield (15,)
        elif self.query.model.__name__ == "ModelB":
            yield (1, 13)
            yield (2, 14)


class SQLInsertCompiler(SQLCompiler):
    def execute_sql(self, return_id=False):
        query = self.query
        """:type: django.db.models.sql.subqueries.InsertQuery"""
        opts = query.get_meta()
        can_bulk = not return_id and self.connection.features.has_bulk_insert

        query_objs = query.objs
        if can_bulk:
            # bulk insert
                data = [
                    {
                        f.column: f.get_db_prep_save(
                            getattr(obj, f.attname) if query.raw else f.pre_save(obj, True),
                            connection=self.connection
                        )
                        for f in query.fields
                    }
                    for obj in query_objs
                ]

                json = {
                    self.get_ressource_name(query.model, many=True): data
                }
                response = self.connection.connection.post(
                    self.get_ressource_path(self.query.model),
                    json=json
                )
                if response.status_code != 201:
                    raise FakeDatabaseDbAPI2.ProgrammingError(
                        "error while creating %d %s.\n%s" %
                        (len(query_objs), opts.verbose_name, response.json()['errors'])
                    )
                result_json = response.json()
                for old, new in zip(query_objs, result_json[self.get_ressource_name(query.model, many=True)]):
                    setattr(old, opts.pk.attname, new[opts.pk.attname])
        else:
            result = None
            for obj in query_objs:
                data = {
                    f.column: f.get_db_prep_save(
                        getattr(obj, f.attname) if query.raw else f.pre_save(obj, True),
                        connection=self.connection
                    )
                    for f in query.fields
                }

                json = {
                    self.get_ressource_name(query.model, many=False): data
                }
                response = self.connection.connection.post(
                    self.get_ressource_path(self.query.model),
                    json=json
                )
                if response.status_code != 201:
                    raise FakeDatabaseDbAPI2.ProgrammingError("error while creating %s.\n%s" % (obj, response.text))
                result = response.json()

            if return_id and result:
                return result[self.get_ressource_name(query.model, many=False)][opts.pk.column]


class SQLDeleteCompiler(SQLCompiler):
    def execute_sql(self, result_type=MULTI):
        q = self.query
        self.connection.connection.delete(
            self.get_ressource_name(q.model, many=True),
            params=self.build_params(q),
        )


class SQLUpdateCompiler(SQLCompiler):
    pass


class SQLAggregateCompiler(SQLCompiler):
    pass
