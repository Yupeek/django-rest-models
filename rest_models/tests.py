# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from unittest.case import TestCase

logger = logging.getLogger(__name__)


class MyTestCase(TestCase):

    def test_true(self):
        self.assertTrue(True)
