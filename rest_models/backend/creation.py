# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging
import re

from django.conf import settings
from django.db.backends.base.creation import BaseDatabaseCreation

from rest_models.backend.connexion import LocalApiAdapter

logger = logging.getLogger(__name__)


def do_nothing(*args, **kwargs):
    pass


class DatabaseCreation(BaseDatabaseCreation):
    """
    dont create anything in this database: its an API noob
    """
    sql_destroy_indexes_for_field = do_nothing
    sql_remove_table_constraints = do_nothing
    sql_indexes_for_fields = do_nothing
    serialize_db_to_string = do_nothing
    sql_destroy_model = do_nothing
    sql_destroy_indexes_for_fields = do_nothing
    sql_destroy_indexes_for_model = do_nothing
    sql_indexes_for_field = do_nothing
    sql_table_creation_suffix = do_nothing
    sql_for_inline_foreign_key_references = do_nothing
    deserialize_db_from_string = do_nothing
    sql_for_pending_references = do_nothing
    sql_indexes_for_model = do_nothing
    sql_create_model = do_nothing
    destroy_test_db = do_nothing

    def create_test_db(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False):
        """
        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        # Don't import django.core.management if it isn't needed.
        if not self.connection.alias.startswith('TEST_'):
            test_database_name = self._get_test_db_name()
            settings.DATABASES[self.connection.alias]["NAME"] = test_database_name
            self.connection.settings_dict["NAME"] = test_database_name
        return self.connection.settings_dict["NAME"]

    def _get_test_db_name(self):
        """
        Internal implementation - returns the name of the test DB that will be
        created. Only useful when called from create_test_db() and
        _create_test_db() and when no external munging is done with the 'NAME'
        settings.
        """
        test_alias = 'TEST_'+self.connection.alias
        if settings.DATABASES.get(test_alias):
            return settings.DATABASES[test_alias]['NAME']
        name = self.connection.settings_dict['NAME']
        return re.sub('https?://[^/]+/', LocalApiAdapter.SPECIAL_URL + "/", name, count=1)
