# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging

from django.test.testcases import TestCase

from testapp.models import ModelA, ModelB

logger = logging.getLogger(__name__)


class MyTestCase(TestCase):

    def setUp(self):
        self.b = ModelB.objects.create(a=ModelA.objects.create())
        self.b2 = ModelB.objects.create(a=ModelA.objects.create())
        self.a = ModelA.objects.create()

    def test_get(self):
        self.assertEqual(ModelA.objects.all().last(), self.a)

    def test_filter(self):
        self.assertEqual(ModelB.objects.exclude(a=None).first().pk, self.b.pk)

    def test_count(self):
        self.assertEqual(len(ModelA.objects.all()), 3)
        self.assertEqual(len(ModelB.objects.all()), 2)

    def test_restult(self):
        self.assertEqual([m.pk for m in ModelA.objects.all()], [13, 14, 15])
        self.assertEqual([m.pk for m in ModelB.objects.all()], [1, 2])