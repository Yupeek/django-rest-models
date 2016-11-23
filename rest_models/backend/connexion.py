# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

import requests
from django.core.handlers.base import BaseHandler
from django.core.handlers.wsgi import WSGIRequest
from django.test.client import RequestFactory
from requests.adapters import BaseAdapter
from requests.cookies import extract_cookies_to_jar
from requests.exceptions import ConnectionError, Timeout
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers
from rest_models.backend.exceptions import FakeDatabaseDbAPI2

logger = logging.getLogger(__name__)


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
        :rtype: WSGIRequest
        """
        wsgi_request = self.request_factory.generic(
            method=prepared_request.method,
            path=prepared_request.url,
            data=prepared_request.body,
            content_type=prepared_request.headers.get('Content-Type', 'application/octet-stream')
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


class ApiConnexion(object):
    """
    wrapper for request.Session that in fact implement useless methods like rollback which
    is not possible with a rest API
    """
    def __init__(self, url, auth=None, retry=3):
        self.session = requests.Session()
        self.session.mount(LocalApiAdapter.SPECIAL_URL, LocalApiAdapter())
        self.session.auth = self.auth = auth
        self.url = url
        self.retry = retry

    def rollback(self):  # pragma: no cover
        pass

    def commit(self):  # pragma: no cover
        pass

    def get_timeout(self):
        return 3.0

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

        assert not url.startswith("/"), "the url should not start with a «/»"
        error = 0
        last_exception = None

        while error <= self.retry:
            try:
                response = self.session.request(method, self.url + url, **kwargs)
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
                    if response.status_code == 403:
                        raise FakeDatabaseDbAPI2.ProgrammingError(
                            "Access to database is Forbidden for user %s.\n%s" %
                            (self.auth[0] if isinstance(self.auth, tuple) else self.auth, response.text)
                        )
                return response
        raise FakeDatabaseDbAPI2.OperationalError(
            "cound not connect to server: %s\nIs the API running on %s ? tried %d times" %
            (last_exception, self.url, error))

    def get(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("get", url, params=params, json=json, **kwargs)

    def head(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("head", url, params=params, json=json, **kwargs)

    def post(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("post", url, params=params, json=json, **kwargs)

    def put(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("put", url, params=params, json=json, **kwargs)

    def patch(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("patch", url, params=params, json=json, **kwargs)

    def options(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("options", url, params=params, json=json, **kwargs)

    def delete(self, url, params=None, json=None, **kwargs):
        """
        :param str url: the path relative to the current connexion
        :param dict[str, any]|byes params: (optional) Dictionary or bytes to append as GET parameters
        :param dict[str, any]|bytes json: (optional) Dictionary, bytes, or file-like object to send
            in the body
        :return:
        """
        return self.request("delete", url, params=params, json=json, **kwargs)
