from __future__ import unicode_literals

import doctest
import os
import sys
import tempfile

import six
from django.test.testcases import TestCase

import rest_models.utils
from rest_models.backend.connexion import ApiConnexion
from rest_models.test import MockDataApiMiddleware, PrintQueryMiddleware
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
            except OSError:  # pragma: no cover
                pass


class TestPrintQueryMiddleware(TestCase):
    def setUp(self):
        self.s = six.StringIO()
        self.mdlw = PrintQueryMiddleware(self.s)
        self.mdlw.colors = {
            'reset': "",
            'yellow': "",
            'red': "",
            'green': "",
            'purple': "",
            'white': "",
        }

        self.cnx = ApiConnexion(url='http://localapi/v2/')
        self.cnx.push_middleware(self.mdlw, 3)
        self.cnx.push_middleware(MockDataApiMiddleware({'/a': [{'data': {'res': 'a'}}],
                                                        'b': {'data': {'res': 'b'}},
                                                       'c': {'data': {'res': object()}}
                                                        }))

    def test_print_null_settings_missings(self):
        res = self.cnx.get('b', params={'name': 'rest'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.s.getvalue(), """## BEGIN GET b =>
<truncated by missing settings.REST_API_OUTPUT_FORMAT>
## END GET b <=
""")

    def test_print_null_settings_null(self):
        with self.settings(REST_API_OUTPUT_FORMAT='null'):
            res = self.cnx.get('b', params={'name': 'rest'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.s.getvalue(), """## BEGIN GET b =>
<truncated by settings.REST_API_OUTPUT_FORMAT="null">
## END GET b <=
""")

    def test_keep_call_middleware(self):
        for i in range(50):
            self.mdlw.process_request({}, i+700, self.cnx)
        self.assertEqual(len(self.mdlw.reqid_to_url), 50)
        self.cnx.get('b')
        self.assertEqual(len(self.mdlw.reqid_to_url), 50)

    def test_bug_call_middleware(self):
        for i in range(550):
            self.mdlw.process_request({}, i+700, self.cnx)
        self.assertEqual(len(self.mdlw.reqid_to_url), 49)
        self.cnx.get('b')
        self.assertEqual(len(self.mdlw.reqid_to_url), 49)

    def test_print_pprint(self):
        self.mdlw.format = 'pprint'
        res = self.cnx.get('b', params={'name': 'rest', 'l': list(range(15))})
        self.assertEqual(res.status_code, 200)
        output = self.s.getvalue()
        split_output = output.split('\n')
        self.assertEqual(split_output[0], "## BEGIN GET b =>")
        if six.PY2:
            expected = "u'params': {u'l': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], u'name': u'rest'}},"
        else:
            expected = "'params': {'l': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], 'name': 'rest'}},"

        for l in split_output:
            if expected in l:
                break
        else:
            self.fail("%s not found in %s" % (expected, split_output))

        self.assertEqual(len(split_output), 8)

    def test_print_pprint_long(self):
        self.mdlw.format = 'pprint'
        res = self.cnx.get('b', params={'name': 'rest', 'l': list(range(255))})  # generate many lines
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.s.getvalue().count('\n'), 3)

    def test_print_pprint_long2(self):
        self.mdlw.format = 'pprint'
        res = self.cnx.get('/a', params={'name': 'rest', 'l': list(range(255))})  # generate many lines
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.s.getvalue().count('\n'), 3)

    def test_print_json(self):
        self.maxDiff = None
        self.mdlw.format = 'json'
        res = self.cnx.get('b', params={'name': 'rest', 'l': list(range(15))})
        self.assertEqual(res.status_code, 200)
        output = self.s.getvalue()
        split_output = output.split('\n')
        self.assertEqual(split_output[0], "## BEGIN GET b =>")
        self.assertEqual(split_output[1], "{")
        self.assertEqual(split_output[2], '    "filter": {')
        self.assertEqual(len(split_output), 33)

    def test_print_json_long(self):
        self.mdlw.format = 'json'
        res = self.cnx.get('b', params={'name': 'rest', 'l': list(range(255))})  # generate many lines
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.s.getvalue().count('\n'), 3)

    def test_unserializable(self):
        self.mdlw.format = 'json'
        res = self.cnx.get('c')  # generate many lines
        self.assertEqual(res.status_code, 200)
        getvalue = self.s.getvalue()
        if six.PY2:
            self.assertIn("u'exception': TypeError('<object object at ",
                          getvalue)
            self.assertIn("u'text': \"{u'res': <object object at ",
                          getvalue)
        elif sys.version_info[:2] >= (3, 6):
            self.assertIn("'exception': TypeError(\"Object of type 'object' is not JSON serializable\"",
                          getvalue)
            self.assertIn("'text': \"{'res': <object object at ",
                          getvalue)
        else:
            self.assertIn("'exception': TypeError('<object object at ",
                          getvalue)
            self.assertIn("'text': \"{'res': <object object at ",
                          getvalue)
