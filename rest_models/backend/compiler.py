# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging
from collections import namedtuple

from django.db.models.lookups import Exact, In, IsNull, Lookup, Range
from django.db.models.sql.compiler import SQLCompiler as BaseSQLCompiler
from django.db.models.sql.constants import MULTI
from django.db.models.sql.where import SubqueryConstraint, WhereNode
from django.db.utils import ProgrammingError
from rest_models.backend.exceptions import FakeDatabaseDbAPI2
from rest_models.router import RestModelRouter

logger = logging.getLogger(__name__)

Alias = namedtuple('Alias', 'model,parent,field,attrname,m2m')
"""
:param model: the model representing the table
:param parent: the parent (recursive Alias)
:param field: the field on the parent model that link to the current model
:param attrname: the name of the attrubute for the parent model to link to us
:param m2m: bool that tell us if this is a many2many table.
"""


def extract_exact_pk_value(where):
    """
    check if the where node given represent a exclude(val=Model) node, which seem
    more complicated, but can be passed as is to the api
    :param django.db.models.sql.where.WhereNode where: the where node
    :return: the real is exact
    """
    if len(where.children) == 2:
        exact, isnull = where.children

        if (isinstance(exact, Exact) and isinstance(isnull, IsNull) and
                exact.lhs.target == isnull.lhs.target):
            return exact
    return None


