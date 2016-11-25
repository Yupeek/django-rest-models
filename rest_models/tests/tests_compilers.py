# -*- coding: utf-8 -*-
import datetime
from unittest.case import skip

from django.db.models.query_utils import Q
from django.db.utils import ProgrammingError
from django.test.testcases import TestCase

import testapi.models as api_models
import testapp.models as client_models


class TestQueryInsert(TestCase):
    fixtures = ['user.json']

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
        p = client_models.Pizza.objects.create(
            name='savoyarde',
            price=13.3,
            from_date=datetime.datetime.today(),
            # to_date has default value
        )
        self.assertEqual(api_models.Pizza.objects.count(), 1)
        self.assertIsNotNone(p.pk)
        new = api_models.Pizza.objects.get(pk=p.pk)

        for attr in ('name', 'price', 'from_date', 'to_date'):
            self.assertEqual(getattr(new, attr), getattr(p, attr))

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


class TestQueryGet(TestCase):
    fixtures = ['data.json']

    def assertObjectEqual(self, obj, data):
        for k, v in data.items():
            self.assertEqual(getattr(obj, k), v)

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
            toppings = list(p.toppings.all())

        self.assertEqual(len(toppings), 5)
        self.assertEqual([t.id for t in toppings], [1, 2, 3, 4, 5])

    def test_get_values_list_simple(self):
        with self.assertNumQueries(1, using='api') as ctx:
            res = list(client_models.Pizza.objects.values_list('id', 'name').order_by('-id'))
        self.assertEqual(
            res,
            [
                (3, "miam d'oie"),
                (2, 'flam'),
                (1, 'suprème')
            ]
        )

    def test_get_values_list_fk(self):
        with self.assertNumQueries(1, using='api') as ctx:
            res = list(client_models.Pizza.objects.values_list('id', 'menu__name').order_by('-id'))
        self.assertEqual(
            res,
            [(3, None), (2, None), (1, 'main menu')]
        )

    @skip('not implemented')
    def test_get_values_list_backward_fk(self):
        with self.assertNumQueries(1, using='api') as ctx:
            res = list(client_models.Menu.objects.values_list('id', 'pizzas__name').order_by('-id'))
        self.assertEqual(
            res,
            [(1, 'suprème')]
        )


class TestQueryDelete(TestCase):
    fixtures = ['data.json']

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
            client_models.Pizza.objects.filter(Q(pk__in=(1,2))).delete()
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
