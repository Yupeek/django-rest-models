# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging
from collections import namedtuple

from django.db.utils import ProgrammingError
from requests.auth import AuthBase, HTTPBasicAuth

from rest_models.backend.exceptions import FakeDatabaseDbAPI2
from rest_models.backend.utils import message_from_response

try:
    from urllib.parse import urlparse, urlunparse
except ImportError:  # pragma: no cover
    from urlparse import urlparse, urlunparse

logger = logging.getLogger(__name__)


Token = namedtuple('Token', 'expiredate access_token token_type scope')


class ApiAuthBase(AuthBase):
    def __init__(self, databasewrapper, settings_dict):
        """
        create the auth backend for the databasewrapper and settings
        :param rest_models.backend.base.DatabaseWrapper databasewrapper: the database wrapper
        :param dict settings_dict: the settings for this connection
        """
        self.settings_dict = settings_dict
        self.databasewrapper = databasewrapper

    def raise_on_response_forbidden(self, response):
        if response.status_code == 403:
            raise FakeDatabaseDbAPI2.ProgrammingError(
                "Access to database is Forbidden for user %s on %s.\n%s" % (
                    self.settings_dict['USER'],
                    self.settings_dict['NAME'],
                    message_from_response(response)
                )
            )


class BasicAuth(ApiAuthBase):

    def __init__(self, databasewrapper, settings_dict):
        self.backend = HTTPBasicAuth(settings_dict['USER'], settings_dict['PASSWORD'])
        super(BasicAuth, self).__init__(databasewrapper, settings_dict)

    def __call__(self, request):
        return self.backend(request)


class OAuthToken(ApiAuthBase):

    @property
    def token(self):
        """
        return the valide token or fetch one new
        :rtype: Token
        """
        if not hasattr(self, '_token'):
            token = self._token = self.get_token()
        else:
            token = self._token
        if self.has_expired(token):
            token = self._token = self.get_token()
        return token

    @property
    def url_token(self):
        url_token = self.settings_dict.get('OPTIONS', {}).get('OAUTH_URL', '/oauth2/token/')
        parsed_url = urlparse(url_token)
        if parsed_url.netloc == '':
            name_url = urlparse(self.settings_dict['NAME'])
            url_token = urlunparse(name_url[:2] + parsed_url[2:])
        return url_token

    def get_token(self):
        """
        query the api to retrive a OAuth token
        :return: the token from the api
        :rtype: Token
        """
        conn = self.databasewrapper.cursor()
        params = {'grant_type': 'client_credentials'}
        # Get client credentials params
        response = conn.session.request(
            'POST',
            self.url_token,
            params=params,
            auth=(self.settings_dict['USER'], self.settings_dict['PASSWORD']),
            stream=False
        )
        if response.status_code != 200:
            raise ProgrammingError("unable to retrive the oauth token from %s: %s" %
                                   (self.url_token,
                                    message_from_response(response))
                                   )
        data = response.json()
        return Token(
            datetime.datetime.now() + datetime.timedelta(seconds=data['expires_in']),
            data['access_token'],
            data['token_type'],
            data['scope']
        )

    def has_expired(self, token):
        """
        check if a token has expired
        :param Token token: the token to check
        :return: True if the token has expired
        :rtype: bool
        """
        # false if expired in 10 sec
        return token.expiredate < (datetime.datetime.now() + datetime.timedelta(seconds=10))

    def __call__(self, request):
        if request.url != self.url_token:
            request.headers['Authorization'] = "Bearer %s" % self.token.access_token
        return request
