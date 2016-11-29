# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.db.utils import ConnectionHandler, ProgrammingError
from django.test.testcases import LiveServerTestCase, TestCase

from rest_models.backend.connexion import ApiConnexion, LocalApiAdapter
from rest_models.backend.exceptions import FakeDatabaseDbAPI2

logger = logging.getLogger(__name__)


class TestApiConnexion(LiveServerTestCase):
    fixtures = ['data.json']

    def setUp(self):
        self.client = ApiConnexion(self.live_server_url + "/api/v2/", auth=None)
        super(TestApiConnexion, self).setUp()

    def test_api_connectionerror(self):
        c = ApiConnexion("http://127.0.0.1:7777")
        self.assertRaisesMessage(FakeDatabaseDbAPI2.OperationalError, 'Is the API', c.get, '')

    def test_api_timeout(self):
        self.assertRaisesMessage(FakeDatabaseDbAPI2.OperationalError, 'Read timed out',
                                 self.client.get, 'wait', timeout=0.2)

    def test_api_get(self):
        r = self.client.get("pizza/1/")
        self.assertEqual(r.json()['pizza']['id'], 1)

    def test_api_filter(self):
        r = self.client.get('pizza/', params={'filter{id}': '1', 'include[]': 'toppings.*'})
        data = r.json()
        self.assertEqual(data['pizzas'][0]['id'], 1)
        self.assertEqual(len(data['toppings']), len(data['pizzas'][0]['toppings']))

    def test_api_post(self):
        r = self.client.post('pizza/', json=dict(pizza={
            "toppings": [
                2,
                3,
                5
            ],
            "from_date": "2016-11-15",
            "price": 13.0,
            "to_date": "2016-11-20T08:46:02.016000",
            "name": "chévre",
            "id": 1,
        }))
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertGreater(data['pizza']['id'], 3)

    def test_api_put(self):
        rget = self.client.get('pizza/1')
        data = rget.json()
        self.assertEqual(data['pizza']['price'], 10.0)
        data['pizza']['price'] = 0.
        rput = self.client.put('pizza/1', json=data)
        self.assertEqual(rput.status_code, 200)
        self.assertEqual(rput.json()['pizza']['price'], 0)
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.json()['pizza']['price'], 0)

    def test_api_patch(self):
        rget = self.client.get('pizza/1')
        data = rget.json()
        self.assertEqual(data['pizza']['price'], 10.0)
        rput = self.client.patch('pizza/1', json={'pizza': {'price': 0}})
        self.assertEqual(rput.status_code, 200)
        self.assertEqual(rput.json()['pizza']['price'], 0)
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.json()['pizza']['price'], 0)

    def test_api_delete(self):
        rget = self.client.get('pizza/1')
        self.assertEqual(rget.status_code, 200)
        self.client.delete('pizza/1')
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.status_code, 404)

    def test_api_options(self):
        rget = self.client.options('pizza/1')
        self.assertEqual(rget.status_code, 200)
        data = rget.json()
        self.assertIn('include[]', data['features'])

    def test_auth_forbiden(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=None)
        self.assertRaises(ProgrammingError, c.patch, 'authpizza/1', json={'pizza': {'price': 0}})

    def test_auth_admin(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=('admin', 'admin'))
        r = c.patch('authpizza/1', json={'pizza': {'price': 0}})
        self.assertEqual(r.status_code, 200)

    def test_auth_no_rigth(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=('user1', 'user1'))
        self.assertRaises(ProgrammingError, c.patch, 'authpizza/1', json={'pizza': {'price': 0}})

    def test_auth_bad_cred(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=('user1', 'badpasswd'))
        self.assertRaises(ProgrammingError, c.patch, 'authpizza/1', json={'pizza': {'price': 0}})


