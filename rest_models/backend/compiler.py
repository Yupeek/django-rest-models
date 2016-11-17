# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from random import randint

from django.db.models.sql.constants import MULTI, NO_RESULTS, SINGLE
from django.db.models.sql.compiler import SQLCompiler as BaseSQLCompiler

logger = logging.getLogger(__name__)


class SQLCompiler(BaseSQLCompiler):
    def __init__(self, query, connection, using):
        """

        :param django.db.models.sql.query.Query query:
        :param DatabaseWrapper connection:
        :param str using:
        """
        self.query = query
        self.connection = connection
        self.using = using
        self.quote_cache = {'*': '*'}
        # The select, klass_info, and annotations are needed by QuerySet.iterator()
        # these are set as a side-effect of executing the query. Note that we calculate
        # separately a list of extra select columns needed for grammatical correctness
        # of the query, but these columns are not included in self.select.
        self.select = None
        self.annotation_col_map = None
        self.klass_info = None
        self.subquery = False

    def compile(self, node, select_format=False):
        return None

    def execute_sql(self, result_type=MULTI):
        self.setup_query()


    def results_iter(self, results=None):
        """
        Returns an iterator over the results from executing this query.
        """
        if self.query.model.__name__ == "ModelA":
            yield (13,)
            yield (14,)
            yield (15,)
        elif self.query.model.__name__ == "ModelB":
            yield (1, 13)
            yield (2, 14)


class SQLInsertCompiler(SQLCompiler):
    def execute_sql(self, return_id=False):
        if return_id:
            if self.query.model.__name__ == "ModelA":
                return 13
            elif self.query.model.__name__ == "ModelB":
                return 1


class SQLDeleteCompiler(SQLCompiler):
    pass


class SQLUpdateCompiler(SQLCompiler):
    pass


class SQLAggregateCompiler(SQLCompiler):
    pass
