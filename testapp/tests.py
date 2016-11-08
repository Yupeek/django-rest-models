#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, absolute_import

from django.test.testcases import TestCase
import rest_models


class MyTest(TestCase):

    def test_import_version(self):
        self.assertIn('__VERSION__', dir(rest_models))
