# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.db.backends.base.operations import BaseDatabaseOperations

logger = logging.getLogger(__name__)


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = 'rest_models.backend.compiler'

    def sql_flush(self, *args, **kwargs):  # pragma: no cover
        return ""

    def quote_name(self, name):
        return "quoted(!%s!)" % name