class QueryParser(object):
    """
    an object helper that parse a attached query to return the
    models, attributes and fields from the list of aliases and select.
    """

    def __init__(self, query):
        """
        :param django.db.models.sql.query.Query query: the query
        :param list[Col] select: the list of select
        """
        self.query = query
        self._aliases = None
        """
        the dict to store aliases giving the tuple
        :type: dict[str, Alias]
        """

    @property
    def aliases(self):
        """
        :rtype: dict[str, Alias]
        """
        if self._aliases is None:
            self._aliases = self._build_aliases()
        return self._aliases

    def _build_aliases(self):
        aliases = {}
        query = self.query
        alias_not_resolved = list(query.alias_map.values())
        current_fail = 0
        m2m_resolved = {}
        while alias_not_resolved and current_fail <= len(alias_not_resolved):
            table = alias_not_resolved.pop()
            """:type: django.db.models.sql.datastructures.Join | django.db.models.sql.datastructures.BaseTable"""

            if table.parent_alias is None:
                # this is the base table
                aliases[table.table_alias] = Alias(query.model, None, None, None, None)
                current_fail = 0
                continue

            try:
                m2m_field = None
                if table.join_field.related_model._meta.auto_created:
                    # no need to add the M2M table table.
                    for m2m in table.join_field.model._meta.local_many_to_many:
                        if getattr(table.join_field.model, m2m.name).through == table.join_field.related_model:
                            # m2m is the M2M field that created the current join
                            m2m_resolved[table.table_alias] = m2m, aliases[table.parent_alias]
                            m2m_field = m2m
                            break

                # not M2M relathionship, but may be folowing previous m2m
                if table.parent_alias in m2m_resolved:
                    field, parent = m2m_resolved[table.parent_alias]
                    # expand the previous alias that is useless
                else:
                    field, parent = table.join_field, aliases[table.parent_alias]
                aliases[table.table_alias] = Alias(table.join_field.related_model, parent,
                                                   field, field.name, m2m_field)
                current_fail = 0
            except KeyError:
                # the table parent is not already resolved
                alias_not_resolved.insert(0, table)
                current_fail += 1
        if alias_not_resolved:
            raise ProgrammingError(
                "impossible to resolve table hierachy: %s" % [a.__dict__ for a in query.alias_map.values()])
        return aliases

    def get_rest_path_for_col(self, col):
        """
        return the path relative to the current query for the given columin
        :param django.db.models.sql.Col col: the column
        :return:
        """
        path, att_name = self.resolve_path(col)
        return ".".join(tuple(path) + (att_name,))

    def resolve_path(self, col):
        """
        resolve the path giving the ressource path as a list.
        :rtype: tuple[str], str
        """
        # current = Alias = NamedTuple(model,parent,field,attrname,m2m)
        current = self.aliases[col.alias]  # type: Alias
        if current.m2m is not None:
            final_att_name = current.m2m.name
            current = current.parent
        else:
            final_att_name = col.target.name

        ancestors = [current]

        while current.parent is not None:
            current = current.parent
            ancestors.insert(0, current)
        # ancesstors is a list of aliass
        attrs = []
        for alias in ancestors:
            if alias.attrname is not None:
                attrs.append(alias.attrname)

        return tuple(attrs), final_att_name

    def flaten_where_clause(self, where_node):
        """
        take the where_node, and flatend it into a list of (negated, lookup),
        :param WhereNode where_node:
        :return: the list of lookup, with a bool telling us if it's negated, and if it was a and
        :rtype: list[tuple[bool, bool, Lookup]]
        """
        res = []
        for child in where_node.children:

            if isinstance(child, WhereNode):
                exact_pk_value = extract_exact_pk_value(child)
                if exact_pk_value is not None:
                    res.append((child.negated, where_node.connector == 'AND', exact_pk_value))
                else:
                    res.extend(self.flaten_where_clause(child))
            else:
                res.append((where_node.negated, where_node.connector == 'AND', child))
        return res

    def get_ressources_for_cols(self, cols):
        """
        return the list of ressources used and the list of attrubutes for each cols
        :param list[django.db.models.expressions.Col] cols: the list of Col
        :return:
        """
        resolved = [self.resolve_path(col) for col in cols]
        return {r[0] for r in resolved}, {r[0] + (r[1],) for r in resolved}

    def resolve_ids(self):
        """
        read the query and resolve the ids if the query is a simple one. return None if it's impossible and it require
        a query on the api to fetch the ids.
        :return: the list of ids found, or None if it was not possible to find out.
        """
        ids = None
        first_connector = None
        # we check if this is a OR all along, or if it's mixed with AND.
        # if there is only one AND, it's ok
        # if there is all OR, it's ok
        # if there is AND and OR, so it will break
        for negated, is_and, lookup in self.flaten_where_clause(self.query.where):
            if first_connector is None:
                first_connector = is_and
            if negated or not lookup.rhs_is_direct_value() or first_connector != is_and:
                return None
            if lookup.lhs.field != self.query.get_meta().pk:
                return None
            if isinstance(lookup, Exact):
                to_add = {lookup.rhs}
            elif isinstance(lookup, In):
                to_add = set(lookup.rhs)
            elif isinstance(lookup, Range):
                to_add = set(range(lookup.rhs[0], lookup.rhs[1] + 1))
            else:
                return None
            if ids is None:
                ids = to_add
            elif is_and:
                ids &= to_add
            else:
                ids |= to_add
        if not ids:
            return None
        return ids


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
        self.query_parser = QueryParser(query)

    def setup_query(self):
        super(SQLCompiler, self).setup_query()
        self.check_compatibility()

    def is_api_model(self):
        return RestModelRouter.is_api_model(self.query.model)

    def compile(self, node, select_format=False):
        return None

    def get_ressource_path(self, model, pk=None):
        """
        return the ressource path relative to the base of the api.
        it use ressource_path and ressource_path, and fallback to the get_ressource_name()
        :param model: the model
        :return: the path of the ressource
        :rtype: str
        """
        ret = getattr(model.APIMeta, 'ressource_path', None) or self.get_ressource_name(model, False)
        if pk is not None:
            ret += "/%s/" % pk
        return ret

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

    def check_compatibility(self):
        """
        check if the query is not using some feathure that we don't provide
        :param django.db.models.sql.query.Query query:
        :return: nothing
        :raise: NotSupportedError
        """
        query = self.query
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
            is_simple_lookup = len(where.children) == 1

            exact_pk_value = extract_exact_pk_value(where)
            if exact_pk_value is not None:
                pass
            elif is_simple_lookup or (is_and and not is_negated):
                for child in where.children:
                    if isinstance(child, WhereNode):
                        where_nodes.append(child)
                    elif isinstance(child, Lookup):
                        if not child.rhs_is_direct_value():
                            raise FakeDatabaseDbAPI2.NotSupportedError(
                                "nested queryset is not supported"
                            )
                    elif isinstance(child, SubqueryConstraint):
                        raise FakeDatabaseDbAPI2.NotSupportedError(
                            "nested queryset is not supported"
                        )
                    else:  # pragma: no cover
                        raise ProgrammingError("unknown type for compiling the query : %s."
                                               " expeced a Lookup or WhereNode" % child.__class__)
            else:

                reason = "NOT (.. AND ..)" if is_negated else "OR"
                raise FakeDatabaseDbAPI2.NotSupportedError(
                    "%s in queryset is not supported yet" % reason
                )

    def build_filter_params(self):
        """
        build the GET parameters to pass for DREST alowing to filter the results.
        :param django.db.models.sql.query.Query query:
        :return: the dict to pass to params for requests to filter results
        :rtype: dict[unicode, unicode]
        """
        res = {}
        query = self.query
        for negated, _, lookup in self.query_parser.flaten_where_clause(query.where):  # type: bool, Lookup
            negated_mark = "-" if negated else ""
            field = self.query_parser.get_rest_path_for_col(lookup.lhs)
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

    def build_include_exclude_params(self):
        """
        build the parameters to eclude/include some data from the serializers
        :param django.db.models.sql.query.Query query:
        :return: the dict to pass to params for requests to exclude some fields
        :rtype: dict[unicode, unicode]
        """
        if self.select is None:
            return {}
        ressources, fields = self.query_parser.get_ressources_for_cols([col for col, _, _ in self.select])
        res = {
            'exclude[]': {".".join(r + ('*',)) for r in ressources},
            'include[]': {".".join(r) for r in fields},
        }
        return res

    def build_sort_params(self):
        """
        build the sort param from the order_by provided by the query
        :param django.db.models.sql.query.Query query:  the query to inspect
        :return: a dict with or without the sort[]
        :rtype: dict[str, str]
        """
        res = {}
        query = self.query
        if query.order_by:
            res['sort[]'] = [lookup.replace('__', '.') for lookup in query.order_by]
        return res

    def build_params(self):
        params = {}
        params.update(self.build_filter_params())
        params.update(self.build_include_exclude_params())
        params.update(self.build_sort_params())
        return params

    # #####################################
    #       real query for select
    # #####################################

    def resolve_ids(self):
        """
        attempt to resolve the ids for the current query. if the query is too complex to guess the ids,
        it will execute the query to get the ids
        :return:
        """
        ids = self.query_parser.resolve_ids()
        if ids is None:

            pk_name = self.query.get_meta().pk.name
            result = self.connection.connection.get(
                self.get_ressource_path(self.query.model),
                params={'exclude[]': '*', 'include[]': pk_name}
            )
            if result.status_code != 200:
                raise ProgrammingError("error while querying the database : %s" % result.text)
            ids = {res['id'] for res in result.json()[self.get_ressource_name(self.query.model, many=True)]}
        return ids

    def execute_sql(self, result_type=MULTI):
        self.setup_query()

    def results_iter(self, results=None):
        """
        Returns an iterator over the results from executing this query.
        """
        raise


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
                for field in opts.concrete_fields:
                    setattr(old, field.attname, field.to_python(new[field.name]))
        else:
            result_json = None
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
                result_json = response.json()
                new = result_json[self.get_ressource_name(query.model, many=False)]
                for field in opts.concrete_fields:
                    setattr(obj, field.attname, field.to_python(new[field.name]))

            if return_id and result_json:
                return result_json[self.get_ressource_name(query.model, many=False)][opts.pk.column]


class SQLDeleteCompiler(SQLCompiler):
    def execute_sql(self, result_type=MULTI):
        if self.is_api_model():

            q = self.query
            if self.query.get_meta().auto_created:
                pass  # we don't care about many2many table, the api will clean it for us
            else:
                for id in self.resolve_ids():
                    result = self.connection.connection.delete(
                        self.get_ressource_path(q.model, pk=id),
                    )
                    if result.status_code not in (200, 202, 204):
                        raise ProgrammingError("the deletion was unseccesfull : %s" % result.text)


class SQLUpdateCompiler(SQLCompiler):
    pass


class SQLAggregateCompiler(SQLCompiler):
    pass
