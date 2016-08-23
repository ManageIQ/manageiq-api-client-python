# -*- coding: utf-8 -*-

from miqclient.utils import escape_filter

def test_escape_filter():
    assert '"ěščřžýáíé"' == escape_filter(b"ěščřžýáíé")
    assert '"\'"' == escape_filter("'")
    assert '"\'\'"' == escape_filter("''")
    assert '"\'\'\'"' == escape_filter("'''")
    assert "'\"'" == escape_filter('"')
    assert "'\"\"'" == escape_filter('""')
    assert "'\"\"\"'" == escape_filter('"""')
    assert '1' == escape_filter(1)
    assert 'NULL' == escape_filter(None)
    assert "''" == escape_filter('')
