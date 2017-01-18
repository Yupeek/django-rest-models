# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.db.models.sql.constants import CURSOR, NO_RESULTS, SINGLE
from django.db.utils import OperationalError, ProgrammingError
from django.test.testcases import TestCase

from rest_models.backend.compiler import SQLCompiler
from rest_models.test import RestModelTestCase
from testapp.models import Pizza


class TestSqlCompiler(TestCase):
    """
    test for coverage use. specials cases are not easy to trigger with queryset
    """
    fixtures = ['data.json']

    def get_compiler(self, queryset):
        return SQLCompiler(queryset.query, connections['api'], 'api')

    def test_no_result(self):
        compiler = self.get_compiler(
            Pizza.objects.all(),
        )

        self.assertEqual(
            compiler.execute_sql(NO_RESULTS),
            None
        )

    def test_no_result_type(self):
        compiler = self.get_compiler(
            Pizza.objects.all()
        )
        self.assertEqual(compiler.execute_sql(None), None)

    def test_uniq_result_no_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1).filter(pk=2)
        )
        self.assertEqual(compiler.execute_sql(SINGLE), None)

    def test_no_result_no_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1).filter(pk=2)
        )
        self.assertEqual(list(compiler.execute_sql()), [])

    def test_get_cursor_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1)
        )
        self.assertRaises(ProgrammingError, compiler.execute_sql, CURSOR)


class TestErrorResponseFormat(RestModelTestCase):
    pizza_data = {
        "cost": 2.08,
        "to_date": "2016-11-20T08:46:02.016000",
        "from_date": "2016-11-15",
        "price": 10.0,
        "id": 1,
        "links": {
            "toppings": "toppings/"
        },
        "name": "suprème",
        "toppings": [
            1,
            2,
            3,
            4,
            5
        ],
        "menu": 1
    }
    rest_fixtures = {
        '/oauth2/token/': [
            {'data': {'scope': 'read write', 'access_token': 'HJKMe81faowKipJGKZSwg05LnfJmrU',
                      'token_type': 'Bearer', 'expires_in': 36000}}
        ],
        'pizza': [
            {
                'data': {
                    'pizzas': [pizza_data]
                }
            }
        ],
    }
    database_rest_fixtures = {'api': rest_fixtures}

    def test_remote_name_mismatch(self):
        with self.mock_api('pizza', {'pazzi': []}, using='api'):
            self.assertRaisesMessage(
                ImproperlyConfigured,
                'the response does not contains the result for pizzas',
                list,
                Pizza.objects.all()
            )

        with self.mock_api('pizza', {'pizzas': []}, using='api'):
            self.assertEqual(len(list(Pizza.objects.all())), 0)

    def test_remote_not_contains_id(self):

        with self.mock_api('pizza', {'menus': [{}], 'pizzas': [self.pizza_data]}, using='api'):
            self.assertRaisesMessage(
                OperationalError,
                'the response from the server does not contains the ID of the model.',
                list,
                Pizza.objects.all().select_related('menu')
            )
