# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.db import connections
from rest_models.test import RestModelTestCase

import os


class TestLoadFixtureTest(RestModelTestCase):
    api_fixtures = {
        'c': os.path.join(os.path.dirname(__file__), 'api_fixtures', 'data_test_fixtures.json'),
        "a": [],
        "b": [{
            "status_code": 503,
        }],
        "d": [{
            "data": {
                "A": "a",
                "B": "b"
            }
        }],
        'me/%(user)s/': [{'data': [1, 2]}]
    }

    database_api_fixtures = {
        'api': api_fixtures
    }

    def setUp(self):
        super(TestLoadFixtureTest, self).setUp()
        self.client = connections['api'].cursor()

    def test_fixtures_loaded(self):
        self.assertEqual(self.client.get('c').json(), {'C': 'c'})
        self.assertEqual(self.client.get('d').json(), {'A': 'a', 'B': 'b'})
        self.assertRaisesMessage(Exception, "the query 'a' was not provided as mocked data", self.client.get, 'a')
        r = self.client.get('b')
        self.assertEqual(r.status_code, 503)

    def test_variable_fixtures(self):
        self.api_fixtures_variables['user'] = '123'
        self.assertEqual(self.client.get('me/123/').json(), [1, 2])
        self.assertRaisesMessage(Exception, "the query 'me/1234/' was not provided as mocked data",
                                 self.client.get, 'me/1234/')


