# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db import connections
from django.db.models.sql.constants import CURSOR, NO_RESULTS, SINGLE
from django.db.utils import ProgrammingError
from django.test.testcases import TestCase

from rest_models.backend.compiler import SQLCompiler
from testapp.models import Pizza


class TestSqlCompiler(TestCase):
    """
    test for coverage use. specials cases are not easy to trigger with queryset
    """
    fixtures = ['data.json']

    def get_compiler(self, queryset):
        return SQLCompiler(queryset.query, connections['api'], 'api')

    def test_no_result(self):
        compiler = self.get_compiler(
            Pizza.objects.all(),
        )

        self.assertEqual(
            compiler.execute_sql(NO_RESULTS),
            None
        )

    def test_no_result_type(self):
        compiler = self.get_compiler(
            Pizza.objects.all()
        )
        self.assertEqual(compiler.execute_sql(None), None)

    def test_uniq_result_no_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1).filter(pk=2)
        )
        self.assertEqual(compiler.execute_sql(SINGLE), None)

    def test_no_result_no_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1).filter(pk=2)
        )
        self.assertEqual(list(compiler.execute_sql()), [])

    def test_get_cursor_query(self):
        compiler = self.get_compiler(
            Pizza.objects.filter(pk=1)
        )
        self.assertRaises(ProgrammingError, compiler.execute_sql, CURSOR)
