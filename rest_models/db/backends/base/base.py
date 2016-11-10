# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
import requests

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.validation import BaseDatabaseValidation

from .features import DatabaseFeatures
from .operations import DatabaseOperations
from .client import DatabaseClient
from .creation import DatabaseCreation
from .introspection import DatabaseIntrospection

logger = logging.getLogger(__name__)


class RestDatabaseWrapper(BaseDatabaseWrapper):

    vendor = 'sqlite'

    def __init__(self, *args, **kwargs):

        super(RestDatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)

    def get_connection_params(self):
        return {}

    def get_new_connection(self, conn_params):
        return requests.Session()

    def init_connection_state(self):
        pass

    def create_cursor(self):
        raise NotImplementedError("this is not a SQL database, so no cursor is available")

    def close(self):
        # do nothing
        pass

    def _start_transaction_under_autocommit(self):
        pass

    def is_usable(self):
        c = self.connection  # type: requests.Session
        c.head(self.settings_dict['NAME'], timeout=4)

    def _set_autocommit(self, autocommit):
        pass
