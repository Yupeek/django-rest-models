# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os

from django.db import connections

from rest_models.test import RestModelTestCase
from rest_models.utils import Path
from testapp.models import Menu


class TestLoadFixtureTest(RestModelTestCase):
    rest_fixtures = {
        'c': Path(os.path.join(os.path.dirname(__file__), 'rest_fixtures', 'data_test_fixtures.json')),
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

    database_rest_fixtures = {
        'api': rest_fixtures
    }

    def setUp(self):
        super(TestLoadFixtureTest, self).setUp()
        self.client = connections['api'].cursor()

    def test_fixtures_loaded(self):
        self.assertEqual(self.client.get('c').json(), {'C': 'c'})
        self.assertEqual(self.client.get('d').json(), {'A': 'a', 'B': 'b'})
        r = self.client.get('b')
        self.assertEqual(r.status_code, 503)

    def test_fixtures_loaded_missing(self):
        self.assertRaisesMessage(Exception,
                                 "the query 'a' was not provided as mocked data: "
                                 "urls was %r" % (['b', 'c', 'd'], ),
                                 self.client.get, 'a')

    def test_variable_fixtures(self):
        self.rest_fixtures_variables['user'] = '123'
        self.assertEqual(self.client.get('me/123/').json(), [1, 2])
        self.assertRaisesMessage(
            Exception, "the query 'me/1234/' was not provided as mocked data",
            self.client.get, 'me/1234/'
        )

    def test_mock_api(self):
        with self.mock_api('me/17', [1, 2, 3], using='api'):
            self.assertEqual(self.client.get('me/17').json(), [1, 2, 3])

    def test_mock_api_statuscode(self):
        with self.mock_api('me/17', [1, 2, 3], using='api', status_code=201):
            self.assertEqual(self.client.get('me/17').status_code, 201)
            self.assertEqual(self.client.get('me/17').json(), [1, 2, 3])

    def test_mock_api_pass(self):
        with self.mock_api('lol', [1, 2, 3], using='api'):
            self.assertEqual(self.client.get('b').status_code, 503)

    def test_track_queries(self):
        with self.track_query('api') as tracker:
            self.assertEqual(self.client.get('c').json(), {'C': 'c'})
            self.assertEqual(self.client.get('d').json(), {'A': 'a', 'B': 'b'})
        self.assertEqual(len(tracker.get_for_url('c')), 1)
        self.assertEqual(len(tracker.get_for_url('d')), 1)
        self.assertEqual(len(tracker.get_for_url('b')), 0)


class TestMockDataSample(RestModelTestCase):
    database_rest_fixtures = {'api': {  # api => response mocker for databasen named «api»
        'menulol': [  # url menulol
            {
                'filter': {  # set of filter to match
                    'params': {  # params => requests parameters to sort[],exclude[],filter{...},include[]
                        'filter{name}': ['lolilol'],  # with filter(name='lolilol')
                        'sort[]': ['-name']  # with order_by('-name')
                    }
                },
                'data': {
                    "menus": [],
                    "meta": {
                        "per_page": 10,
                        "total_pages": 1,
                        "page": 1,
                        "total_results": 0
                    }
                }
            },
            {
                'filter': [{
                    'params': {
                        'filter{name}': ['lolilol'],  # just the filter, no sorting
                    }
                }],
                'data': {
                    "menus": [
                        {
                            "links": {
                                "pizzas": "pizzas/"
                            },
                            "id": 1,
                            "pizzas": [
                                1
                            ],
                            "name": "main menu",
                            "code": "mn"
                        }
                    ],
                    "meta": {
                        "per_page": 10,
                        "total_pages": 1,
                        "page": 1,
                        "total_results": 1
                    }
                }
            },
            {  # response for post
                'filter': {
                    'method': 'post',
                    'json': {'menu': {'name': 'hey'}}  # posted data must match this
                },
                'data': {  # this will return a fake models created response
                    "menu": {
                        "id": 1,
                        "pizzas": [],
                        "name": "hey",
                        "code": "hy"
                    }
                },
                'status_code': 201  # the mandatory statuscode to return for a post success
            },
            {  # response for post
                'filter': {
                    'method': 'post',
                },
                'data': {
                    "menu": {
                        "id": 2,
                        "pizzas": [],
                        "name": "hello",
                        "code": "ho"
                    }
                },
                'status_code': 201
            },
            {  # fallback
                'filter': {},  # no filter => fallback
                'data': {
                    "menus": [
                        {
                            "links": {
                                "pizzas": "pizzas/"
                            },
                            "id": 1,
                            "pizzas": [
                                1
                            ],
                            "name": "lolilol",
                            "code": "mn"
                        },
                        {
                            "links": {
                                "pizzas": "pizzas/"
                            },
                            "id": 2,
                            "pizzas": [
                                2
                            ],
                            "name": "lolilol",
                            "code": "ll"
                        }
                    ],
                    "meta": {
                        "per_page": 10,
                        "total_pages": 1,
                        "page": 1,
                        "total_results": 2
                    }
                }

            }
        ],
    }}

    def test_multi_results_filter(self):
        # no filter/no sort => fallback
        self.assertEqual(len(list(Menu.objects.all())), 2)
        # no matching filter => fallback
        self.assertEqual(len(list(Menu.objects.filter(code='pr'))), 2)
        # no matching filter => fallback
        self.assertEqual(len(list(Menu.objects.filter(name='pr'))), 2)
        # matching filter/no sort => don't care for missing sort and return 1rst
        self.assertEqual(len(list(Menu.objects.filter(name='lolilol'))), 1)
        # no matching sort => 2nd found
        self.assertEqual(len(list(Menu.objects.filter(name='lolilol').order_by('name'))), 1)
        # no matching sort => 1st found
        self.assertEqual(len(list(Menu.objects.filter(name='lolilol').order_by('-name'))), 0)
        # no matching filter => fallback
        self.assertEqual(len(list(Menu.objects.filter(name='pr').order_by('-name'))), 2)

    def test_post_filter(self):
        # no filter/no sort => fallback
        m = Menu.objects.create(name='hey', code='!!')
        self.assertEqual(m.pk, 1)
        self.assertEqual(m.name, 'hey')
        self.assertEqual(m.code, 'hy')

        m = Menu.objects.create(name='prout', code='??')
        self.assertEqual(m.pk, 2)
        self.assertEqual(m.name, 'hello')
        self.assertEqual(m.code, 'ho')


class TestMockUrlResolving(RestModelTestCase):
    database_rest_fixtures = {'api': {
        '/root/': [  # url menulol
            {
                'filter': {
                },
                'data': {
                    "root": "root",

                }
            }
        ],
        'root/': [  # url menulol
            {
                'filter': {
                },
                'data': {
                    "root": "notroot",

                }
            }
        ]
    }}

    def test_fake_data_from_root(self):
        db = connections['api'].cursor()
        response = db.get('/root/')
        self.assertEqual(response.data, {'root': 'root'})

    def test_fake_data_from_not_root(self):
        db = connections['api'].cursor()
        response = db.get('root/')
        self.assertEqual(response.data, {'root': 'notroot'})
