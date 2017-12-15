# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json
import pprint
import sys
from collections import OrderedDict
from contextlib import contextmanager

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connections
from django.test.testcases import TestCase

from rest_models.backend.middlewares import ApiMiddleware
from rest_models.router import get_default_api_database
from rest_models.utils import JsonFixtures, dict_contains

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:  # pragma: no cover
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse


# noinspection PyUnusedLocal
def not_found_raise(url, middleware, extra=''):
    """
    raise an exception if the query is not found
    :param str url: the asked url
    :param MockDataApiMiddleware middleware: the middleware
    :param str extra: extra data to display
    :return:
    """
    raise Exception("the query '%s' was not provided as mocked data: %s" % (url, extra))


# noinspection PyUnusedLocal
def not_found_continue(url, middleware, extra=''):
    """
    do not do anything
    :param str url: the asked url
    :param MockDataApiMiddleware middleware: the middleware
    :param str extra: extra data to display
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

    def process_request(self, params, requestid, connection):

        for url, results_for_url in self.data_for_url.items():
            if url.startswith('/'):
                parsed_query = urlparse(params['url'])
                if parsed_query.path == url:
                    break
            elif connection.url + url == params['url']:
                break
        else:
            missing_url = params["url"]
            if missing_url.startswith(connection.url):
                missing_url = missing_url[len(connection.url):]
            return self.not_found(missing_url, self, extra='urls was %s' % sorted([item[0]
                                                                                  for item
                                                                                  in self.data_for_url.items()]))
        # we have many results for this url.
        # the mocked result can add a special «filter» value along with «data»
        # that all items must match the one in the params to be ok.
        result_found = None
        if not isinstance(results_for_url, list):
            results_for_url = [results_for_url]
        for mocked_result in results_for_url:
            filters = mocked_result.get('filter', [{}])
            if not isinstance(filters, list):
                filters = [filters]
            for filter_ in filters:
                if dict_contains(filter_, params):
                    # all item in the for is ok.
                    # we break and so won't pass into the «else» of the first for
                    result_found = mocked_result
                    break
            if result_found:
                break
        if not result_found:
            # no mocked data have matched
            return self.not_found(url,
                                  self,
                                  extra='%s fixture for this url, but filter did not match' % len(results_for_url)
                                  )

        data = result_found.get('data')
        status_code = result_found.get('status_code')
        if data is None and not status_code:
            # None return 204
            return self.empty_response()
        elif data is None:
            # int: statuscode
            return self.make_response(None, status_code)
        elif isinstance(data, (dict, list)):
            # dict,list: data to return
            return self.data_response(data, status_code)
        else:
            raise Exception("the given data don't match a proper type : %s not in (int, dict, list, None)" %
                            type(data))


class TrackRequestMiddleware(ApiMiddleware):
    def __init__(self):
        self.queries = {}

    def process_request(self, params, requestid, connection):
        self.queries[requestid] = {
            'params': params,
        }

    def process_response(self, params, response, requestid):
        self.queries[requestid]['response'] = response

    def get_for_url(self, url):
        return [q for q in self.queries.values() if q['params']['url'].endswith(url)]


class MyJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set, frozenset)):
            return list(sorted(obj))
        return super(MyJSONEncoder, self).default(obj)


class PrintQueryMiddleware(ApiMiddleware):
    """
    a middleware that print all intercepted query in a format usable for tests fixtures.

    in settings::

        DATABASES['api']['MIDDLEWARES'].append(
            'rest_models.test.PrintQueryMiddleware',
        )
        REST_API_OUTPUT_FORMAT = 'json' # or 'pprint' or 'null'

    this will print all query in the json format. this print can be copy/posted into a json fixtures in
    the url list.

    ie output::

        ## BEGIN GET http://localapi:8001/api/v2/user/3238/ =>
        {'data': {'user': {'email': 'admin@exemple.com',
                           'first_name': '',
                           'id': 3238,
                           'last_name': '',
                           'links': {'poster': 'poster/'}}},
         'filter': {'json': None,
                     'method': 'get',
                     'params': {'exclude[]': {'*'}, 'include[]': {'id', 'first_name', 'email', 'last_name'}}},
         'status_code': 200}
        ## END GET http://localapi:8001/api/v2/user/3238/ <=

    ie fixture::

        {
            "user/3238/": [
                {'data': {'user': {'email': 'admin@exemple.com',
                'first_name': '',
                'id': 3238,
                'last_name': '',
                'links': {'poster': 'poster/'}}},
                'filter': {'json': None,
                'method': 'get',
                'params': {'exclude[]': {'*'}, 'include[]': {'id', 'first_name', 'email', 'last_name'}}},
                'status_code': 200}
            ]
        }

    the recipe is ::

        {
            "url_part_after_database_name": [
                <past from output>
            ]
        }

    """
    colors = {
        'reset': "\033[0m",
        'yellow': "\033[1;33m",
        'red': "\033[1;31m",
        'green': "\033[1;32m",
        'purple': "\033[1;35m",
        'white': "\033[1;37m",
    }

    def __init__(self, stream=sys.stdout, format_=None):
        self.reqid_to_url = {}
        self.stream = stream
        self.format = format_ or getattr(settings, 'REST_API_OUTPUT_FORMAT', 'null')

    def process_request(self, params, requestid, connection):
        if len(self.reqid_to_url) > 500:
            # prevent memory leak. this should not be a problem in dev prod
            self.reqid_to_url.clear()
        self.reqid_to_url[requestid] = connection.url

    def format_result(self, result, max_lines=255):
        return getattr(self, 'format_result_%s' % self.format)(result, max_lines)

    def format_result_pprint(self, result, max_lines):
        result = pprint.pformat(dict(result.items()), width=120)
        if result.count('\n') > max_lines:
            return repr(result)
        else:
            return result

    # noinspection PyUnusedLocal
    def format_result_null(self, result, max_lines):
        if hasattr(settings, 'REST_API_OUTPUT_FORMAT'):
            return '<truncated by settings.REST_API_OUTPUT_FORMAT="null">'
        else:
            return '<truncated by missing settings.REST_API_OUTPUT_FORMAT>'

    def format_result_json(self, result, max_lines):
        result = json.dumps(result, indent=4, cls=MyJSONEncoder)
        if result.count('\n') > max_lines:
            return json.dumps(result, cls=MyJSONEncoder)
        else:
            return result

    def process_response(self, params, response, requestid):
        url = params['url']
        url_from_api = self.reqid_to_url.pop(requestid, '')
        if url.startswith(url_from_api):
            url = url[len(url_from_api):]
        try:
            response_data = response.json() if response.text != '' else {}
            result_sample = OrderedDict([
                ("filter", {
                    "params": params['params'],
                    "method": params['method'],
                    "json": params['json']
                }),
                ("data", response_data),
                ("status_code", response.status_code),
            ])
            result = self.format_result(result_sample)

        except (ValueError, TypeError) as e:
            result = {
                "text": response.text,
                "exception": e
            }

        print("{white}##{reset} {green}BEGIN{reset} {white}{method}{reset} {purple}{url}{reset} =>".format(
            url=url, method=params['method'].upper(), **self.colors), file=self.stream)
        print(result, file=self.stream)
        print("{white}##{reset} {red}END{reset} {white}{method}{reset} {purple}{url}{reset} <=".format(
            url=url, method=params['method'].upper(), **self.colors), file=self.stream)


# noinspection PyUnresolvedReferences,PyAttributeOutsideInit,PyPep8Naming
class RestModelTestMixin(object):
    """
    a test case mixin that add the feathure to mock the response from an api

    """
    rest_fixtures = {}
    """
    fixtures to give for this tests. all missing values will trigger a exception
    """

    database_rest_fixtures = None

    @classmethod
    def setUpClass(cls):
        # populate the database_rest_fixtures from the rest_fixtures for moste case where
        # there is only one database targeting an api.
        super(RestModelTestMixin, cls).setUpClass()
        if cls.database_rest_fixtures is None:
            cls.database_rest_fixtures = {
                get_default_api_database(settings.DATABASES): cls.rest_fixtures
            }

    def setUp(self):
        # add all mock_data middleware to the databsase
        self._mock_data_middleware = {}
        self.rest_fixtures_variables = {}  # should be update by the tests, and by side effects work on mocked data
        for db_name, fixtures in self.database_rest_fixtures.items():
            fixtures = JsonFixtures(fixtures)
            fixtures.set_variable(self.rest_fixtures_variables)
            self._mock_data_middleware[db_name] = MockDataApiMiddleware(fixtures)
            dbwrapper = connections[db_name]
            dbwrapper.cursor().push_middleware(
                self._mock_data_middleware[db_name],
                priority=9
            )
        super(RestModelTestMixin, self).setUp()

    def tearDown(self):
        # remove all middelwaress
        for db_name, middleware in self._mock_data_middleware.items():
            connections[db_name].connection.pop_middleware(middleware)

    @contextmanager
    def track_query(self, using=None):
        """
        :return: the middleware that tracked the queeries
        :rtype: TrackRequestMiddleware
        """
        connection = connections[using or get_default_api_database(settings.DATABASES)]
        middleware = TrackRequestMiddleware()
        cursor = connection.cursor()
        try:

            cursor.push_middleware(middleware, priority=6)
            yield middleware
        finally:
            cursor.pop_middleware(middleware)

    @contextmanager
    def mock_api(self, url, result, params=None, using=None, status_code=200):
        """
        assert that the eather one of the api have executed a query, with optionnaly the given params,
        the query was made `count` times and by the given API

        :param str|None url: the url in which the query was made. if None, all url will be count
        :param params: the params that must be present in the query
        :param str using: the name of connection to use
        :param int status_code: the status code to return for this query
        :param dict|None|list result: the temporary result to provide for the given time
        """
        connection = connections[using or get_default_api_database(settings.DATABASES)]
        mocked = {
            url: [{
                'filter': params or {},
                'data': result,
                'status_code': status_code
            }]
        }
        middleware = MockDataApiMiddleware(mocked, not_found=not_found_continue)
        cursor = connection.cursor()
        try:

            cursor.push_middleware(middleware, priority=7)
            yield
        finally:
            cursor.pop_middleware(middleware)


class RestModelTestCase(RestModelTestMixin, TestCase):
    pass
