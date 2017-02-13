# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management import call_command
from django.test.testcases import TestCase
import six


class TestIntrospection(TestCase):
    fixtures = ['data.json']

    def test_make_models(self):
        res = six.StringIO()
        call_command('inspectdb', database='api', stdout=res)
        self.assertIn('class Topping(models.Model):', res.getvalue())
