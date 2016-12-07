# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import logging
import re
from collections import namedtuple

from django.core.exceptions import ImproperlyConfigured
from django.db.models.aggregates import Count
from django.db.models.base import ModelBase
from django.db.models.expressions import Col, RawSQL
from django.db.models.lookups import Exact, In, IsNull, Lookup, Range
from django.db.models.query import EmptyResultSet
from django.db.models.sql.compiler import SQLCompiler as BaseSQLCompiler
from django.db.models.sql.constants import CURSOR, MULTI, NO_RESULTS, ORDER_DIR, SINGLE
from django.db.models.sql.where import SubqueryConstraint, WhereNode
from django.db.utils import NotSupportedError, OperationalError, ProgrammingError

from rest_models.backend.connexion import build_url
from rest_models.backend.exceptions import FakeDatabaseDbAPI2
from rest_models.backend.utils import message_from_response
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
AliasTree = namedtuple('AliasTree', 'alias,children')
"""
a recursive struct that provide a représentation of all the aliases

:param Alias alias: the current alias
:param list[AliasTree] childs: the child alias tree
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

        if (
            isinstance(exact, Exact) and isinstance(isnull, IsNull) and
            exact.lhs.target == isnull.lhs.target
        ):
            return exact
    return None


def pgcd(a, b):
    """
    return the best page size for a given limited query
    :param a: the start offset
    :param b: the end offset
    :return:
    """
    while a % b != 0:
        a, b = b, a % b
    return b


def get_resource_path(model, pk=None):
    """
    return the resource path relative to the base of the api.
    it use resource_path and resource_path, and fallback to the get_resource_name()
    :param model: the model
    :return: the path of the resource
    :rtype: str
    """
    ret = getattr(model.APIMeta, 'resource_path', None) or get_resource_name(model, False)
    if pk is not None:
        ret += "/%s/" % pk
    return ret


def get_resource_name(model, many=False):
    """
    return the name of the resource on the server
    if multi is True, it's the url for the «many» models, so we add a «s».
    the resulotion try first to check the APIMeta resource_name and resource_name_plural. if it don't exists,
    it will guess the value from the model name.(lower)
    :param model: the model
    :param bool many: if true, the url of many results
    :return: the resource name (plural if needed)
    :rtype: str
    """
    try:
        if many:
            return getattr(model.APIMeta, 'resource_name_plural', None) or model.__name__.lower() + 's'
        else:
            return getattr(model.APIMeta, 'resource_name', None) or model.__name__.lower()
    except AttributeError:
        raise OperationalError("the given model %s is not a api model" % model)


def find_m2m_field(field_on_through):
    """
    find the many2many field that correspond to the field_on_through field
    A.b <= x through y => B.a
    if A.b is a many2many field, the table throug wil be created with 2 FK, one for A (x) and one for B (y)
    this function give you A.b if you give x, and give B.a if you give y.
    :param field_on_through:
    :return:
    """
    related_model = field_on_through.related_model  # find A or B

    # chain all m2mrel : first the one on the current model found by the manytomany list,
    # 2nd the one dirrectly in related_objects for backward link
    for field, m2mrel in itertools.chain(
            ((field, getattr(related_model, field.name, None)) for field in related_model._meta.many_to_many),
            zip(related_model._meta.related_objects, related_model._meta.related_objects)
    ):
        try:
            if m2mrel.through == field_on_through.model:
                return field
        except AttributeError:
            pass  # the field can be other than a M2Mfield
    raise Exception("can't find a M2M field which use %s on the model %s" %
                    (field_on_through.model, field_on_through.related_model))


class ApiResponseReader(object):
    """
    a helper class the read the response of an api, and give
    some convenient tools to recover the data from it.

    """

    def __init__(self, json, next_=None, many=True):
        """
        create the read of the response
        :param json:  the data loaded from the response
        :param next_: the special function to call on iteration for getting the next result
        :param many: if True, the main rows is on a plurial verbose name. (pizzas instead of pizza)
        """
        self.json = json
        self.cache = {}
        self.many = many
        if next_ is None:
            def nonext():
                # this will trigger the StopIteration at first iter_next
                return []

            self.next = nonext
        else:
            self.next = next_

    def iterate(self, model):
        """
        shortcut that iterate over the result of model. if next was given in the start, it will iterate over the
        result when the result of the model is cosumed
        :param model:
        :return:
        """
        resource_name = get_resource_name(model, many=self.many)

        try:
            iter_next = iter(self.next())
            if self.many:
                # many result in the json.
                # list of results
                while True:
                    for data in self.json[resource_name]:
                        yield data

                    self.json = next(iter_next)
                    self.cache = {}
            else:
                # on result in the response
                yield self.json[resource_name]
        except StopIteration:
            pass
        except KeyError:
            raise ImproperlyConfigured('the response does not contains the result for %s. '
                                       'maybe the resource name does not match the one on the api. '
                                       'please check if %s.APIMeta.resource_name_plural is ok. '
                                       'had %s in result' %
                                       (resource_name, model.__name__, list(self.json.keys())))

    def __getitem__(self, model):
        """
        return the data for the given model on the response.
        the data is a dict which for a pk, give back the data representing it.
        :param model: the model to parse the response for
        :return: all the data found in the response corresponding to the model
        :rtype: dict[str|int, dict[str, any]]
        """
        assert isinstance(model, ModelBase), "you must ask for a django model. not %s" % model
        res = None
        try:
            if model not in self.cache:
                resource_name = get_resource_name(model, many=True)
                pk = model._meta.pk.name

                res = self.cache[model] = collections.OrderedDict(
                    (apidata[pk], apidata)
                    # read all primary request result, and alternative result for the same model,
                    # rendered in a other key prefixed by + (used for foregnkey on self)
                    for apidata in self.json.get(resource_name, []) + self.json.get('+' + resource_name, [])
                )
        except KeyError:
            raise OperationalError("the response from the server does not contains the ID of the model.")
        return res or self.cache[model]


def ancestors(alias):
    """
    generator the return the list of ancestors of an alias
    :param alias:
    :return:
    """
    res = [alias]
    current = alias
    while current.parent is not None:
        current = current.parent
        res.insert(0, current)
    return res


class QueryParser(object):
    """
    an object helper that parse a attached query to return the
    models, attributes and fields from the list of aliases and select.
    """
    quote_rexep = re.compile(r'quoted\(!([^\)]+)!\)')

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
            # table is current model repr, join_field is the field on the remote model that triggered the link
            # and so the related model is the current one
            current_model = table.join_field.related_model
            try:
                m2m_field = None
                parent_alias = aliases[table.parent_alias]

                if current_model._meta.auto_created:
                    m2m = find_m2m_field(table.join_field.field)
                    m2m_resolved[table.table_alias] = m2m, parent_alias
                    m2m_field = m2m

                # not M2M relathionship, but may be folowing previous m2m
                if table.parent_alias in m2m_resolved:
                    field, parent = m2m_resolved[table.parent_alias]
                    # expand the previous alias that is useless
                else:
                    field, parent = table.join_field, parent_alias
                aliases[table.table_alias] = Alias(current_model, parent,
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
        current_alias, att_name = self.resolve_path(col)
        return ".".join(
            tuple(alias.attrname for alias in ancestors(current_alias) if alias.attrname is not None) + (att_name,))

    def resolve_path(self, col):
        """
        resolve the path of Alias to find the final model, with the final name of the attr
        :param Col col: the column to resolve
        :rtype: tuple[Alias], str
        """
        # current = Alias = NamedTuple(model,parent,field,attrname,m2m)
        if isinstance(col, RawSQL):
            matches = self.quote_rexep.findall(col.sql)
            if len(matches) == 2:
                table, field = matches
                current = self.aliases[table]
            else:
                raise NotSupportedError("Only Col in sql select is supported")
        elif isinstance(col, Col):
            current = self.aliases[col.alias]  # type: Alias
            field = col.target.name
        else:
            raise NotSupportedError("Only Col in sql select is supported")
        if current.m2m is not None:
            final_att_name = current.m2m.name
            current = current.parent
        else:
            final_att_name = field

        return current, final_att_name

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

    def get_resources_for_cols(self, cols):
        """
        return the list of resources used and the list of attrubutes for each cols
        :param list[django.db.models.expressions.Col] cols: the list of Col
        :return: 2 sets, the first if the alias useds, the 2nd is the set of the full path of the resources, with the
                 attributes
        """
        resolved = [self.resolve_path(col) for col in cols if not isinstance(col, RawSQL) or col.sql != '1']

        return (
            set(r[0] for r in resolved),  # set of tuple of Alias successives
            set(tuple(a.attrname for a in ancestors(r[0]) if a.attrname is not None) + (r[1],) for r in resolved)
        )

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


def build_aliases_tree(aliases):
    """
    build a tree graph of the aliases. wich give a nested list of list. each list cotains the alias
    :param Iterable[Alias] aliases: the list of aliases, which ancestors is resolved via Alias.parent
    :return: the AliasTree representing the imbicked aliases given
    :rtype: AliasTree
    """
    buildt = {  # type: dict[Alias, AliasTree]
        None: AliasTree(None, [])
    }
    for top_alias in aliases:
        for alias in ancestors(top_alias):
            if alias not in buildt:
                buildt[alias] = AliasTree(alias, [])
            buildt[alias.parent].children.append(buildt[alias])

    return buildt[None].children[0]


def resolve_tree(alias_tree):
    """
    take a tree of aliases and make it a plane list, respecting the order in which we should
    browse it.
    :param alias_tree:
    :return:
    """
    yield alias_tree.alias
    for child in alias_tree.children:
        for alias in resolve_tree(child):
            yield alias


def join_aliases(aliases, responsereader, existing_aliases):
    """
    @private
    a genenartor that flaten a nested structure of data by traversing the given list of alias.
    :param list[Alias] aliases: the aliases to check
    :param responsereader: the ResponseReader with all data from the response
    :param dict[Alias, dict] existing_aliases: the existing alias previously resolved. a dict that.
    :return:
    :rtype: Iterable
    """
    if not aliases:
        yield existing_aliases
        return

    alias = aliases[0]
    if alias in existing_aliases:
        # already exists. no need to work on it
        for subresult in join_aliases(aliases[1:], responsereader, existing_aliases):
            yield subresult
    else:
        # resolve the values of next jump
        val_for_model = responsereader[alias.model]
        current_data = existing_aliases[alias.parent]
        val = current_data[alias.attrname]
        if not isinstance(val, list):
            val = [val]
        for pk in val:
            resolved_aliases = existing_aliases.copy()
            if pk is not None:
                obj = val_for_model[pk]
            else:
                obj = {}
            resolved_aliases[alias] = obj
            for subresult in join_aliases(aliases[1:], responsereader, resolved_aliases):
                yield subresult


def join_results(row, resolved):
    """
    a generator that will generate each results possible for the row data and the resolved data
    :param row:
    :param resolved:
    :return:
    """
    if not resolved:
        yield []
        return
    resolved = list(resolved)
    res = []
    while resolved:
        alias, attrname = resolved.pop(0)

        try:
            raw_val = row[alias][attrname]
        except KeyError:
            res.append(None)
            continue

        field = alias.model._meta.get_field(attrname)
        if hasattr(field, "to_python"):
            python_val = field.to_python(raw_val)
            res.append(python_val)

        elif isinstance(raw_val, list):
            for val in raw_val:
                for subresult in join_results(row, resolved[:]):
                    yield res + [val] + subresult
            return
        else:
            raise NotSupportedError("the result from the api for %s.%s is not supported : %s" %
                                    (alias.model, attrname, raw_val))

    yield res


def simple_count(compiler, result):
    """
    special case that check if the query is a count on one column and shall return only one resulti.
    this can be made by the pagination hack
    :param SQLCompiler compiler: the compiler that is used
    :param result: the result type
    :return:
    """
    if len(compiler.select) == 1 and isinstance(compiler.select[0][0], Count) and result is SINGLE:
        url = get_resource_path(compiler.query.model)
        params = compiler.build_filter_params()
        params['per_page'] = 1
        params['exclude[]'] = '*'
        response = compiler.connection.cursor().get(
            url,
            params=params
        )
        compiler.raise_on_response(url, params, response)
        return True, [response.json()['meta']['total_results']]

    return False, None


class SQLCompiler(BaseSQLCompiler):
    SPECIAL_CASES = [
        simple_count
    ]

    META_NAME = 'meta'

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
        return None, None

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
                if lookup.lookup_name == 'exact' and res.get(key, lookup.rhs) != lookup.rhs:
                    # a small performance that won't trigger any query if the
                    # queryset ask for differents exacts values
                    raise EmptyResultSet()
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
            return {}  # pragma: no cover
        # resources is a set of tuple, each item in the tuple is the alias
        resources, fields = self.query_parser.get_resources_for_cols([col for col, _, _ in self.select])
        # build the list of all pks for selected resources.
        # this prevent the exclusion of the pks if they are not included in the query
        pks = []
        resources_bases = []
        for aliases in resources:
            path = []
            model = self.query.model
            for alias in ancestors(aliases):
                if alias.attrname is not None:
                    path.append(alias.attrname)

                model = alias.model
            pks.append(".".join(path + [model._meta.pk.name]))
            resources_bases.append(".".join(path))

        # exclude[) contains all resources queried forowed by a *
        # include[] contains all pk of each resources along with the queried fields minus the resources itselfs
        res = {
            'exclude[]': {
                ".".join(
                    tuple(
                        a.attrname
                        for a in ancestors(aliases)
                        if a.attrname is not None
                    ) + ('*',))
                for aliases in resources},
            'include[]': ({".".join(r) for r in fields} | set(pks)) - set(resources_bases),
        }
        return res

    def build_sort_params(self):
        """
        build the sort param from the order_by provided by the query
        :return: a dict with or without the sort[]
        :rtype: dict[str, str]
        """
        res = {}
        if self.query.standard_ordering:
            asc, desc = ORDER_DIR['ASC']
        else:
            asc, desc = ORDER_DIR['DESC']

        order_by = [
            self.find_ordering_name(field, self.query.get_meta(), default_order=asc)
            for field in self.query.order_by
            ]

        resolved_order_by = []
        for ob1 in order_by:
            for ob1bis in ob1:
                ob2, boolosef = ob1bis
                if isinstance(ob2.expression, Col):
                    resolved_order_by.append((ob2.descending, ob2.expression))

        if order_by:
            res['sort[]'] = [
                ("-" if desc else "") + self.query_parser.get_rest_path_for_col(col)
                for desc, col in resolved_order_by
                ]
        return res

    def build_limit(self):
        if self.query.high_mark is not None:
            if self.query.low_mark not in (0, None):
                page_size = pgcd(self.query.high_mark, self.query.low_mark)
                return {
                    'per_page': page_size,
                    'page': (self.query.low_mark // page_size) + 1
                }
            else:
                return {
                    'per_page': self.query.high_mark,
                }
        return {}

    def build_params(self):
        params = {}
        params.update(self.build_filter_params())
        params.update(self.build_include_exclude_params())
        params.update(self.build_sort_params())
        params.update(self.build_limit())
        return params

    def build_params_and_pk(self):
        """
        will try to get the pk on the query if there is one pk in the filter

        :return:
        """
        ids = self.query_parser.resolve_ids()
        if ids is not None and len(ids) == 1:
            params = {}
            params.update(self.build_include_exclude_params())
            return next(iter(ids)), params
        return None, self.build_params()

    def raise_on_response(self, url, params, response):
        """
        raise a exception with a explicit message if the respones from the backend is not a 200, 202 or 204
        :param url:
        :param params:
        :param response:
        :return:
        """
        if response.status_code == 204:
            raise EmptyResultSet
        elif response.status_code != 200:
            raise ProgrammingError("the query to the api has failed : GET %s \n=> %s" %
                                   (build_url(url, params), message_from_response(response)))

    def get_meta(self, json, response):
        """
        small shortcut to get the metadata from a response data.
        simle for now, but allow for refactoring in future release if meta system has changed

        :param dict json: the data of the response
        :param response: the response if used
        :return:
        """
        return json.get(self.META_NAME)
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
            params = {
                'exclude[]': '*',
                'include[]': pk_name,
            }
            params.update(self.build_filter_params())
            result = self.connection.cursor().get(
                get_resource_path(self.query.model),
                params=params
            )
            if result.status_code != 200:
                raise ProgrammingError("error while querying the database : %s" % result.text)
            ids = {res['id'] for res in result.json()[get_resource_name(self.query.model, many=True)]}
        return ids

    def response_to_table(self, responsereader, item):
        """
        take the total result, and return flatened data into a list, including all cols in the select.
        :param ApiResponseReader responsereader: the full response as a convenient ApiResponseReader
        :param dict item: the current item to parse
        :return:
        """
        resolved = [
            self.query_parser.resolve_path(col)
            for col, _, _ in self.select
            if not isinstance(col, RawSQL) or col.sql != '1'  # skip special case with exists()
            ]
        if not resolved:
            # nothing in select. special case in exists()
            yield [[]]
        else:
            uniq_aliases = set(list(zip(*resolved))[0])
            alias_tree = build_aliases_tree(uniq_aliases)
            alias_list = list(resolve_tree(alias_tree))

            for row in join_aliases(alias_list, responsereader, {alias_tree.alias: item}):
                for subresult in join_results(row, resolved):
                    yield subresult

    def result_iter(self, responsereader):
        """
        iterate over the result given by the ApiResponseReader
        :param ApiResponseReader responsereader:
        :return:
        """
        for item in responsereader.iterate(self.query.model):
            for subitem in self.response_to_table(responsereader, item):
                yield [subitem]

    def special_cases(self, result_type):
        """
        a special processor that allow to bypass the normal GET process for the current query.
        :param result_type:
        :return: a tupel, with bool and result. the bool is meant to say if there was a special case that matched
        """
        for special_case in self.SPECIAL_CASES:
            is_special, result = special_case(self, result_type)
            if is_special:
                return True, result
        return False, None

    def execute_sql(self, result_type=MULTI):
        self.setup_query()
        if not result_type:
            result_type = NO_RESULTS
        try:
            is_special, result = self.special_cases(result_type)
            if is_special:
                return result

            pk, params = self.build_params_and_pk()
            url = get_resource_path(self.query.model, pk)
            response = self.connection.cursor().get(
                url,
                params=params
            )
            self.raise_on_response(url, params, response)

            json = response.json()
            meta = self.get_meta(json, response)
            if meta:
                # pagination and others thing

                high_mark = self.query.high_mark
                page_to_stop = None if high_mark is None else (high_mark // meta['per_page'])

                def next_from_query():
                    for i in range(meta['page'], page_to_stop or meta['total_pages']):
                        tmp_params = params.copy()
                        tmp_params['page'] = i + 1  # + 1 because of range include start and exclude stop
                        last_response = self.connection.cursor().get(
                            url,
                            params=tmp_params
                        )
                        yield last_response.json()

            else:
                next_from_query = None

        except EmptyResultSet:
            if result_type == MULTI:
                return iter([])
            else:
                return

        if result_type == CURSOR:
            # Caller didn't specify a result_type, so just give them back the
            # cursor to process (and close).
            raise ProgrammingError("returning a cursor for this database is not supported")
        if result_type == SINGLE:
            response_reader = ApiResponseReader(json, many=pk is None)
            for result in self.result_iter(response_reader):
                return result
            return
        if result_type == NO_RESULTS:
            return
        response_reader = ApiResponseReader(json, next_=next_from_query, many=pk is None)
        result = self.result_iter(response_reader)
        return result


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
                get_resource_name(query.model, many=True): data
            }
            response = self.connection.cursor().post(
                get_resource_path(self.query.model),
                json=json
            )
            if response.status_code != 201:
                raise FakeDatabaseDbAPI2.ProgrammingError(
                    "error while creating %d %s.\n%s" %
                    (len(query_objs), opts.verbose_name, response.json()['errors'])
                )
            result_json = response.json()
            for old, new in zip(query_objs, result_json[get_resource_name(query.model, many=True)]):
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
                    get_resource_name(query.model, many=False): data
                }
                response = self.connection.cursor().post(
                    get_resource_path(self.query.model),
                    json=json
                )
                if response.status_code != 201:
                    raise FakeDatabaseDbAPI2.ProgrammingError("error while creating %s.\n%s" % (
                        obj, message_from_response(response)))
                result_json = response.json()
                new = result_json[get_resource_name(query.model, many=False)]
                for field in opts.concrete_fields:
                    setattr(obj, field.attname, field.to_python(new[field.name]))

            if return_id and result_json:
                return result_json[get_resource_name(query.model, many=False)][opts.pk.column]


class SQLDeleteCompiler(SQLCompiler):
    def execute_sql(self, result_type=MULTI):
        if self.is_api_model():

            q = self.query
            # we don't care about many2many table, the api will clean it for us
            if not self.query.get_meta().auto_created:

                for id in self.resolve_ids():
                    result = self.connection.cursor().delete(
                        get_resource_path(q.model, pk=id),
                    )
                    if result.status_code not in (200, 202, 204):
                        raise ProgrammingError("the deletion has failed : %s" % result.text)


class SQLUpdateCompiler(SQLCompiler):
    def resolve_data(self):
        """
        build the dict to send with a put/patch that contains the data to update

        :return:
        """
        return {
            get_resource_name(self.query.model, many=False): {
                field.name: field.get_db_prep_save(val, connection=self.connection)
                for field, _, val in self.query.values
                }
        }

    def execute_sql(self, result_type=MULTI):
        updated = 0
        if self.is_api_model():
            q = self.query
            json = self.resolve_data()
            for id in self.resolve_ids():
                result = self.connection.cursor().patch(
                    get_resource_path(q.model, pk=id),
                    json=json
                )
                if result.status_code not in (200, 202, 204):
                    raise ProgrammingError("the update has failed : %s" % result.text)
                updated += 1
        return updated


class SQLAggregateCompiler(SQLCompiler):

    def execute_sql(self, result_type=MULTI):
        raise NotSupportedError("the aggregation for the database %s is not supported : %s" % (
                                self.connection.alias, self.query))  # pragma: no cover
