# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import logging
import time

import requests
from django.core.handlers.base import BaseHandler
from django.test.client import RequestFactory
from requests.adapters import BaseAdapter
from requests.cookies import extract_cookies_to_jar
from requests.exceptions import ConnectionError, Timeout
from requests.models import RequestEncodingMixin, Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers

from rest_models.backend.exceptions import FakeDatabaseDbAPI2
from rest_models.backend.utils import message_from_response

try:
    from urllib.parse import urlparse, urlunparse
except ImportError:  # pragma: no cover
    from urlparse import urlparse, urlunparse

logger = logging.getLogger("django.db.backends")


def build_url(url, params):
    """
    only for display purpose, parse the params and url to build the final api
    :param str url: the url path to use
    :param dict params: the dict with the GET parameters, as accepted by requests
    :return: the url with the get part
    :rtype: str
    """
    if params is None:
        result = url
    else:
        result = "%s?%s" % (url, RequestEncodingMixin._encode_params(params))
    return result


class LocalApiAdapter(BaseAdapter):

    SPECIAL_URL = "http://localapi"

    def __init__(self):
        self.request_factory = RequestFactory()
        super(LocalApiAdapter, self).__init__()

    def prepared_request_to_wsgi_request(self, prepared_request):
        """
        transform a PreparedRequest into a WsgiRequest for django to use
        :param requests.models.PreparedRequest prepared_request:
        :return: the request ready to use for django
        :rtype: django.core.handlers.wsgi.WSGIRequest
        """
        wsgi_request = self.request_factory.generic(
            method=prepared_request.method,
            path=prepared_request.url,
            data=prepared_request.body,
            content_type=prepared_request.headers.get('Content-Type', 'application/x-www-form-urlencoded')
        )
        for name, val in prepared_request.headers.items():
            wsgi_request.META['HTTP_' + name.upper()] = val
        return wsgi_request

    def http_response_to_response(self, http_response, prepared_request):
        """
        transform a WSGIResponse into a requests's Response model
        :param django.http.response.HttpResponse http_response: the http response send by django view
        :return: the requests's Response model corresponding to the http_response
        :rtype: Response
        """
        response = Response()

        # Fallback to None if there's no status_code, for whatever reason.
        response.status_code = getattr(http_response, 'status_code', None)

        # Make headers case-insensitive.
        response.headers = CaseInsensitiveDict(getattr(http_response._headers, 'headers', {}))

        # Set encoding.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = http_response
        response.reason = response.raw.reason_phrase
        response._content = http_response.content
        req = prepared_request

        if isinstance(req.url, bytes):  # pragma: no cover
            response.url = req.url.decode('utf-8')
        else:
            response.url = req.url

        # Add new cookies from the server.
        extract_cookies_to_jar(response.cookies, req, response)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):
        handler = BaseHandler()
        handler.load_middleware()
        wsgi_request = self.prepared_request_to_wsgi_request(request)
        http_response = handler.get_response(wsgi_request)
        requests_response = self.http_response_to_response(http_response, request)
        return requests_response

    def close(self):  # pragma: no cover
        pass


