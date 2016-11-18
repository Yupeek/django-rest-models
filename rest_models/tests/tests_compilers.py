# -*- coding: utf-8 -*-
import datetime
from unittest.case import skip

from django.db.utils import ProgrammingError
from django.test.testcases import TestCase

import testapp.models as client_models
import testapi.models as api_models


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

        for attr in ('name','price','from_date','to_date'):
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

        for attr in ('name','price','from_date','to_date'):
            self.assertEqual(getattr(new, attr), getattr(p, attr))

    def test_insert_missing_data(self):
        with self.assertRaises(ProgrammingError):
            p = client_models.Pizza.objects.create(
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
        self.assertEqual(p.cost, 777)  # value not changed

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


class TestQueryDelete(TestCase):
    fixtures = ['data.json']

    @skip("no delete currently")
    def test_delete_obj(self):

        n = api_models.Pizza.objects.count()
        self.assertEqual(n, 3)
        p = client_models.Pizza(pk=1)
        p.delete()
        self.assertEqual(api_models.Pizza.objects.count(), 2)
        self.assertFalse(api_models.Pizza.objects.filter(pk=1).exists())