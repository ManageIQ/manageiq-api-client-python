import pytest
import mock

from manageiq_client.api import ManageIQClient as MiqApi

def test_no_user_password_auth_dict():
    with pytest.raises(KeyError):
        MiqApi('http://www.example.com', {})

def test_no_user_password_auth_tuple():
    with pytest.raises(ValueError):
        MiqApi('http://www.example.com', "")

def test_no_password_auth():
    with pytest.raises(KeyError):
        MiqApi('http://www.example.com', {'user': 'Fred'})

def test_no_user_auth():
    with pytest.raises(KeyError):
        MiqApi('http://www.example.com', {'password': 'secret'})

@mock.patch('manageiq_client.api.ManageIQClient._load_data')
def test_user_password(self):
    MiqApi('http://www.example.com', {'user': 'Fred', 'password': 'secret'})
    
@mock.patch('manageiq_client.api.ManageIQClient._load_data')
def test_token(self):
    MiqApi('http://www.example.com', {'x-auth-token': 'abcdef12345'})
    
     
