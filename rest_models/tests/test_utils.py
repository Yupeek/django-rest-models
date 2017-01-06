from __future__ import unicode_literals

import doctest
import os
import tempfile

from django.test.testcases import TestCase

import rest_models.utils
from rest_models.utils import JsonFixtures


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(rest_models.utils))
    return tests


PARTIAL_DATA_FIXTURES = str(os.path.join(os.path.dirname(__file__), 'rest_fixtures', 'data_test_fixtures.json'))
FULL_TEST_FIXTURES = str(os.path.join(os.path.dirname(__file__), 'rest_fixtures', 'full_test_fixtures.json'))


class TestLoadFixtures(TestCase):
    def test_fixtures_file_full_path(self):
        a = JsonFixtures(FULL_TEST_FIXTURES)
        self.assertEqual(a._load(), {
            'a': None,
            'b': 503,
            'd': {'A': 'a', 'B': 'b'}
        })

    def test_fixtures_file_full_str(self):
        a = JsonFixtures(str(FULL_TEST_FIXTURES))
        self.assertEqual(a._load(), {
            'a': None,
            'b': 503,
            'd': {'A': 'a', 'B': 'b'}
        })

    def test_raw_data(self):
        a = JsonFixtures(**{
            'a': None,
            'b': 503,
            'd': {'A': 'a', 'B': 'b'}
        })
        self.assertEqual(a._load(), {
            'a': None,
            'b': 503,
            'd': {'A': 'a', 'B': 'b'}
        })

    def test_fixtures_file_partial_path(self):
        a = JsonFixtures(
            c=PARTIAL_DATA_FIXTURES
        )
        self.assertEqual(a._load(), {'c': [{'data': {'C': 'c'}}, {}, {}]})

    def test_fixtures_file_partial_str(self):
        a = JsonFixtures(
            c=str(PARTIAL_DATA_FIXTURES)
        )
        self.assertEqual(a._load(), {'c': [{'data': {'C': 'c'}}, {}, {}]})

    def test_recursive(self):
        b = JsonFixtures(FULL_TEST_FIXTURES)
        a = JsonFixtures(b, c=[1, 2, 3])
        self.assertEqual(a._load(), {
            'a': None,
            'b': 503,
            'c': [1, 2, 3],
            'd': {'A': 'a', 'B': 'b'}
        })

    def test_args(self):
        a = JsonFixtures(
            FULL_TEST_FIXTURES,
            {
                'c': PARTIAL_DATA_FIXTURES
            },
            {
                'b': 502,
            }
        )
        self.assertEqual(a._load(), {
            'a': None,
            'b': 502,
            'c': [{'data': {'C': 'c'}}, {}, {}],
            'd': {'A': 'a', 'B': 'b'}
        })

    def test_type_error(self):
        self.assertRaises(ValueError, JsonFixtures, None)

    def test_variables_fixtures(self):
        o = object()
        a = JsonFixtures({
            "/me/%(userid)s/": o,
        })
        v = {}
        a.set_variable(v)
        with self.assertRaises(KeyError):
            a["/me/1234/"]
        v['userid'] = 1234
        self.assertIs(a["/me/1234/"], o)

    def test_load_bad_fixtures(self):
        _, path = tempfile.mkstemp(".json", text=True)
        file = open(path, "w")
        try:
            file.write("coucoubad json")
            file.flush()
            file.close()
            a = JsonFixtures(path)
            self.assertRaisesMessage(ValueError, 'error while loading ', a._load)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
