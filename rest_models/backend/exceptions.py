# -*- coding: utf-8 -*-

from django.db.utils import (DatabaseError, DataError, Error, IntegrityError, InterfaceError, InternalError,  # noqa
                             NotSupportedError, OperationalError, ProgrammingError)

__ALL__ = ['ProgrammingError', 'OperationalError', 'IntegrityError', 'InternalError',
           'NotSupportedError', 'DatabaseError', 'InterfaceError', 'Error']


class FakeDatabaseDbAPI2(object):
    ProgrammingError = ProgrammingError
    OperationalError = OperationalError
    IntegrityError = IntegrityError
    InternalError = InternalError
    NotSupportedError = NotSupportedError
    DatabaseError = DatabaseError
    InterfaceError = InterfaceError
    Error = Error
    DataError = DataError
