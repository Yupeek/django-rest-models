# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

logger = logging.getLogger(__name__)


def message_from_response(response):
    return "[%d]%s" % (
        response.status_code,
        response.text if '<!DOCTYPE html>' not in response.text[:30] else response.reason
    )


try:
    from django.db.models import JSONField as JSONFieldLegacy
except ImportError:
    try:
        from django.contrib.postgres.fields import JSONField as JSONFieldLegacy
    except ImportError:
        pass

try:
    class JSONField(JSONFieldLegacy):
        def get_prep_value(self, value):
            return value

        def from_db_value(self, value, expression, connection):
            try:
                return super().from_db_value(value, expression, connection)
            except TypeError:
                return value

except NameError:
    def JSONField(*args, **kwargs):
        return None
