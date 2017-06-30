# -*- coding: utf-8 -*-
import pytest
import mock

from manageiq_client.api import ManageIQClient as MiqApi


def test_no_user_password_dict_list_or_tuple():
    with pytest.raises(ValueError):
        MiqApi('http://www.test.com', {})
        MiqApi('http://www.test.com', [])
        MiqApi('http://www.test.com', ())


def test_no_user_or_password_dict():
    with pytest.raises(ValueError):
        MiqApi('http://www.test.com', {'user': 'Bob'})
        MiqApi('http://www.test.com', {'password': 'Bob'})


@mock.patch('manageiq_client.api.ManageIQClient._load_data')
def test_token_passed_in_dict(self):
    MiqApi('http://www.test.com', {'token': '123234'})


def test_invalid_token_key():
    with pytest.raises(ValueError):
        MiqApi('http://www.test.com', {'Token': '123234'})
        MiqApi('http://www.test.com', {'Broken': '123234'})
        MiqApi('http://www.test.com', ['123234'])
        MiqApi('http://www.test.com', ('123234',))


@mock.patch('manageiq_client.api.ManageIQClient._load_data')
def test_valid_login_credentials(self):
    MiqApi('http://www.test.com', {'user': 'Bob', 'password': '12345'})
