# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import json
from unittest import skipIf

from django.conf import settings
from django.db import NotSupportedError, ProgrammingError, connections
from django.db.models import Q, Sum
from django.test import TestCase
from django.urls import reverse
from dynamic_rest.constants import VALID_FILTER_OPERATORS
from dynamic_rest.filters import DynamicFilterBackend

from rest_models.backend.compiler import SQLAggregateCompiler, SQLCompiler
from testapi import models as api_models
from testapi.models import auto_now_plus_5d
from testapp import models as client_models


class TestQueryInsert(TestCase):
    fixtures = ['user.json']
    databases = ["default", "api"]

    def test_insert_normal(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        p = client_models.Pizza.objects.create(
            name='savoyarde',
            price=13.3,
            from_date=datetime.datetime.today(),
            to_date=datetime.datetime.today() + datetime.timedelta(days=3)
        )
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertIsNotNone(p.pk)
        new = api_models.Pizza.objects.get(pk=p.pk)

        for attr in ('name', 'price', 'from_date', 'to_date'):
            self.assertEqual(getattr(new, attr), getattr(p, attr))

    def test_insert_default_value(self):

        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        client_created = client_models.Pizza.objects.create(
            name='savoyarde',
            price=13.3,
            from_date=datetime.datetime.today(),
            # to_date has default value
        )
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertIsNotNone(client_created.pk)
        api_fetched = api_models.Pizza.objects.get(pk=client_created.pk)
        client_fetched = client_models.Pizza.objects.get(pk=client_created.pk)

        expected_default = auto_now_plus_5d()

        self.assertLess((client_created.to_date - expected_default).total_seconds(), 1)
        self.assertLess((client_fetched.to_date - expected_default).total_seconds(), 1)
        self.assertLess((api_fetched.to_date - expected_default).total_seconds(), 1)

        for attr in ('name', 'price', 'from_date', 'to_date'):
            self.assertEqual(getattr(client_fetched, attr), getattr(client_created, attr), "%s differ" % attr)
            self.assertEqual(getattr(api_fetched, attr), getattr(client_created, attr), "%s differ" % attr)

    def test_save_normal(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        p = client_models.Pizza(
            name='savoyarde',
            price=13.3,
            from_date=datetime.datetime.today(),
            to_date=datetime.datetime.today() + datetime.timedelta(days=3)
        )
        p.save(force_insert=True)
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertIsNotNone(p.pk)
        new = api_models.Pizza.objects.get(pk=p.pk)

        for attr in ('name', 'price', 'from_date', 'to_date'):
            self.assertEqual(getattr(new, attr), getattr(p, attr))

    def test_insert_missing_data(self):
        with self.assertRaises(ProgrammingError):
            client_models.Pizza.objects.create(
                name='savoyarde',
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            )

    def test_insert_too_many_data(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        p = client_models.Pizza.objects.create(
            name='savoyarde',
            price=13.4,
            cost=777,  # cost is a computed value
            from_date=datetime.datetime.today(),
            to_date=datetime.datetime.today() + datetime.timedelta(days=3)
        )
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertIsNotNone(p.pk)
        self.assertEqual(p.cost, None)  # value was updated from the api result

    def test_bulk_insert(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        pizzas = [
            client_models.Pizza(
                name='savoyarde',
                price=13.3,
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            ),
            client_models.Pizza(
                name='vide',
                price=5,
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            ),
            client_models.Pizza(
                name='poulet',
                price=11.3,
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            )
        ]
        client_models.Pizza.objects.bulk_create(pizzas)

        self.assertEqual(api_models.Pizza.objects.count(), 3)
        for p in pizzas:
            self.assertIsNotNone(p.pk)
            new = api_models.Pizza.objects.get(pk=p.pk)

            for attr in ('name', 'price', 'from_date', 'to_date'):
                self.assertEqual(getattr(new, attr), getattr(p, attr))

    def test_bulk_insert_error(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 0)  # there is no fixture
        pizzas = [
            client_models.Pizza(
                name='savoyarde',
                price=13.3,
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            ),
            client_models.Pizza(
                name='vide',
                # cost is missing
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            ),
            client_models.Pizza(
                name='poulet',
                price=11.3,
                from_date=datetime.datetime.today(),
                to_date=datetime.datetime.today() + datetime.timedelta(days=3)
            )
        ]
        with self.assertRaises(ProgrammingError):
            client_models.Pizza.objects.bulk_create(pizzas)

        self.assertEqual(api_models.Pizza.objects.count(), 0)  # validation accure for all pizza befor insert
        for p in pizzas:
            self.assertIsNone(p.pk)


class TestM2M(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def setUp(self):
        self.p4 = api_models.Pizza.objects.create(
            pk=4,
            name="vomito",
            price=0
        )
        self.topping7 = api_models.Topping.objects.create(
            pk=7,
            cost=0.5,
            name="champi perimé",
        )

    def test_many2many_insert(self):
        p = client_models.Pizza.objects.get(pk=4)
        p2 = client_models.Pizza.objects.get(pk=3)

        topping = client_models.Topping.objects.get(pk=7)

        self.assertEqual(list(p.toppings.all()), [])
        self.assertEqual(list(topping.pizzas.all()), [])

        topping.pizzas.add(p, p2)

        self.assertEqual(list(p.toppings.all()), [topping])
        self.assertEqual(set(topping.pizzas.all()), {p, p2})

    def test_many2many_delete(self):
        p = client_models.Pizza.objects.get(pk=3)
        topping = client_models.Topping.objects.get(pk=6)
        topping2 = client_models.Topping.objects.get(pk=4)

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1], [4], [6]])
        self.assertEqual(list(topping.pizzas.all()), [p])

        p.toppings.remove(topping, topping2)

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1]])
        self.assertEqual(list(topping.pizzas.all()), [])

    def test_many2many_set(self):
        p = client_models.Pizza.objects.get(pk=3)
        topping = client_models.Topping.objects.get(pk=6)

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1], [4], [6]])
        self.assertEqual(list(topping.pizzas.all()), [p])
        vals = client_models.Topping.objects.filter(pk__in=[1, 2])
        p.toppings.set(vals)

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1], [2]])
        self.assertEqual(list(topping.pizzas.all()), [])

    def test_many2many_clear(self):
        p = client_models.Pizza.objects.get(pk=3)
        topping = client_models.Topping.objects.get(pk=6)

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1], [4], [6]])
        self.assertEqual(list(topping.pizzas.all()), [p])

        topping.pizzas.clear()

        self.assertEqual(list(p.toppings.all().values_list('pk')), [[1], [4], ])
        self.assertEqual(list(topping.pizzas.all()), [])


@skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3', 'no json in sqlite')
class TestJsonField(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def test_jsonfield_create(self):
        t = client_models.Topping.objects.create(
            name='lardons lux',
            cost=2,
            metadata={'origine': 'france', 'abattage': 2018}
        )
        self.assertIsNotNone(t)
        self.assertEqual(t.metadata, {'origine': 'france', 'abattage': 2018})
        self.assertEqual(t.cost, 2)
        self.assertEqual(t.name, 'lardons lux')

        t2 = api_models.Topping.objects.get(pk=t.pk)
        self.assertEqual(
            {k: v for k, v in t.__dict__.items() if k in ('name', 'cost', 'metadata')},
            {k: v for k, v in t2.__dict__.items() if k in ('name', 'cost', 'metadata')}
        )

    def test_jsonfield_update(self):
        t = client_models.Topping.objects.create(
            name='lardons lux',
            cost=2,
            metadata={'origine': 'france', 'abattage': 2018}
        )
        self.assertIsNotNone(t)
        self.assertEqual(t.metadata, {'origine': 'france', 'abattage': 2018})
        self.assertEqual(t.cost, 2)
        self.assertEqual(t.name, 'lardons lux')

        t2 = api_models.Topping.objects.get(pk=t.pk)
        t2.metadata = {'origine': 'france'}
        t2.save()
        t.refresh_from_db()
        self.assertEqual(t.metadata,  {'origine': 'france'})
        self.assertEqual(
            {k: v for k, v in t.__dict__.items() if k in ('name', 'cost', 'metadata')},
            {k: v for k, v in t2.__dict__.items() if k in ('name', 'cost', 'metadata')}
        )


@skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3', 'no json in sqlite')
@skipIf('year' in VALID_FILTER_OPERATORS, 'skip check not compatible with current drest')
class TestJsonLookup(TestCase):
    fixtures = ['data.json']

    def test_jsonfield_lookup_isnull(self):
        t = api_models.Topping.objects.create(
            name='lardons lux',
            cost=2,
            metadata={'origine': 'france', 'abattage': None}
        )
        self.assertIsNotNone(t)

        self.assertEqual(client_models.Topping.objects.filter(pk=t.pk).count(), 1)
        self.assertEqual(list(api_models.Topping.objects.filter(metadata__abattage__isnull=False).values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(api_models.Topping.objects.filter(metadata__abattage__isnull=True).values_list('pk')),
                         [[1], [2], [3], [4], [5], [6]])

    def test_jsonfield_lookup(self):
        t = api_models.Topping.objects.create(
            name='lardons lux',
            cost=2,
            metadata={'origine': 'france', 'abattage': '2018'}
        )
        self.assertIsNotNone(t)

        self.assertEqual(client_models.Topping.objects.filter(pk=t.pk).count(), 1)
        self.assertEqual(list(api_models.Topping.objects.filter(metadata__abattage='2018').values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(client_models.Topping.objects.filter(metadata__abattage='2018').values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(client_models.Topping.objects.filter(metadata__abattage=2018).values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(client_models.Topping.objects.filter(metadata__abattage__lt='2019').values_list('pk')),
                         [(t.pk,)])

    def test_jsonfield_lookup_deeper(self):
        t = api_models.Topping.objects.create(
            name='lardons lux',
            cost=2,
            metadata={'origine': 'france', 'abattage': {'pays': 'DE', 'annee': '2018'}}
        )
        self.assertIsNotNone(t)

        self.assertEqual(client_models.Topping.objects.filter(pk=t.pk).count(), 1)
        self.assertEqual(list(api_models.Topping.objects.filter(metadata__abattage__annee='2018').values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(
            client_models.Topping.objects.filter(metadata__abattage__annee='2018').values_list('pk')
        ), [(t.pk,)])
        self.assertEqual(list(client_models.Topping.objects.filter(metadata__abattage__annee=2018).values_list('pk')),
                         [(t.pk,)])
        self.assertEqual(list(
            client_models.Topping.objects.filter(metadata__abattage__annee__lt='2019').values_list('pk')
        ), [(t.pk,)])


@skipIf('year' in VALID_FILTER_OPERATORS, 'skip check not compatible with current drest')
class TestQueryLookupTransform(TestCase):
    fixtures = ['data.json']

    def test_get_iexact(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(len(list(client_models.Pizza.objects.filter(name__iexact="FlAm"))), 1)

    def test_get_regex(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(len(list(client_models.Pizza.objects.filter(name__regex=r"[fF]lam*"))), 1)

    def test_get_transform_date(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(len(list(client_models.Pizza.objects.filter(from_date__year__exact=2016))), 2)

    def test_get_transform_date_gt(self):

        with self.assertNumQueries(1, using='api'):
            self.assertEqual(len(list(client_models.Pizza.objects.filter(from_date__year__lt=2016))), 1)


class TestQueryGet(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def assertObjectEqual(self, obj, data):
        for k, v in data.items():
            self.assertEqual(getattr(obj, k), v)

    def test_does_not_exists(self):
        with self.assertRaises(client_models.Pizza.DoesNotExist):
            client_models.Pizza.objects.get(pk=12345)

    def test_get(self):
        with self.assertNumQueries(1, using='api'):
            p = client_models.Pizza.objects.get(pk=1)
        with self.assertNumQueries(0, using='api'):
            self.assertObjectEqual(
                p,
                {
                    "id": 1,
                    "menu_id": 1,
                    "name": "supr\u00e8me",
                    "price": 10.0,
                    "from_date": datetime.date(2016, 11, 15),
                    "to_date": datetime.datetime(2016, 11, 20, 8, 46, 2, 16000),
                }
            )

    def test_simple_transform(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(len(list(client_models.Pizza.objects.filter(from_date__year=2016))), 2)

    def test_none(self):
        with self.assertNumQueries(0, using='api'):
            p = client_models.Pizza.objects.none()
        with self.assertNumQueries(0, using='api'):
            self.assertEqual(list(p), [])

    def test_get_related(self):
        with self.assertNumQueries(1, using='api'):
            p = client_models.Pizza.objects.get(pk=1)
        with self.assertNumQueries(1, using='api'):
            menu = p.menu
        self.assertObjectEqual(
            menu,
            {
                "name": "main menu",
                "code": "mn"
            }
        )

    def test_get_many2many(self):
        p = client_models.Pizza.objects.get(pk=1)
        with self.assertNumQueries(1, using='api'):
            toppings = list(p.toppings.all().order_by('pk'))

        self.assertEqual(len(toppings), 5)
        self.assertEqual([t.id for t in toppings], [1, 2, 3, 4, 5])

    def test_get_values_list_simple(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.values_list('id', 'name').order_by('-id'))
        self.assertEqual(
            res,
            [
                [3, "miam d'oie"],
                [2, 'flam'],
                [1, 'suprème']
            ]
        )

    def test_get_values_list_fk(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.values_list('id', 'menu__name').order_by('-id'))
        self.assertEqual(
            res,
            [[3, None], [2, None], [1, 'main menu']]
        )

    def test_get_values_list_backward_fk(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Menu.objects.values_list('id', 'pizzas__name').order_by('-id'))
        self.assertEqual(
            res,
            [[1, 'suprème']]
        )

    def test_get_no_result(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Menu.objects.filter(name='noname').values_list('id'))
        self.assertEqual(res, [])

    def test_chunked_read_not_enouth_data(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.all().
                       order_by('id').values_list('id', 'toppings__id'))

        self.assertEqual(
            [(i, set(j)) for i, j in res],
            [
                (1, {1, 2, 3, 4, 5}),
                (2, {1, 4}),
                (3, {1, 4, 6})
            ]
        )

    def test_chunked_read_auto_activate(self):
        nb_of_pizzas = 23
        for i in range(nb_of_pizzas):
            m = api_models.Pizza.objects.create(
                name='pizza %s' % i,
                price=i
            )
            for topping in api_models.Topping.objects.filter(pk__in=[5, (i % 3) + 1]):
                m.toppings.add(topping)
        with self.assertNumQueries(3, using='api'):
            res = list(client_models.Pizza.objects.all().values_list('id', 'toppings__id').order_by('id'))
        self.assertEqual(len(res), nb_of_pizzas + 3)

    def test_query_backward(self):
        res = list(client_models.Topping.objects.filter(pizzas=client_models.Pizza.objects.get(pk=1)))
        self.assertEqual(len(res), 5)

    def test_query_backward_values_sample(self):
        res = list(api_models.Topping.objects.filter(pizzas=api_models.Pizza.objects.get(pk=1)).values_list('pizzas'))
        self.assertEqual(len(res), 5)
        self.assertEqual(res, [(1, )] * 5)

    def test_query_backward_values_sample2(self):
        res = list(api_models.Topping.objects.order_by('pizzas__pk').values_list('pizzas'))
        self.assertEqual(len(res), 10)
        self.assertEqual(res, [(1,), (1,), (1,), (1,), (1,), (2,), (2,), (3,), (3,), (3,)])
        # self.assertEqual(res, [[1], [1], [1], [1], [1], [2], [2], [3], [3], [3]])

    def test_query_backward_values(self):
        # this case differ from the normal database, but it is not a mistake to return the list of all pizzas.
        # the test «test_query_backward_values_sample» which is the sample for a real database for this one return
        # only the list of 1. it is because of the filter which filter the pk of pizzas to 1. and then
        # the only pk for pizza returnid match this where clause. this is because the filter and the select
        # is done by only one query, and so contraints on the where apply to the select
        #
        # in our api, we make first the filter, and after we make other query retreiving the pk of pizzas. (as a list)
        # so, we first list all Toppings in pizza 1, and then we retrive all pizzas for these toppings. whith return
        # many more data than with one query filtered.

        res = list(
            client_models.Topping.objects.filter(
                pizzas=client_models.Pizza.objects.get(pk=1)
            ).order_by('pk', 'pizzas__pk').values_list('pizzas')
        )
        self.assertEqual(len(res), 9)
        # this order is matchin topping1: pizza1,2,3; topping2: pizza1, topping3:pizza1, etc
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            # sqlite compiler take into account the orderby in pizzas__pk.
            self.assertEqual(res,  [[1], [2], [3], [1], [1], [1], [2], [3], [1]])
        else:
            # postgresql compiler loos the orderby in the process
            self.assertEqual(len(res), 9)
            self.assertEqual(set(tuple(r) for r in res), {(1,), (2,), (3,)})

    def test_without_get_select_related_sample(self):
        with self.assertNumQueries(1, using='api'):
            p = client_models.Pizza.objects.get(pk=1)
        with self.assertNumQueries(1, using='api'):
            m = p.menu
        with self.assertNumQueries(0, using='api'):
            self.assertEqual(m.name, 'main menu')

    def test_get_select_related(self):
        with self.assertNumQueries(1, using='api'):
            p = client_models.Pizza.objects.select_related('menu').get(pk=1)
        with self.assertNumQueries(0, using='api'):
            m = p.menu
        with self.assertNumQueries(0, using='api'):
            self.assertEqual(m.name, 'main menu')

    def test_prefetch_related_sample(self):
        with self.assertNumQueries(2):
            p = api_models.Pizza.objects.prefetch_related('toppings').get(pk=1)

        with self.assertNumQueries(0):
            self.assertEqual(len(list(p.toppings.all())), 5)

    def test_prefetch_related(self):
        with self.assertNumQueries(2, using='api') as queries:
            p = client_models.Pizza.objects.prefetch_related('toppings').get(pk=1)
            self.assertNotIn('filter_to_prefetch=true', queries[0]['sql'])
            self.assertIn('filter_to_prefetch=true', queries[1]['sql'])
        with self.assertNumQueries(0, using='api'):
            self.assertEqual(len(list(p.toppings.all())), 5)

    def test_exists(self):
        with self.assertNumQueries(1, using='api'):
            self.assertTrue(client_models.Pizza.objects.filter(pk=1).exists())
        with self.assertNumQueries(1, using='api'):
            self.assertFalse(client_models.Pizza.objects.filter(name="une pizza").exists())

    def test_limited_query(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.all().order_by('id')[:1])
        self.assertEqual(len(res), 1)

    def test_limited_query_sample(self):
        with self.assertNumQueries(1):
            res = list(api_models.Pizza.objects.all().order_by('id')[:1])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, 1)

    def test_limited_with_offset(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.all().order_by('id')[1:2])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, 2)

    def test_limited_with_offset_bad_offset_for_perfs(self):
        with self.assertNumQueries(2, using='api'):
            res = list(client_models.Pizza.objects.all().order_by('id')[1:3])
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, 2)
        self.assertEqual(res[1].id, 3)

    def test_limited_with_offset_good_offset_for_perfs(self):
        with self.assertNumQueries(1, using='api'):
            res = list(client_models.Pizza.objects.all().order_by('id')[2:4])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, 3)

    def test_get_last(self):
        with self.assertNumQueries(1, using='api'):
            res = client_models.Pizza.objects.all().order_by('id').last()
        self.assertEqual(res.id, 3)

    def test_query_no_result(self):
        with self.assertNumQueries(0, using='api'):
            self.assertEqual(list(client_models.Pizza.objects.filter(pk=1).filter(pk=2)), [])

    def test_query_pagination_no_meta(self):
        old_meta_val = SQLCompiler.META_NAME
        SQLCompiler.META_NAME = "lolilol"
        try:
            with self.assertNumQueries(1, using='api'):
                self.assertEqual(
                    list(client_models.Pizza.objects.values_list('pk')),
                    [[1], [2], [3]]
                )
        finally:
            SQLCompiler.META_NAME = old_meta_val

    def test_query_pk_empty_in(self):
        with self.assertNumQueries(0, using='api'):
            res = client_models.Pizza.objects.filter(id__in=[])
        self.assertEqual(list(res), [])

    def test_query_field_empty_in(self):
        with self.assertNumQueries(0, using='api'):
            res = client_models.Pizza.objects.filter(name__in=[])
        self.assertEqual(list(res), [])


class TestQueryCount(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def test_count(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(client_models.Pizza.objects.all().count(), 3)

    def test_count_ensure_no_cache(self):
        with self.assertNumQueries(1, using='api'):
            q = client_models.Pizza.objects.all().distinct()
            self.assertEqual(q.query.get_count(using=q.db), 3)

    def test_count_no_result(self):
        api_models.Pizza.objects.all().delete()
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(client_models.Pizza.objects.all().count(), 0)

    def test_count_filter_order_and_all(self):
        with self.assertNumQueries(1, using='api'):
            self.assertEqual(client_models.Pizza.objects.filter(pk__in=[1, 2]).order_by('id').count(), 2)


class TestQueryDelete(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def test_delete_obj(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        p = client_models.Pizza(pk=1)
        with self.assertNumQueries(1, using='api'):
            p.delete()
        self.assertEqual(api_models.Pizza.objects.count(), 2)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())

    def test_delete_qs_one(self):
        n = api_models.Pizza.objects.count()

        self.assertEqual(n, 3)
        with self.assertNumQueries(2, using='api'):
            client_models.Pizza.objects.filter(pk=1).delete()
        self.assertEqual(api_models.Pizza.objects.count(), 2)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=2).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=3).exists())

    def test_delete_qs_many(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        with self.assertNumQueries(3, using='api'):
            client_models.Pizza.objects.filter(Q(pk__in=(1, 2))).delete()
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())
        self.assertFalse(api_models.Pizza.objects.filter(pk=2).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=3).exists())

    def test_delete_qs_many_range(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        with self.assertNumQueries(3, using='api'):
            client_models.Pizza.objects.filter(pk__range=(1, 2)).delete()
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())
        self.assertFalse(api_models.Pizza.objects.filter(pk=2).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=3).exists())

    def test_delete_qs_no_pk(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        with self.assertNumQueries(2, using='api'):
            client_models.Pizza.objects.filter(name='suprème').delete()
        self.assertEqual(api_models.Pizza.objects.count(), 2)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=2).exists())
        self.assertTrue(api_models.Pizza.objects.filter(pk=3).exists())

    def test_delete_qs_all(self):
        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        with self.assertNumQueries(4, using='api'):
            client_models.Pizza.objects.all().delete()
        self.assertEqual(api_models.Pizza.objects.count(), 0)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())
        self.assertFalse(api_models.Pizza.objects.filter(pk=2).exists())
        self.assertFalse(api_models.Pizza.objects.filter(pk=3).exists())


class TestQueryUpdate(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def test_manual_update(self):
        p = api_models.Pizza.objects.get(pk=1)
        api_models.Menu.objects.get(pk=1)
        menu2 = api_models.Menu.objects.create(name="menu2", code="m2")

        res = self.client.patch(reverse('pizza-detail', kwargs={'pk': p.pk}),
                                data=json.dumps({'pizza': {'menu': menu2.pk}}),
                                content_type='application/json',
                                headers={"authorization": 'Basic YWRtaW46YWRtaW4='}
                                )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['pizza']['menu'], menu2.pk)

    def assertFieldsSameValues(self, a, b, excluded=None):
        # build commons attrubutes, excluding the excluded ones
        attrs = (
            {f.attname for f in a.__class__._meta.concrete_fields} &
            {f.attname for f in b.__class__._meta.concrete_fields}
        ) - set(excluded or [])

        for attr in attrs:
            self.assertEqual(getattr(a, attr), getattr(b, attr))

    def test_update_pizza(self):
        pizza_original = api_models.Pizza.objects.get(pk=1)
        p_api = client_models.Pizza.objects.get(pk=1)
        self.assertFieldsSameValues(pizza_original, p_api)
        p_api.name = 'super suprème'
        p_api.save()
        self.assertFieldsSameValues(pizza_original, p_api, excluded=['name'])
        self.assertNotEqual(p_api.name, pizza_original.name)
        pizza_original.refresh_from_db()
        self.assertFieldsSameValues(pizza_original, p_api)
        self.assertEqual(pizza_original.name, 'super suprème')

    def test_update_pizza_qs_one(self):
        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'suprème',
            2: 'flam',
            3: "miam d'oie",
        })
        with self.assertNumQueries(1, using='api'):
            nb_update = client_models.Pizza.objects.filter(pk=1).update(name='super suprème')
        self.assertEqual(nb_update, 1)
        pizza_original = api_models.Pizza.objects.get(pk=1)
        p_api = client_models.Pizza.objects.get(pk=1)
        self.assertFieldsSameValues(pizza_original, p_api)
        self.assertEqual(pizza_original.name, 'super suprème')

        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'super suprème',
            2: 'flam',
            3: "miam d'oie",
        })

    def test_update_pizza_qs_all(self):
        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'suprème',
            2: 'flam',
            3: "miam d'oie",
        })
        with self.assertNumQueries(4, using='api'):
            nb_update = client_models.Pizza.objects.update(name='une pizza')
        self.assertEqual(nb_update, 3)
        pizza_original = api_models.Pizza.objects.get(pk=1)
        p_api = client_models.Pizza.objects.get(pk=1)
        self.assertFieldsSameValues(pizza_original, p_api)
        self.assertEqual(pizza_original.name, 'une pizza')

        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'une pizza',
            2: 'une pizza',
            3: "une pizza",
        })

    def test_update_pizza_qs_one_filtered(self):
        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'suprème',
            2: 'flam',
            3: "miam d'oie",
        })
        with self.assertNumQueries(2, using='api'):
            nb_update = client_models.Pizza.objects.filter(name="suprème").update(name='super suprème')
        self.assertEqual(nb_update, 1)
        pizza_original = api_models.Pizza.objects.get(pk=1)
        p_api = client_models.Pizza.objects.get(pk=1)
        self.assertFieldsSameValues(pizza_original, p_api)
        self.assertEqual(pizza_original.name, 'super suprème')

        self.assertEqual(dict(api_models.Pizza.objects.values_list('id', 'name')), {
            1: 'super suprème',
            2: 'flam',
            3: "miam d'oie",
        })


class TestUnallowedQuery(TestCase):
    fixtures = ['data.json']
    databases = ["default", "api"]

    def test_raw_query_fail(self):
        self.assertRaisesMessage(NotSupportedError, "Only Col in sql select is supported", list,
                                 client_models.Pizza.objects.all().extra(select={'a': 'id'}))

    def test_aggregate_query_fail(self):
        self.assertRaisesMessage(NotSupportedError, "Only Col in sql select is supported",
                                 client_models.Pizza.objects.all().aggregate, Sum('cost'))

    def test_annotate_query_fail(self):

        self.assertRaisesMessage(NotSupportedError, "group by is not supported",
                                 list, client_models.Pizza.objects.all().annotate(Sum('cost')))

    def test_subquery_aggregate(self):
        qs = client_models.Pizza.objects.all().annotate(Sum('cost'))
        compiler = SQLAggregateCompiler(qs.query, connections['api'], 'api')
        self.assertRaisesMessage(
            NotSupportedError,
            "group by is not supported",
            compiler.execute_sql
        )
