# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import io
import unittest

from django.core.management import call_command
from django.test import override_settings
from django.test.testcases import TestCase


class TestIntrospection(TestCase):
    fixtures = ['data.json']
    databases = ['api', 'default']

    @override_settings(
        DEBUG=True,
    )
    @unittest.skip
    def test_make_models(self):
        # skiped test since it's hard to allow test database with IGNORE_INTROSPECT
        res = io.StringIO()
        call_command('inspectdb', database='api', stdout=res)
        self.assertIn('class Topping(models.Model):', res.getvalue())
        self.assertIn('class Review(models.Model):', res.getvalue())