class ApiVerbShortcutMixin(object):

    def get(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("get", url, params=params, json=json, **kwargs)

    def head(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("head", url, params=params, json=json, **kwargs)

    def post(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("post", url, params=params, json=json, **kwargs)

    def put(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("put", url, params=params, json=json, **kwargs)

    def patch(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("patch", url, params=params, json=json, **kwargs)

    def options(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("options", url, params=params, json=json, **kwargs)

    def delete(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        :rtype: requests.Response
        """
        return self.request("delete", url, params=params, json=json, **kwargs)


class DebugApiConnectionWrapper(ApiVerbShortcutMixin):
    def __init__(self, connection, db):
        self.connection = connection
        self.db = db

    def __getattr__(self, attr):  # pragma: no cover
        cursor_attr = getattr(self.connection, attr)
        return cursor_attr

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.connection.close()

    def request(self, method, url, **kwargs):

        start = time.time()
        try:
            return self.connection.request(method, url, **kwargs)
        finally:
            stop = time.time()
            duration = stop - start
            sql = build_url(url, kwargs['params'])
            self.db.queries_log.append({
                'sql': "%s %s ||| %s" % (method, sql, kwargs),
                'time': "%.3f" % duration,
            })
            logger.debug('(%.3f) %s %s; args=%s' % (duration, method, sql, kwargs),
                         extra={'duration': duration, 'sql': sql, 'params': kwargs, 'method': method}
                         )


class ApiConnexion(ApiVerbShortcutMixin):
    """
    wrapper for request.Session that in fact implement useless methods like rollback which
    is not possible with a rest API
    """
    def __init__(self, url, auth=None, retry=3, timeout=3, backend=None, middlewares=(), ssl_verify=None):
        """
        create a persistent connection to the api
        :param str url: the base url for the api (host + port + start path)
        :param ApiAuthBase auth: the auth provider
        :param int retry: number of retry
        :param int|(int, int) timeout: the timeout to pass to the api
        :param DatabaseWrapper backend: the backend
        :param list[Middleware]|tuple[Middleware] middlewares:the list of middleware to execute for each query.
        """
        if not url.endswith('/'):
            # fix the miss configured url in the api (must end with a /)
            url = url + '/'
        self.session = requests.Session()
        self.session.mount(LocalApiAdapter.SPECIAL_URL, LocalApiAdapter())
        self.session.auth = self.auth = auth
        self.url = url
        self.retry = retry
        self.timeout = timeout
        self.backend = backend
        self._middlewares_scheduler = collections.defaultdict(list)
        self._requestid = 0
        if ssl_verify is not None:
            self.session.verify = ssl_verify
        for middleware in middlewares:
            self.push_middleware(middleware, 8)

    @property
    def middlewares(self):
        """
        the list of middleware to iterate over. ordered by priority from 1 to 10
        :return:
        """
        return list(itertools.chain(*(v for k, v in sorted(self._middlewares_scheduler.items()))))

    def push_middleware(self, middleware, priority=5):
        """
        push a middleware into the list, which will be called at each request and response processing
        :param ApiMiddleware middleware: the middleware to apppend
        :return:
        """
        self._middlewares_scheduler[priority].insert(0, middleware)

    def pop_middleware(self, middleware):
        for middlewares in self._middlewares_scheduler.values():
            try:
                middlewares.remove(middleware)
            except ValueError:
                pass

    def close(self):
        self.session.close()

    def __exit__(self, *args):
        self.close()

    def __enter__(self):
        return self

    def inc_request_id(self):
        """
        increment the request id and then return it
        :return:
        """
        self._requestid += 1
        return self._requestid

    def execute(self, sql, params=None):
        """

        :param sql: the usless sql
        :param params: the userless params
        :return:
        """
        params = params or {}
        return self._make_request(params)

    def _make_request(self, params):
        """
        finaly make the request. will pass all middleware on send and recieve
        :param params:
        :return:
        """
        requestid = self.inc_request_id()
        middlewares = self.middlewares
        i = 0
        for i, middleware in enumerate(middlewares):
            response = middleware.process_request(params, requestid, self)
            if response is not None:
                break
        else:
            # if the middleware did not override the real response, we make the query
            response = self.session.request(**params)
        for middleware in middlewares[i::-1]:  # iterate over all previously executed middlewares
            response = middleware.process_response(params, response, requestid) or response
        return response

    def rollback(self):  # pragma: no cover
        pass

    def commit(self):  # pragma: no cover
        pass

    def get_timeout(self):
        return self.timeout

    def request(self, method, url, **kwargs):
        """
        wrapper for requests.Session.get

        :param unicode method: the method to use
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes data: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the
            :class:`Request`.
        :param files: (optional) Dictionary of ``'filename': file-like-objects``
            for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable
            Basic/Digest/Custom HTTP Auth.
        :param float|tuple[float, float] timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :rtype: requests.Response

        """
        kwargs.setdefault("allow_redirects", False)
        kwargs.setdefault("timeout", self.get_timeout())
        kwargs.setdefault('stream', False)
        real_url = self.get_final_url(url)

        error = 0
        last_exception = None

        while error <= self.retry:
            try:
                # to stay compatible with django_debug_toolbar, we must
                # call execute on the cursor return by the backend, since this one is replaced
                # by django-debug-toolbar to state the query.
                if self.backend:
                    execute = self.backend.cursor().execute
                else:
                    execute = self.execute
                response = execute("%s %s" % (method.upper(), real_url), dict(method=method, url=real_url, **kwargs))

            except Timeout as e:
                error += 1
                last_exception = e
            except ConnectionError as e:
                error += 1
                last_exception = e
            else:

                if self.auth and hasattr(self.auth, 'raise_on_response_forbidden'):
                    self.auth.raise_on_response_forbidden(response)
                else:
                    if response.status_code in (403, 401):
                        raise FakeDatabaseDbAPI2.ProgrammingError(
                            "Access to database is Forbidden for user %s.\n%s" %
                            (self.auth[0] if isinstance(self.auth, tuple) else self.auth,
                             message_from_response(response))
                        )
                return response
        raise FakeDatabaseDbAPI2.OperationalError(
            "cound not connect to server: %s\nIs the API running on %s ? tried %d times" %
            (last_exception, self.url, error))

    def get_final_url(self, url):
        if url.startswith("/"):
            parsed_url = urlparse(url)
            api_url = urlparse(self.url)
            return urlunparse(api_url[:2] + parsed_url[2:])

        return self.url + url
