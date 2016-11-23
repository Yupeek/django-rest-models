# -*- coding: utf-8 -*-
from django.db import connections
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.db.utils import NotSupportedError, ProgrammingError
from django.test import TestCase
from rest_models.backend.compiler import Alias, QueryParser, SQLCompiler

from testapp.models import Menu, Pizza, Topping


class CompilerTestCase(TestCase):
    def assertQsToFilter(self, queryset, res):
        # fix the fact the the test test uniq value, but the
        # compiler return a dict of list (even if there is on element each times)
        for k, v in res.items():
            if not isinstance(v, list):
                res[k] = [v]
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        compiler.setup_query()
        self.assertEqual(compiler.build_filter_params(), res)

    def assertQsToInclude(self, queryset, expected):
        for k, v in expected.items():
            if isinstance(v, list):
                expected[k] = set(expected[k])
            elif not isinstance(v, set):
                expected[k] = {v}
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        compiler.setup_query()

        self.assertEqual(compiler.build_include_exclude_params(), expected)

    def assertBadQs(self, queryset, expected=NotSupportedError):
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        # con't setup query since this call check_compatibility
        self.assertRaises(expected, compiler.check_compatibility)

    def assertGoodQs(self, queryset):
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        compiler.setup_query()
        self.assertIsNone(compiler.check_compatibility())

    def assertQsToOrder(self, queryset, res):
        # fix the fact the the test test uniq value, but the
        # compiler return a dict of list (even if there is on element each times)
        for k, v in res.items():
            if not isinstance(v, list):
                res[k] = [v]
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        compiler.setup_query()
        self.assertEqual(compiler.build_sort_params(), res)


class QueryParesTest(TestCase):

    def assertParsedAliasEqual(self, queryset, res):
        queryset.query.get_initial_alias()
        parser = QueryParser(queryset.query)
        # remove the alias key, which is useless for our testing
        alieses_dict_testable = {alias[0].__name__: alias for alias in parser.aliases.values()}
        res_dict_testable = {
            expected[0]: expected
            for expected in (
                (t[0] if isinstance(t[0], str) else t[0].__name__,) + t[1:]
                for t in res
            )
        }

        self.assertEqual(
            set(alieses_dict_testable.keys()),
            set(res_dict_testable.keys()),
            "%s = %s" % (set(alieses_dict_testable.keys()), set(res_dict_testable.keys()))
        )
        for model_alias, alias in alieses_dict_testable.items():  # type: str, Alias
            model_name, parent, field, attrname, m2m = res_dict_testable[model_alias]

            self.assertEqual(model_name, alias.model.__name__)
            self.assertEqual(field, alias.field and alias.field.name)
            self.assertEqual(attrname, alias.attrname)
            self.assertEqual(m2m, alias.m2m is not None)

    def assertPathToColEqual(self, queryset, expected):
        queryset.query.get_initial_alias()
        parser = QueryParser(queryset.query)
        result = {parser.get_rest_path_for_col(col) for col in queryset.query.select}
        self.assertEqual(set(expected), result)

    def test_aliases_one_table(self):
        self.assertParsedAliasEqual(
            Pizza.objects.all(),
            [
                (Pizza, None, None, None, False)
            ]
        )
        self.assertParsedAliasEqual(
            Pizza.objects.all().values('id'),
            [
                (Pizza, None, None, None, False)
            ]
        )
        self.assertParsedAliasEqual(
            Pizza.objects.all().values('name'),
            [
                (Pizza, None, None, None, False)
            ]
        )
        self.assertParsedAliasEqual(
            Pizza.objects.all().only('name'),
            [
                (Pizza, None, None, None, False)
            ]
        )

        self.assertParsedAliasEqual(
            Pizza.objects.all().defer('name'),
            [
                (Pizza, None, None, None, False)
            ]
        )

        self.assertParsedAliasEqual(
            Pizza.objects.all().filter(id=1),
            [
                (Pizza, None, None, None, False)
            ]
        )
        self.assertParsedAliasEqual(
            Pizza.objects.all().filter(name="supreme"),
            [
                (Pizza, None, None, None, False)
            ]
        )

    def test_aliases_two_tables(self):
        # alias : 'model,parent,field,attrname,m2m'
        self.assertParsedAliasEqual(
            Pizza.objects.all().filter(menu__name='menu'),
            [
                (Pizza, None, None, None, False),
                (Menu, Pizza, 'menu', 'menu', False),
            ]
        )
        self.assertParsedAliasEqual(
            Pizza.objects.all().values("menu__code"),
            [
                (Pizza, None, None, None, False),
                (Menu, Pizza, 'menu', 'menu', False),
            ]
        )

    def test_aliases_three_tables(self):
        # alias : 'model,parent,field,attrname,m2m'
        self.assertParsedAliasEqual(
            Menu.objects.all().filter(pizzas__toppings__name='crème'),
            [
                (Menu, None, None, None, False),
                (Pizza, Menu, 'pizzas', 'pizzas', False),
                (Topping, Pizza, 'toppings', 'toppings', False),
                ('Pizza_toppings', Pizza, 'Pizza_toppings+', 'Pizza_toppings+', True),

            ]
        )
        self.assertParsedAliasEqual(
            Menu.objects.all().values("pizzas__toppings__name"),
            [
                (Menu, None, None, None, False),
                (Pizza, Menu, 'pizzas', 'pizzas', False),
                (Topping, Pizza, 'toppings', 'toppings', False),
                ('Pizza_toppings', Pizza, 'Pizza_toppings+', 'Pizza_toppings+', True),
            ]
        )

    def test_column_resolution_fk(self):
        self.assertPathToColEqual(
            Pizza.objects.all().values('name'),
            {
                'name'
            }
        )
        self.assertPathToColEqual(
            Pizza.objects.all().values('name', 'id'),
            {
                'name',
                'id'
            }
        )
        self.assertPathToColEqual(
            Pizza.objects.all().values('menu__name', 'id'),
            {
                'menu.name',
                'id'
            }
        )

    def test_column_resolution_m2m(self):
        self.assertPathToColEqual(
            Pizza.objects.all().values('toppings__name'),
            {
                'toppings.name'
            }
        )

    def test_colum_resolution_m2m_id(self):
        self.assertPathToColEqual(
            Pizza.objects.all().values('toppings__id'),
            {
                'toppings'
            }
        )




