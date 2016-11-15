# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from importlib import import_module

import requests
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.validation import BaseDatabaseValidation

from rest_models.db.backends.base.connexion import ApiConnexion
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


class FakeDatabaseDbAPI2(object):
    class DataError(Exception):
        pass

    class OperationalError(Exception):
        pass

    class IntegrityError(Exception):
        pass

    class InternalError(Exception):
        pass

    class ProgrammingError(Exception):
        pass

    class NotSupportedError(Exception):
        pass

    class DatabaseError(Exception):
        pass

    class InterfaceError(Exception):
        pass

    class Error(Exception):
        pass


class FakeCursor(object):
    def execute(self, sql):
        raise NotImplementedError("this is not a SQL database, so no cursor is available")

    def close(self):
        pass


class DatabaseWrapper(BaseDatabaseWrapper):

    Database = FakeDatabaseDbAPI2
    vendor = 'rest_api'
    SchemaEditorClass = DatabaseSchemaEditor

    def __init__(self, *args, **kwargs):

        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)

    def get_connection_params(self):
        authpath = self.settings_dict.get('AUTH', 'rest_models.db.backends.base.auth.basic')
        auth = import_class(authpath)(self.settings_dict)

        params = {
            'url': self.settings_dict['NAME'],
            'auth': auth,
        }
        return params

    def get_new_connection(self, conn_params):
        return ApiConnexion(**conn_params)

    def init_connection_state(self):
        pass

    def create_cursor(self):
        return FakeCursor()

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
