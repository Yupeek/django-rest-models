# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management import call_command
from django.test.testcases import TestCase

from rest_models.backend.client import DatabaseClient


class ClientTest(TestCase):
    def setUp(self):
        self.original_execute = DatabaseClient.execute_subprocess
        self.original_ports = DatabaseClient.port_range

    def tearDown(self):
        DatabaseClient.execute_subprocess = self.original_execute
        DatabaseClient.port_range = self.original_ports

    def test_existing_db(self):
        called = []

        def tmp_exec(self_dc, args, env):
            self.assertEqual(env['_resty_host'], 'http://localhost:8097/api/v2*')
            called.append(args)

        DatabaseClient.execute_subprocess = tmp_exec

        self.assertEqual(len(called), 0)
        call_command('dbshell', database='api')
        self.assertEqual(len(called), 1)

    def test_to_run_db(self):
        called = []

        def tmp_exec(self_dc, args, env):
            self.assertEqual(env['_resty_host'], 'http://localhost:8080/api/v2*')
            called.append(args)

        DatabaseClient.execute_subprocess = tmp_exec

        self.assertEqual(len(called), 0)
        call_command('dbshell', database='api2')
        self.assertEqual(len(called), 1)

    def test_run_error_server(self):
        DatabaseClient.port_range = (80, 80)  # this port wont work

        def tmp_exec(self_dc, args, env):
            raise AssertionError('the exec shall not being called')  # pragma: no cover

        DatabaseClient.execute_subprocess = tmp_exec
        self.assertRaises(Exception, call_command, 'dbshell', database='api')
