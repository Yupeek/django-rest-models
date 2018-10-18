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
    from django.contrib.postgres.fields import JSONField
except ImportError as e:
    class JSONField(object):
        def __init__(self, *args, **kwargs):
            raise ImportError("can't use JSONField if postgresql dependencies is not available")
else:
    class JSONField(JSONField):
        def get_prep_value(self, value):
            return value
