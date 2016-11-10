# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.test.testcases import TestCase

from testapp.models import ModelA, ModelB

logger = logging.getLogger(__name__)


class MyTestCase(TestCase):

    def setUp(self):
        self.a = ModelA.objects.create()
        self.b = ModelB.objects.create(a=ModelA.objects.create())

    def test_queryset_get(self):
        self.assertEqual(ModelB.objects.exclude(a=None).last(), self.b)
