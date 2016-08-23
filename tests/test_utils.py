# -*- coding: utf-8 -*-

from unittest import TestCase

from miqclient.utils import escape_filter

class TestUtils(TestCase):
    def test_escape_filter(self):
        self.assertEqual('"\'"', escape_filter("'"))
        self.assertEqual('"\'\'"', escape_filter("''"))
        self.assertEqual('"\'\'\'"', escape_filter("'''"))
        self.assertEqual("'\"'", escape_filter('"'))
        self.assertEqual("'\"\"'", escape_filter('""'))
        self.assertEqual("'\"\"\"'", escape_filter('"""'))
        self.assertEqual('1', escape_filter(1))
        self.assertEqual('NULL', escape_filter(None))
        self.assertEqual("''", escape_filter(''))
        self.assertEqual(u'"ěščřžýáíé"', escape_filter('ěščřžýáíé'))

