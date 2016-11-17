# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

logger = logging.getLogger(__name__)


class FakeDatabaseDbAPI2(object):
    class DataError(Exception):
        pass

    class OperationalError(Exception):
        pass

    class IntegrityError(Exception):
        pass

    class InternalError(Exception):
        pass

    class ProgrammingError(Exception):
        pass

    class NotSupportedError(Exception):
        pass

    class DatabaseError(Exception):
        pass

    class InterfaceError(Exception):
        pass

    class Error(Exception):
        pass