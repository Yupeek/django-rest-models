# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db.utils import ConnectionHandler
from django.test.testcases import TestCase

from rest_models.backend.connexion import ApiConnexion
from rest_models.backend.middlewares import ApiMiddleware, FakeApiResponse
from rest_models.test import MockDataApiMiddleware


class StoreMiddleware(ApiMiddleware):
    queries = {}
    responses = {}

    def process_request(self, params, requestid, connection):
        self.queries[requestid] = params

    def process_response(self, params, response, requestid):
        self.responses[requestid] = response
        return response


class DummyMiddleware(ApiMiddleware):
    pass


class ReturnValueMiddleware(ApiMiddleware):
    data = {
        "pizza": {
            "from_date": "2016-11-15",
            "id": 1,
            "name": "suprème",
            "links": {
                "toppings": "toppings/"
            },
            "menu": 1,
            "cost": 2.08,
            "to_date": "2016-11-20T08:46:02.016000",
            "price": 10.0,
            "toppings": [
                1,
                2,
                3,
                4,
                5
            ]
        }
    }

    def process_request(self, params, requestid, connection):
        return self.data_response(self.data)


class RaiseMiddleware(ApiMiddleware):
    def process_request(self, params, requestid, connection):
        raise Exception("opps request")

    def process_response(self, params, response, requestid):
        raise Exception("opps response")  # pragma: no cover


class NoResultMiddleware(ApiMiddleware):
    def process_request(self, params, requestid, connection):
        return self.empty_response()


class TestMiddleware(TestCase):

    def setUp(self):
        StoreMiddleware.queries.clear()
        StoreMiddleware.responses.clear()
        self.ch = ConnectionHandler({
            'default': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/v2/',
                'MIDDLEWARES': []
            },
            'one': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/v2/',
                'MIDDLEWARES': [
                    'rest_models.tests.test_middlewares.DummyMiddleware',
                    'rest_models.tests.test_middlewares.DummyMiddleware',
                    'rest_models.tests.test_middlewares.DummyMiddleware',
                    'rest_models.tests.test_middlewares.DummyMiddleware',
                    'rest_models.tests.test_middlewares.StoreMiddleware',
                ]
            },
            'return': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://nohostoops/api/v2/',
                'MIDDLEWARES': [
                    'rest_models.tests.test_middlewares.DummyMiddleware',
                    'rest_models.tests.test_middlewares.StoreMiddleware',
                    'rest_models.tests.test_middlewares.ReturnValueMiddleware',
                ]
            },
            'raise': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/v2/',
                'MIDDLEWARES': [
                    'rest_models.tests.test_middlewares.RaiseMiddleware',
                    'rest_models.tests.test_middlewares.StoreMiddleware',  # won't be called
                ]
            },
            'empty': {
                'ENGINE': 'rest_models.backend',
                'NAME': 'http://localapi/api/v2/',
                'MIDDLEWARES': [
                    'rest_models.tests.test_middlewares.NoResultMiddleware',
                    'rest_models.tests.test_middlewares.StoreMiddleware',  # won't be called
                ]
            }
        })

    def tearDown(self):
        StoreMiddleware.queries.clear()
        StoreMiddleware.responses.clear()

    def test_no_middleware(self):
        response = self.ch['default'].cursor().get('')
        self.assertEqual(response.status_code, 200, response.text)

    def test_middleware_execute(self):
        response = self.ch['one'].cursor().get('')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([1], list(StoreMiddleware.queries.keys()))
        self.assertEqual([1], list(StoreMiddleware.responses.keys()))
        self.assertIs(response, StoreMiddleware.responses[1])
        self.assertEqual(StoreMiddleware.queries[1]['url'], 'http://localapi/api/v2/')

    def test_bypass_middleware(self):
        response = self.ch['return'].cursor().get('')
        self.assertIsInstance(response, FakeApiResponse)
        self.assertEqual(response.json(), ReturnValueMiddleware.data)

    def test_raise(self):
        self.assertRaisesMessage(Exception, 'opps request', self.ch['raise'].cursor().get, '')

    def test_empty(self):
        self.assertEqual(self.ch['empty'].cursor().get('').status_code, 204)


class TestFakeApiResponse(TestCase):
    def test_text_ok(self):
        r = FakeApiResponse({'name': 'darius'}, 200)
        self.assertEqual(r.json(), {'name': 'darius'})
        self.assertEqual(r.text, """{"name": "darius"}""")

    def test_text_fail(self):
        r = FakeApiResponse(object(), 204)
        self.assertTrue(r.text.startswith('<object object at'))


class TestMockDataError(TestCase):

    def setUp(self):
        super(TestMockDataError, self).setUp()
        self.mdlwr = MockDataApiMiddleware({
            'a': {'data': {'result': 'a'}},
            'b': {'data': {'result': 'b'}},
            'c': {'filter': {'method': 'post'}, 'data': {'result': 'b'}},
        })
        self.cnx = ApiConnexion(url='http://localapi/v2/')
        self.cnx.push_middleware(self.mdlwr, 3)

    def test_not_found(self):
        with self.assertRaises(Exception) as e:
            self.cnx.get('dada')
        self.assertEqual(e.exception.args, ("the query 'dada' was not provided as mocked data: "
                                            "urls was %s" % ['a', 'b', 'c'], ))

    def test_not_found_abs(self):
        with self.assertRaises(Exception) as e:
            self.cnx.get('/dada')
        self.assertEqual(e.exception.args, ("the query 'http://localapi/dada' was not provided as mocked data: "
                                            "urls was %s" % ['a', 'b', 'c'],))

    def test_found_bad_filters(self):
        with self.assertRaises(Exception) as e:
            self.cnx.get('c')
        self.assertEqual(e.exception.args, ("the query 'c' was not provided as mocked data: "
                                            "1 fixture for this url, but filter did not match",))

    def test_ok(self):
        self.cnx.post('c', data={})
        self.cnx.get('a')
