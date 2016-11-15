# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from requests.auth import AuthBase, HTTPBasicAuth

logger = logging.getLogger(__name__)


def basic(settings_dict):
    return HTTPBasicAuth(settings_dict['USER'], settings_dict['PASSWORD'])


class ApiAuthBase(AuthBase):
    def __init__(self, settings_dict):
        self.settings_dict = settings_dict


class OAuthToken(ApiAuthBase):

    def __call__(self, request):
        return request
