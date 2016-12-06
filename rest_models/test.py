# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test.testcases import TestCase
from rest_models.backend.middlewares import ApiMiddleware
from rest_models.router import get_default_api_database
from rest_models.utils import dict_contains, JsonFixtures


def not_found_raise(url, middleware):
    """
    raise an exception if the query is not found
    :param str url: the asked url
    :param MockDataApiMiddleware middleware: the middleware
    :return:
    """
    raise Exception("the query %r was not provided as mocked data" % url)


def not_found_continue(url, middleware):
    """
    do not do anything
    :param str url: the asked url
    :param MockDataApiMiddleware middleware: the middleware
    :return:
    """
    return None  # returning None in a process_request mean continue


class MockDataApiMiddleware(ApiMiddleware):
    """
    a middleware that totaly disablow a real query on the api.
    it will return a data for a given url, and record the numbers of query
    made.

    data_for_url is a dict with:

    .. code-block:: python

        {"/model/1/": [
            {
                'filter': {
                    'params': {
                        'filter{id.in}': [15894],
                        'exclude[]': {'*'}
                    }
                },
                'data': {...} ## copy past from the api for this response.
        ]
        }
    """

    def __init__(self, data_for_url=None, not_found=not_found_raise):
        data_for_url = data_for_url or {}
        self.data_for_url = data_for_url
        self.not_found = not_found

    def set_data_for_url(self, url, data):
        self.data_for_url[url] = data

    def process_request(self, params, requestid, connection):
        if not params['url'].startswith(connection.url):
            raise ImproperlyConfigured("strage case where the query don't go to our api") # pragma: no cover
        url = params['url'][len(connection.url)+1:]

        try:
            results_for_url = self.data_for_url[url]
        except KeyError:
            return self.not_found(url, self)
        # we have many results for this url.
        # the mocked result can add a special «filter» value along with «data»
        # that all items must match the one in the params to be ok.
        for mocked_result in results_for_url:
            if dict_contains(mocked_result.get('filter', {}), params):
                # all item in the for is ok.
                # we break and so won't pass into the «else» of the first for
                break
        else:
            # no mocked data have matched
            return self.not_found(url, self)

        data = mocked_result.get('data')
        status_code = mocked_result.get('status_code')
        if data is None and not status_code:
            # None return 204
            return self.empty_response()
        elif data is None:
            # int: statuscode
            return self.make_response(None, status_code)
        elif isinstance(data, (dict, list)):
            # dict,list: data to return
            return self.data_response(data)
        else:
            raise Exception("the given data don't match a proper type : %s not in (int, dict, list, None)" %
                            type(data))


class RestModelTestMixin(object):
    """
    a test case mixin that add the feathure to mock the response from an api

    """
    api_fixtures = {}
    """
    fixtures to give for this tests. all missing values will trigger a exception
    """

    database_api_fixtures = None

    @classmethod
    def setUpClass(cls):
        # populate the database_api_fixtures from the api_fixtures for moste case where
        # there is only one database targeting an api.
        super(RestModelTestMixin, cls).setUpClass()
        if cls.database_api_fixtures is None:
            cls.database_api_fixtures = {
                get_default_api_database(settings.DATABASES): cls.api_fixtures
            }

    def setUp(self):
        # add all mock_data middleware to the databsase
        self._mock_data_middleware = {}
        self.api_fixtures_variables = {}  # should be update by the tests, and by side effects work on mocked data
        for db_name, fixtures in self.database_api_fixtures.items():
            fixtures = JsonFixtures(fixtures)
            fixtures.set_variable(self.api_fixtures_variables)
            self._mock_data_middleware[db_name] = MockDataApiMiddleware(fixtures)
            dbwrapper = connections[db_name]
            dbwrapper.cursor().push_middleware(
                self._mock_data_middleware[db_name]
            )
        super(RestModelTestMixin, self).setUp()

    def tearDown(self):
        # remove all middelwaress
        for db_name, middleware in self._mock_data_middleware.items():
            connections[db_name].connection.pop_middleware(middleware)


class RestModelTestCase(RestModelTestMixin, TestCase):
    pass
