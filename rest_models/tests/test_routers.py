# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function


from django.test import TestCase

from django.core.management import call_command


class TestMigrationRouter(TestCase):

    def test_make_migration(self):
        call_command('makemigrations', app_label='testapi', interactive=False, dry_run=True)
        call_command('makemigrations', app_label='testapp', interactive=False, dry_run=True)