class TestCompilerFilterParams(CompilerTestCase):
    def test_no_filter(self):
        self.assertQsToFilter(
            Pizza.objects.all(),
            {}
        )

    def test_simple_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(pk=1),
            {'filter{id}': 1}
        )

    def test_simple_exclude(self):
        self.assertQsToFilter(
            Pizza.objects.exclude(pk=1),
            {'filter{-id}': 1}
        )

    def test_anded_exclude(self):
        self.assertQsToFilter(
            Pizza.objects.exclude(pk=1).exclude(price=11.0),
            {'filter{-id}': 1, 'filter{-price}': 11.0},
        )

    def test_and_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id=3, price=15.0),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(id=3).filter(price=15.0),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )

    def test_exclude_and_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id=3).exclude(price=11.0),
            {'filter{id}': 3, 'filter{-price}': 11.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3) & ~Q(price=11.0)),
            {'filter{id}': 3, 'filter{-price}': 11.0},
        )

    def test_Q_with_and(self):
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3), Q(price=15.0)),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )
        self.assertQsToFilter(
            Pizza.objects.filter(Q(id=3) & Q(price=15.0)),
            {'filter{id}': 3, 'filter{price}': 15.0},
        )


class TestIncompatibleBuildCompiler(CompilerTestCase):
    def test_or_filter(self):
        self.assertBadQs(
            Pizza.objects.filter(Q(id=1) | Q(cost=10.0))
        )
        self.assertBadQs(
            Pizza.objects.exclude(Q(id=2) | Q(cost=15.0))
        )

    def test_negated_Q(self):
        # negate a AND give a OR, whiche is not supported
        self.assertBadQs(
            Pizza.objects.filter(~Q(Q(id=1) & Q(cost=10.0)))
        )
        self.assertBadQs(
            Pizza.objects.filter(~Q(id=1, cost=10.0))
        )

    def test_distinct(self):
        self.assertBadQs(
            Pizza.objects.all().distinct('name')
        )

    def test_annotate(self):
        self.assertBadQs(
            Pizza.objects.all().annotate(Sum('toppings__cost'))
        )

    def test_nested_qs(self):
        self.assertBadQs(
            Pizza.objects.all().filter(menu__in=Menu.objects.all()),
        )

    def test_raw_qs(self):
        self.assertBadQs(
            Pizza.objects.all().filter(menu_id=F('menu_id')),
        )

    def test_ok_filter(self):
        self.assertGoodQs(
            Pizza.objects.filter(Q(id=1) & Q(cost=10.0))
        )
        self.assertGoodQs(
            Pizza.objects.filter(Q(id=1) & ~Q(cost=10.0))
        )
        self.assertGoodQs(
            Pizza.objects.filter(Q(Q(id=1) & ~Q(cost=10.0)))
        )

    def test_unseported_mix(self):
        # negated OR give AND
        # but it's took complexe to detect
        self.assertBadQs(
            Pizza.objects.filter(~Q(Q(id=1) | ~Q(cost=10.0)))
        )

    def test_ored_exclude(self):
        self.assertBadQs(
            Pizza.objects.exclude(pk=1, price=11.0),
        )


