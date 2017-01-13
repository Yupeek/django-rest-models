# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging
from importlib import import_module

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.validation import BaseDatabaseValidation

from rest_models.backend.connexion import ApiConnexion, DebugApiConnectionWrapper
from rest_models.backend.exceptions import FakeDatabaseDbAPI2

from .client import DatabaseClient
from .creation import DatabaseCreation
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor

logger = logging.getLogger(__name__)


def import_class(path):
    """
    import a component of a module by his path.
    ie module.submodule.ClassName return the class ClassName
    don't work for nested item. the class must be on the root of the module
    :param str path: the path to import
    :return: the class
    :rtype: type
    """
    lpath = path.split(".")
    module = import_module(".".join(lpath[:-1]))
    obj = getattr(module, lpath[-1])
    return obj


class DatabaseWrapper(BaseDatabaseWrapper):

    Database = FakeDatabaseDbAPI2
    vendor = 'rest_api'
    SchemaEditorClass = DatabaseSchemaEditor

    def __init__(self, *args, **kwargs):
        self.connection = None  # type: ApiConnexion

        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)

    def get_connection_params(self):
        authpath = self.settings_dict.get('AUTH', None)
        auth = authpath and import_class(authpath)(self, self.settings_dict)
        options = self.settings_dict.get('OPTIONS', {})

        params = {
            'url': self.settings_dict['NAME'],
            'auth': auth,
            'timeout': self.timeout,
            'backend': self,
            'middlewares': [import_class(path)() for path in self.settings_dict.get('MIDDLEWARES', ())],
            'ssl_verify': options.get('SSL_VERIFY', True)
        }
        return params

    def get_new_connection(self, conn_params):
        return ApiConnexion(**conn_params)

    @property
    def timeout(self):
        return self.settings_dict['OPTIONS'].get('TIMEOUT', 10)

    def init_connection_state(self):
        self.autocommit = True

    def create_cursor(self):
        return self.connection

    def make_cursor(self, cursor):
        return cursor

    def make_debug_cursor(self, cursor):
        return DebugApiConnectionWrapper(cursor, self)

    def close(self):
        # do nothing
        pass

    def _start_transaction_under_autocommit(self):
        pass

    def is_usable(self):
        c = self.connection
        try:
            c.head('', timeout=self.timeout)
            return True
        except FakeDatabaseDbAPI2.OperationalError:
            return False

    def _set_autocommit(self, autocommit):
        pass

    def cursor(self):
        # type: () -> ApiConnexion
        return super(DatabaseWrapper, self).cursor()

    def check(self):
        from rest_models.checks import api_struct_check

        api_struct_check(None)
