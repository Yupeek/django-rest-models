# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from django.core.management import call_command
from django.test.testcases import TestCase
from io import StringIO


class TestIntrospection(TestCase):
    fixtures = ['data.json']

    def test_make_models(self):
        res = StringIO()
        call_command('inspectdb', database='api', stdout=res)
        self.assertIn('class Topping(models.Model):', res.getvalue())

