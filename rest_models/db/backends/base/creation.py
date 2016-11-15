# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.backends.base.creation import BaseDatabaseCreation

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
    create_test_db = do_nothing
    sql_destroy_indexes_for_model = do_nothing
    sql_indexes_for_field = do_nothing
    sql_table_creation_suffix = do_nothing
    sql_for_inline_foreign_key_references = do_nothing
    deserialize_db_from_string = do_nothing
    sql_for_pending_references = do_nothing
    sql_indexes_for_model = do_nothing
    sql_create_model = do_nothing
    destroy_test_db = do_nothing
