# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import copy
import logging

import six
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.db.utils import ProgrammingError
from django.test.testcases import TestCase
from django.test.utils import modify_settings, override_settings
from dynamic_rest.routers import directory

from rest_models.test import RestModelTestCase

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
            interactive=False)
#           settings.skip_check.set(False)

    @classmethod
    def tearDownClass(cls):
        # hack to prevent some global varible to be tainted by our activation of badapi
        try:
            del directory['a']
            del directory['aa']
            del directory['b']
            del directory['bb']
        except KeyError:
            pass

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
        self.assertIn('Serializer.many value corresponding to the local model a', msg)
        self.assertIn('OPTIONS http://localapi/api/v1/c => 404', msg)
        self.assertIn('SystemCheckError: System check identified some issues', msg)

    def test_check_one_error(self):
        with self.assertRaises(SystemCheckError) as ctx:
            call_command('check', 'badapp')
        msg = ctx.exception.args[0]
        self.assertIn('has a field "aa"', msg)
        self.assertIn('has a field "bb"', msg)
        self.assertIn('Serializer.many value corresponding to the local model a', msg)
        self.assertIn('OPTIONS http://localapi/api/v1/c => 404', msg)
        self.assertIn('SystemCheckError: System check identified some issues', msg)

    def test_check_one_ok(self):
        res = six.StringIO()
        call_command('check', 'testapp', stdout=res)
        self.assertEqual(res.getvalue(), '')


@override_settings(ROOT_URLCONF='testapi.badapi.urls')
@modify_settings(INSTALLED_APPS={
    'append': ['testapi.badapi', 'testapp.badapp'],
})
class TestErrorsCheck(RestModelTestCase):
    fixtures = ['user.json']

    res_ok = {
        'description': '', 'resource_name_plural': 'as',
        'parses': ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'],
        'renders': ['application/json', 'text/html'],
        'properties': {
            'id': {'type': 'integer', 'default': None, 'required': False, 'read_only': True, 'nullable': False,
                   'label': 'ID'},
            'bb': {'immutable': False, 'type': 'many', 'default': None, 'related_to': 'bbs', 'required': False,
                   'read_only': False, 'nullable': False, 'label': 'Bb'},
            'name': {'type': 'string', 'default': None, 'required': True, 'read_only': False, 'nullable': False,
                     'label': 'Name'}},
        'features': ['include[]', 'exclude[]', 'filter{}', 'page', 'per_page', 'sort[]'],
        'name': 'A List', 'resource_name': 'a'}

    database_rest_fixtures = {}

    @classmethod
    def tearDownClass(cls):
        # hack to prevent some global varible to be tainted by our activation of badapi
        try:
            del directory['a']
            del directory['aa']
            del directory['b']
            del directory['bb']
        except KeyError:
            pass

    def test_missing_feature(self):
        res_no_feature = copy.deepcopy(self.res_ok)
        res_no_feature['features'] = ['include[]', 'page', 'per_page', 'sort[]']
        with self.mock_api('a', result=res_no_feature, using='apifail'):
            with self.assertRaises(SystemCheckError) as ctx:
                call_command('check', 'badapp')
        msg = ctx.exception.args[0]

        self.assertIn('running with dynamic-rest ?', msg)
        self.assertIn('SystemCheckError: System check identified some ', msg)

    def test_ok_feature(self):
        with self.assertRaises(SystemCheckError) as ctx:
            call_command('check', 'badapp')
        msg = ctx.exception.args[0]

        self.assertNotIn('running with dynamic-rest ?', msg)
        self.assertIn('SystemCheckError: System check identified some ', msg)

    def test_missing_prop(self):
        res_missing_field = copy.deepcopy(self.res_ok)
        del res_missing_field['properties']['name']
        with self.mock_api('a', result=res_missing_field, using='apifail'):
            with self.assertRaises(SystemCheckError) as ctx:
                call_command('check', 'badapp')
        msg = ctx.exception.args[0]

        self.assertIn('the field A.name in not present on the remote serializer', msg)
        self.assertIn('SystemCheckError: System check identified some issues', msg)

    def test_too_many_choices(self):
        res_toomany_choices = copy.deepcopy(self.res_ok)
        res_toomany_choices['properties']['bb']['choices'] = [(i, str(i)) for i in range(150)]
        with self.mock_api('a', result=res_toomany_choices, using='apifail'):
            with self.assertRaises(SystemCheckError) as ctx:
                call_command('check', 'badapp')
        msg = ctx.exception.args[0]

        self.assertIn('the field A.bb has many choices values (150) in OPTIONS ', msg)
        self.assertIn('SystemCheckError: System check identified some issues', msg)
