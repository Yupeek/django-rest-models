# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import copy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase
from rest_models.router import RestModelRouter

import testapp.models as client_models


class TestMigrationRouter(TestCase):

    def test_make_migration(self):
        call_command('makemigrations', app_label='testapi', interactive=False, dry_run=True, verbosity=0)
        call_command('makemigrations', app_label='testapp', interactive=False, dry_run=True, verbosity=0)


class TestApiResolution(TestCase):
    def test_api_db_not_provided(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': "testappsimple"
        }):
            from testappsimple.models import ModelA
            self.assertIn('api2', settings.DATABASES)
            self.assertRaises(ImproperlyConfigured, ModelA.objects.all().count)
            router = RestModelRouter()
            self.assertRaises(ImproperlyConfigured, getattr, router, "api_database_name")

    def test_only_one_api_provided(self):
        router = RestModelRouter()

        DB = copy.deepcopy(settings.DATABASES)
        del DB['api2']
        router.databases = DB
        self.assertEqual(router.api_database_name, 'api')

    def test_no_api_provided(self):
        router = RestModelRouter()

        DB = copy.deepcopy(settings.DATABASES)
        del DB['api2']
        del DB['api']
        router.databases = DB
        self.assertRaises(ImproperlyConfigured, getattr, router, "api_database_name")

    def test_allow_relation(self):
        router = RestModelRouter()
        UserModel = get_user_model()
        self.assertFalse(router.allow_relation(client_models.Pizza, client_models.Topping))
        self.assertFalse(router.allow_relation(client_models.Topping, client_models.Pizza))
        self.assertFalse(router.allow_relation(client_models.Pizza, UserModel))
        self.assertFalse(router.allow_relation(UserModel, client_models.Pizza))
        self.assertFalse(router.allow_relation(client_models.Bookmark, client_models.Pizza))

        self.assertIsNone(router.allow_relation(UserModel, client_models.Bookmark))

    def test_allow_migration(self):
        router = RestModelRouter()

        self.assertFalse(router.allow_migrate('api', 'testapp', 'Pizza'))  # api model on api db
        self.assertFalse(router.allow_migrate('api2', 'testapp', 'Pizza'))   # api model on api db
        self.assertFalse(router.allow_migrate('default', 'testapp', 'Pizza'))  # api model on legacy db
        self.assertIsNone(router.allow_migrate('default', 'testapi', 'Pizza'))  # legacy model on legacy db
        self.assertFalse(router.allow_migrate('api', 'testapi', 'Pizza'))  # legacy model on api db

        self.assertIsNone(router.allow_migrate('default', 'testapi'))  # final model not provided : don't know
