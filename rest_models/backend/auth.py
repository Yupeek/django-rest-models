# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

from requests.auth import AuthBase, HTTPBasicAuth
from rest_models.backend.exceptions import FakeDatabaseDbAPI2

logger = logging.getLogger(__name__)


class ApiAuthBase(AuthBase):
    def __init__(self, settings_dict):
        self.settings_dict = settings_dict

    def raise_on_response_forbidden(self, response):
        if response.status_code == 403:
            raise FakeDatabaseDbAPI2.ProgrammingError(
                "Access to database is Forbidden for user %s on %s.\n%s" % (
                    self.settings_dict['USER'],
                    self.settings_dict['NAME'],
                    response.text
                )
            )


class BasicAuth(ApiAuthBase):

    def __init__(self, settings_dict):
        self.backend = HTTPBasicAuth(settings_dict['USER'], settings_dict['PASSWORD'])
        super(BasicAuth, self).__init__(settings_dict)

    def __call__(self, request):
        return self.backend(request)


class OAuthToken(ApiAuthBase):
    def __call__(self, request):
        return request
