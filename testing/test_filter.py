# -*- coding: utf-8 -*-
import pytest

from manageiq_client.filters import Q
from manageiq_client.utils import escape_filter


class TestEscapeFilter(object):
    def test_none(self):
        assert escape_filter(None) == u'NULL'

    def test_int(self):
        assert escape_filter(42) == u'42'

    def test_empty_string(self):
        assert escape_filter('') == "''"

    def test_string_single_quote(self):
        assert escape_filter("'") == '"\'"'

    def test_string_double_quote(self):
        assert escape_filter('"') == "'\"'"

    def test_unicode_characters(self):
        assert escape_filter(u'Příliš žluťoučký kůň úpěl ďábelské ódy.') == (
            u'"Příliš žluťoučký kůň úpěl ďábelské ódy."')

    def test_pre_quoted(self):
        assert escape_filter('"prequoted!"') == "'\"prequoted!\"'"


class TestQueryClass(object):
    def test_single(self):
        assert Q('foo', '=', 'bar').as_filters == ['foo = "bar"']

    def test_and(self):
        assert (Q('foo', '=', 'bar') & Q('xyz', '=', 'abc')).as_filters == [
            'foo = "bar"', 'xyz = "abc"']

    def test_or(self):
        assert (Q('foo', '=', 'bar') | Q('xyz', '=', 'abc')).as_filters == [
            'foo = "bar"', 'or xyz = "abc"']

    def test_bad_operator(self):
        with pytest.raises(ValueError):
            Q('foo', 'explode', 'bar')
