# -*- coding: utf-8 -*-

from django.db import connections
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.db.utils import NotSupportedError, ProgrammingError
from django.test import TestCase

from rest_models.backend.compiler import QueryParser, SQLCompiler, find_m2m_field
from testapp.models import Menu, Pizza, Topping


def dict_of_set(expected):
    res = {}
    for k, v in expected.items():
        if isinstance(v, list):
            res[k] = set(v)
        elif not isinstance(v, set):
            res[k] = {v}
        else:
            res[k] = v
    return res


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

    def assertQsParams(self, queryset, expected):
        # fix the fact the the test test uniq value, but the
        # compiler return a dict of list (even if there is on element each times)
        compiler = SQLCompiler(queryset.query, connections['api'], 'api')
        compiler.setup_query()

        self.assertEqual(dict_of_set(compiler.build_params()), dict_of_set(expected))


class QueryParserPathResolutionTest(TestCase):

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

    def test_alias_resolution_failure(self):
        query = Menu.objects.values_list('pizzas__toppings__name').query
        del query.alias_map['testapp_pizza']
        parser = QueryParser(query)
        self.assertRaises(ProgrammingError, getattr, parser, 'aliases')

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


class QueryParserIdResolutionTest(CompilerTestCase):
    def assertResolvedId(self, queryset, expected):
        queryset.query.get_initial_alias()
        parser = QueryParser(queryset.query)
        self.assertEqual(parser.resolve_ids(), expected and set(expected))

    def test_pk_equal(self):
        self.assertResolvedId(
            Pizza.objects.filter(pk=1),
            [1]
        )
        self.assertResolvedId(
            Pizza.objects.filter(id=1),
            [1]
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__exact=1),
            [1]
        )
        self.assertResolvedId(
            Menu.objects.filter(id__exact=1),
            [1]
        )

    def test_pk_or(self):
        self.assertResolvedId(
            Pizza.objects.filter(Q(pk=1) | Q(pk=3)),
            [1, 3]
        )
        self.assertResolvedId(
            Pizza.objects.filter(Q(pk=1) | Q(pk__range=[3, 5])),
            [1, 3, 4, 5]
        )
        self.assertResolvedId(
            Pizza.objects.filter(Q(pk=1) | Q(pk__in=[3, 5])),
            [1, 3, 5],
        )

    def test_field_mix_fail(self):
        self.assertResolvedId(
            Pizza.objects.filter(pk__in=[1, 3]).filter(name='lolilol'),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(pk__in=[1, 3]).exclude(pk=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(pk__in=[1, 3]).filter(pk=1).filter(pk=3),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(pk__in=[1, 3]).filter(pk=1),
            {1}
        )
        self.assertResolvedId(
            Pizza.objects.filter(pk=1).filter(pk=3),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(Q(pk__in=[1, 3]) | Q(name='lolilol')),
            None
        )

    def test_pk_in(self):
        self.assertResolvedId(
            Pizza.objects.filter(pk__in=[1, 3]),
            [1, 3]
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__in=[1, 3]),
            [1, 3]
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__in=(1, 3)),
            [1, 3]
        )
        self.assertResolvedId(
            Menu.objects.filter(id__in=[1, 3]),
            [1, 3]
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__range=[1, 3]),
            [1, 2, 3]
        )

    def test_bad_lookup(self):
        self.assertResolvedId(
            Pizza.objects.filter(pk__gte=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__gte=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__lte=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__gt=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__lt=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__contains=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__icontains=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__iexact=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(id__isnull=True),
            None
        )

    def test_bad_field(self):
        self.assertResolvedId(
            Pizza.objects.all(),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(menu_id=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(menu__id=1),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(name="supreme"),
            None
        )
        self.assertResolvedId(
            Pizza.objects.filter(name__contains="supreme"),
            None
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

    def test_models_value(self):
        self.assertQsToFilter(
            Pizza.objects.all().filter(
                menu=Menu(pk=1)
            ),
            {'filter{menu}': 1}
        )

    def test_models_value_exclude(self):
        self.assertQsToFilter(
            Pizza.objects.all().exclude(
                menu=Menu(pk=1)
            ),
            {'filter{-menu}': 1}
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

    def test_filter_auto_created_replacment(self):
        self.assertQsToFilter(
            Topping.objects.filter(**{'Pizza_toppings+__pizza': 1}),
            {'filter{pizzas}': 1}
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

    def test_related_filter(self):
        self.assertQsToFilter(
            Pizza.objects.filter(menu__name='chien'),
            {'filter{menu.name}': 'chien'}
        )

    def test_related_filter_3_models(self):
        self.assertQsToFilter(
            Menu.objects.filter(pizzas__toppings__cost__gt=2),
            {'filter{pizzas.toppings.cost.gt}': 2.0}
        )

    def test_related_filter_id_shortcut(self):
        self.assertQsToFilter(
            Pizza.objects.filter(menu__id=1),
            {'filter{menu}': 1}
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
            {'exclude[]': ['*', 'menu.*', 'toppings.*'],
             'include[]': ['id', 'menu.name', 'toppings.name', 'menu.id', 'toppings.id']},
        )

    def test_include_related_resolution(self):
        self.assertQsToInclude(
            Menu.objects.all().values('code', 'pizzas__name', 'pizzas__toppings__name'),
            {'exclude[]': ['*', 'pizzas.*', 'pizzas.toppings.*'],
             'include[]': ['code', 'pizzas.name', 'pizzas.toppings.name', 'id', 'pizzas.id', 'pizzas.toppings.id']},
        )

    def test_include_realted_pk(self):
        self.assertQsToInclude(
            Pizza.objects.all().values('id', 'menu__code', 'toppings__id'),
            {'exclude[]': ['*', 'menu.*'],
             'include[]': ['id', 'menu.code', 'toppings', 'menu.id']},
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

    def test_order_related_id(self):
        self.assertQsToOrder(
            Pizza.objects.all().order_by('toppings__id'),
            {'sort[]': ['toppings']},
        )


class TestFullCompiler(CompilerTestCase):
    def test_build_params(self):
        self.assertQsParams(
            Pizza.objects.all().filter(
                toppings__name__in=['chien', 'chat']
            ).exclude(
                menu=Menu(pk=1)
            ).order_by('menu__code', 'cost').values('menu__code', 'toppings__name', 'cost'),
            {
                'sort[]': ['cost', 'menu.code'],
                'exclude[]': ['*', 'menu.*', 'toppings.*'],
                'include[]': ['menu.code', 'toppings.name', 'cost', 'menu.id', 'id', 'toppings.id'],
                'filter{toppings.name.in}': ['chien', 'chat'],
                'filter{-menu}': 1,
            }
        )


class TestFindM2MField(TestCase):
    def setUp(self):
        self.throug = Pizza.toppings.through

    def test_forward_check(self):
        self.assertEqual(
            Pizza._meta.get_field('toppings'),
            find_m2m_field(self.throug._meta.get_field('pizza'))
        )

    def test_backward_check(self):
        self.assertEqual(
            Topping._meta.get_field('pizzas'),
            find_m2m_field(self.throug._meta.get_field('topping'))
        )

    def test_failed(self):
        self.assertRaises(Exception, find_m2m_field, Pizza._meta.get_field('menu'))
