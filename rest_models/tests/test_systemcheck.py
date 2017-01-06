# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.db.utils import ProgrammingError
from django.test.testcases import TestCase
from django.test.utils import modify_settings, override_settings

logger = logging.getLogger(__name__)


@override_settings(ROOT_URLCONF='testapi.badapi.urls')
@modify_settings(INSTALLED_APPS={
    'append': ['testapi.badapi', 'testapp.badapp'],
})
class SystemCheckTest(TestCase):

    fixtures = ['user.json']

    @classmethod
    def setUpClass(cls):
        super(SystemCheckTest, cls).setUpClass()
        call_command(
            'migrate',
            verbosity=0,
            interactive=False,
            test_flush=True)

    def setUp(self):
        from testapp.badapp import models
        self.models = models

    def test_query_ok(self):
        self.assertEqual(0, self.models.AA.objects.filter(a__name='a').all().count())

    def test_query_fail(self):
        with self.assertRaisesMessage(ProgrammingError, 'Invalid filter field: aa'):
            self.assertEqual(0, self.models.A.objects.filter(aa__name='a').all().count())

    def test_check_all_error(self):
        with self.assertRaises(SystemCheckError) as ctx:
            call_command('check')
        msg = ctx.exception.args[0]
        self.assertIn('has a field "aa"', msg)
        self.assertIn('has a field "bb"', msg)
        self.assertIn('OPTIONS http://localapi/api/v1/c => 404', msg)

    def test_check_one_error(self):
        with self.assertRaises(SystemCheckError) as ctx:
            call_command('check', 'badapp')
        msg = ctx.exception.args[0]
        self.assertIn('has a field "aa"', msg)
        self.assertIn('has a field "bb"', msg)
        self.assertIn('OPTIONS http://localapi/api/v1/c => 404', msg)

    def test_check_one_ok(self):
        call_command('check', 'testapp')
