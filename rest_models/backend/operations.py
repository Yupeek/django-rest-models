# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.db.backends.base.operations import BaseDatabaseOperations

logger = logging.getLogger(__name__)


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = 'rest_models.backend.compiler'

    def sql_flush(self, *args, **kwargs):  # pragma: no cover
        return ""
