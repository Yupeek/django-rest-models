# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

logger = logging.getLogger(__name__)


def message_from_response(response):
    return "[%d]%s" % (
        response.status_code,
        response.text if '<!DOCTYPE html>' not in response.text[:30] else response.reason
    )
