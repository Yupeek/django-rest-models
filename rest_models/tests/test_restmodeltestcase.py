# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os

from django.db import connections

from rest_models.test import RestModelTestCase


class TestLoadFixtureTest(RestModelTestCase):
    rest_fixtures = {
        '/c': str(os.path.join(os.path.dirname(__file__), 'rest_fixtures', 'data_test_fixtures.json')),
        "/a": [],
        "/b": [{
            "status_code": 503,
        }],
        "/d": [{
            "data": {
                "A": "a",
                "B": "b"
            }
        }],
        '/me/%(user)s/': [{'data': [1, 2]}]
    }

    database_rest_fixtures = {
        'api': rest_fixtures
    }

    def setUp(self):
        super(TestLoadFixtureTest, self).setUp()
        self.client = connections['api'].cursor()

    def test_fixtures_loaded(self):
        self.assertEqual(self.client.get('c').json(), {'C': 'c'})
        self.assertEqual(self.client.get('d').json(), {'A': 'a', 'B': 'b'})
        self.assertRaisesMessage(Exception, "the query %r was not provided as mocked data" % "/a",
                                 self.client.get, 'a')
        r = self.client.get('b')
        self.assertEqual(r.status_code, 503)

    def test_variable_fixtures(self):
        self.rest_fixtures_variables['user'] = '123'
        self.assertEqual(self.client.get('me/123/').json(), [1, 2])
        self.assertRaises(Exception, "the query %r was not provided as mocked data" % "/me/1234/",
                          self.client.get, 'me/1234/')
