# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

import requests

logger = logging.getLogger(__name__)


class ApiConnexion(object):
    """
    wrapper for request.Session that in fact implement useless methods like rollback which
    is not possible with a rest API
    """
    def __init__(self, url, auth):
        self.session = requests.Session()
        self.session.auth = auth

    def rollback(self):
        pass

    def commit(self):
        pass