class TestLocalApiHandler(TestCase):
    fixtures = ['data.json']

    def setUp(self):
        self.live_server_url = LocalApiAdapter.SPECIAL_URL
        self.client = ApiConnexion(self.live_server_url + "/api/v2/", auth=None)

    def test_api_connectionerror(self):
        c = ApiConnexion("http://127.0.0.1:7777")
        self.assertRaisesMessage(FakeDatabaseDbAPI2.OperationalError, 'Is the API', c.get, '')

    def test_api_get(self):
        r = self.client.get("pizza/1/")
        self.assertEqual(r.json()['pizza']['id'], 1)

    def test_api_filter(self):
        r = self.client.get('pizza/', params={'filter{id}': '1', 'include[]': 'toppings.*'})
        data = r.json()
        self.assertEqual(data['pizzas'][0]['id'], 1)
        self.assertEqual(len(data['toppings']), len(data['pizzas'][0]['toppings']))

    def test_api_post(self):

        r = self.client.post('pizza/', json=dict(pizza={
                "toppings": [
                    2,
                    3,
                    5
                ],
                "from_date": "2016-11-15",
                "price": 13.0,
                "to_date": "2016-11-20T08:46:02.016000",
                "name": "chévre",
                "id": 1,
            })
                             )
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertGreater(data['pizza']['id'], 3)  # 3 is the id of the fixture

    def test_api_put(self):
        rget = self.client.get('pizza/1')
        data = rget.json()
        self.assertEqual(data['pizza']['price'], 10.0)
        data['pizza']['price'] = 0.
        rput = self.client.put('pizza/1', json=data)
        self.assertEqual(rput.status_code, 200)
        self.assertEqual(rput.json()['pizza']['price'], 0)
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.json()['pizza']['price'], 0)

    def test_api_patch(self):
        rget = self.client.get('pizza/1')
        data = rget.json()
        self.assertEqual(data['pizza']['price'], 10.0)
        rput = self.client.patch('pizza/1', json={'pizza': {'price': 0}})
        self.assertEqual(rput.status_code, 200)
        self.assertEqual(rput.json()['pizza']['price'], 0)
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.json()['pizza']['price'], 0)

    def test_api_delete(self):
        rget = self.client.get('pizza/1')
        self.assertEqual(rget.status_code, 200)
        self.client.delete('pizza/1')
        rget2 = self.client.get('pizza/1')
        self.assertEqual(rget2.status_code, 404)

    def test_api_options(self):
        rget = self.client.options('pizza/1')
        self.assertEqual(rget.status_code, 200)
        data = rget.json()
        self.assertIn('include[]', data['features'])

    def test_auth_forbiden(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=None)

        self.assertRaises(ProgrammingError, c.patch, 'authpizza/1', json={'pizza': {'price': 0}})

    def test_auth_admin(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=('admin', 'admin'))
        r = c.patch('authpizza/1', json={'pizza': {'price': 0}})
        self.assertEqual(r.status_code, 200)

    def test_auth_no_rigth(self):
        c = ApiConnexion(self.live_server_url + "/api/v2/", auth=('user1', 'user1'))
        self.assertRaises(ProgrammingError, c.patch, 'authpizza/1', json={'pizza': {'price': 0}})


class TestDatabaseWrapper(TestCase):
    fixtures = ['user.json']

    def setUp(self):
        self.ch = ConnectionHandler({
            'default': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/v2/',
                'USER': 'userapi',
                'PASSWORD': 'apipassword',
                'AUTH': 'rest_models.backend.auth.BasicAuth',
            },
            'bad': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/forbidden',
                'USER': 'userapi',
                'PASSWORD': 'badpassword',
                'AUTH': 'rest_models.backend.auth.BasicAuth',
            },
            'unavailable': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://129.0.0.1/',
                'USER': 'userapi',
                'PASSWORD': 'osef',
                'AUTH': 'rest_models.backend.auth.BasicAuth',
                'OPTIONS': {
                    'TIMEOUT': 0.1
                }
            },

        })

    def test_bad_password(self):
        wrapper = self.ch['bad']
        self.assertRaisesMessage(FakeDatabaseDbAPI2.ProgrammingError,
                                 'Access to database is Forbidden for user userapi', wrapper.ensure_connection)

    def test_good_password(self):
        wrapper = self.ch['default']
        wrapper.ensure_connection()

    def test_get_cursor(self):
        wrapper = self.ch['default']
        c = wrapper.cursor()
        self.assertIsNotNone(c)
        c.close()  # do nothing

    def test_cursor_execute_raises(self):
        c = self.ch['default'].cursor()
        self.assertRaises(NotImplementedError, c.execute, 'select * from table')

    def test_available(self):
        wrapper = self.ch['default']
        wrapper.connect()
        wrapper._start_transaction_under_autocommit()  # does nothing as expeced
        self.assertTrue(wrapper.is_usable())

    def test_unavailable(self):
        wrapper = self.ch['unavailable']
        wrapper.init_connection_state = lambda: None  # this method will check connectivity at connect time, we skip it
        wrapper.connect()
        self.assertFalse(wrapper.is_usable())
