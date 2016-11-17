# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.backends.base.introspection import BaseDatabaseIntrospection

logger = logging.getLogger(__name__)


class DatabaseIntrospection(BaseDatabaseIntrospection):
    def get_indexes(self, cursor, table_name):
        return []

    def get_key_columns(self, cursor, table_name):
        return []

    def get_table_list(self, cursor):
        return []

    def get_constraints(self, cursor, table_name):
        return []

    def django_table_names(self, only_existing=False, include_views=True):
        return []