class TestLookupCompliler(CompilerTestCase):
    def test_in(self):
        self.assertQsToFilter(
            Pizza.objects.filter(id__in=[1, 2]),
            {'filter{id.in}': [1, 2]}
        )
        self.assertQsToFilter(
            Pizza.objects.exclude(id__in=[1, 2]),
            {'filter{-id.in}': [1, 2]}
        )

    def test_icontains(self):
        self.assertQsToFilter(
            Pizza.objects.filter(name__icontains='sup'),
            {'filter{name.icontains}': 'sup'}
        )
        self.assertQsToFilter(
            Pizza.objects.exclude(name__icontains='sup'),
            {'filter{-name.icontains}': 'sup'}
        )


class TestIncludeCompiler(CompilerTestCase):
    def test_only_get(self):
        self.assertQsToInclude(
            Pizza.objects.all().only('id'),
            {'exclude[]': '*', 'include[]': ['id']},
        )

    def test_values_get(self):
        self.assertQsToInclude(
            Pizza.objects.all().values('id'),
            {'exclude[]': '*', 'include[]': ['id']},
        )

    def test_defered_get(self):
        self.assertQsToInclude(
            Pizza.objects.all().defer('name'),
            {'exclude[]': '*',
             'include[]': ['id', 'price', 'from_date', 'to_date', 'menu', 'cost']},
        )

    def test_normal_get(self):
        self.assertQsToInclude(
            Pizza.objects.all(),
            {'exclude[]': '*',
             'include[]': ['id', 'price', 'from_date', 'to_date', 'menu', 'cost', 'name']}
        )

    def test_include_related(self):
        self.assertQsToInclude(
            Pizza.objects.all().values('id', 'menu__name', 'toppings__name'),
            {'exclude[]': ['*', 'menu.*', 'toppings.*'], 'include[]': ['id', 'menu.name', 'toppings.name']},
        )

    def test_include_related_resolution(self):
        self.assertQsToInclude(
            Menu.objects.all().values('code', 'pizzas__name', 'pizzas__toppings__name'),
            {'exclude[]': ['*', 'pizzas.*', 'pizzas.toppings.*'],
             'include[]': ['code', 'pizzas.name', 'pizzas.toppings.name']},
        )

    def test_include_realted_pk(self):
        self.assertQsToInclude(
            Pizza.objects.all().values('id', 'menu__code', 'toppings__id'),
            {'exclude[]': ['*', 'menu.*'],
             'include[]': ['id', 'menu.code', 'toppings']},
        )


class TestOrderByCompiler(CompilerTestCase):
    def test_normal(self):
        self.assertQsToOrder(
            Pizza.objects.all(),
            {},
        )

    def test_order_asc(self):
        self.assertQsToOrder(
            Pizza.objects.all().order_by('name'),
            {'sort[]': 'name'},
        )

    def test_order_desc(self):
        self.assertQsToOrder(
            Pizza.objects.all().order_by('-name'),
            {'sort[]': '-name'},
        )

    def test_order_multi(self):
        self.assertQsToOrder(
            Pizza.objects.all().order_by('menu', 'name'),
            {'sort[]': ['menu', 'name']},
        )

    def test_order_related(self):
        self.assertQsToOrder(
            Pizza.objects.all().order_by('menu__name'),
            {'sort[]': ['menu.name']},
        )
