# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.backends.base.creation import BaseDatabaseCreation

logger = logging.getLogger(__name__)


class DatabaseCreation(BaseDatabaseCreation):
    def sql_destroy_indexes_for_field(self, model, f, style):
        raise NotImplementedError("database is not creatable")

    def sql_remove_table_constraints(self, model, references_to_delete, style):
        raise NotImplementedError("database is not creatable")

    def sql_indexes_for_fields(self, model, fields, style):
        raise NotImplementedError("database is not creatable")

    def serialize_db_to_string(self):
        raise NotImplementedError("database is not creatable")

    def sql_destroy_model(self, model, references_to_delete, style):
        raise NotImplementedError("database is not creatable")

    def sql_destroy_indexes_for_fields(self, model, fields, style):
        raise NotImplementedError("database is not creatable")

    def create_test_db(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False):
        raise NotImplementedError("database is not creatable")

    def sql_destroy_indexes_for_model(self, model, style):
        raise NotImplementedError("database is not creatable")

    def sql_indexes_for_field(self, model, f, style):
        raise NotImplementedError("database is not creatable")

    def sql_table_creation_suffix(self):
        raise NotImplementedError("database is not creatable")

    def sql_for_inline_foreign_key_references(self, model, field, known_models, style):
        raise NotImplementedError("database is not creatable")

    def deserialize_db_from_string(self, data):
        raise NotImplementedError("database is not creatable")

    def sql_for_pending_references(self, model, style, pending_references):
        raise NotImplementedError("database is not creatable")

    def sql_indexes_for_model(self, model, style):
        raise NotImplementedError("database is not creatable")

    def sql_create_model(self, model, style, known_models=set()):
        raise NotImplementedError("database is not creatable")

    def destroy_test_db(self, old_database_name, verbosity=1, keepdb=False):
        raise NotImplementedError("database is not creatable")
