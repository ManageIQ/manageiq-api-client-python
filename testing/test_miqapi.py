# -*- coding: utf-8 -*-
import re

import pytest

from httmock import all_requests, HTTMock
from manageiq_client.api import ManageIQClient as MiqApi


API_CONTENT = {
    "name": "API",
    "description": "REST API",
    "version": "2.4.0",
    "versions": [
        {
            "name": "2.4.0",
            "href": "http://www.test.com/api/v2.4.0"
        }
    ],
    "collections": [
        {
            "name": "servers",
            "href": "https://www.test.com/api/servers",
            "description": "EVM Servers"
        }
    ]
}

SERVERS_CONTENT = {
    "name": "servers",
    "count": 1,
    "subcount": 1,
    "resources": [
        {
            "href": "https://www.test.com/api/servers/1"
        }
    ]
}

SERVERS_W_ATTRIBUTES_CONTENT = {
    "name": "servers",
    "count": 1,
    "subcount": 1,
    "resources": [
        {
            "href": "https://www.test.com/api/servers/1",
            "id": 1,
            "name": "EVM",
            "region_number": 0
        }
    ]
}

SERVER_ENTITY_CONTENT = {
    "href": "https://www.test.com/api/servers/1",
    "id": 1,
    "name": "EVM"
}

SERVER_ENTITY_W_ATTRIBUTES_CONTENT = {
    "href": "https://www.test.com/api/servers/1",
    "id": 1,
    "name": "EVM",
    "region_number": 0
}


@all_requests
def api_mock(url, request):
    return {'status_code': 200,
            'content': API_CONTENT}


@all_requests
def servers_mock(url, request):
    entity_matched = re.match(r'/api[^?]*/[0-9]+', request.path_url)
    attributes_present = 'attributes' in request.path_url
    response = {'status_code': 200}

    if entity_matched and attributes_present:
        response['content'] = SERVER_ENTITY_W_ATTRIBUTES_CONTENT
    elif entity_matched:
        response['content'] = SERVER_ENTITY_CONTENT
    elif attributes_present:
        response['content'] = SERVERS_W_ATTRIBUTES_CONTENT
    else:
        response['content'] = SERVERS_CONTENT
    return response


@pytest.fixture(scope='module')
def api():
    with HTTMock(api_mock):
        api = MiqApi('http://www.test.com/api', ('admin', 'admin'), verify_ssl=False)
    return api


class TestEntities(object):
    def test_get_all(self, api):
        with HTTMock(servers_mock):
            srv = api.collections.servers.all[0]
            # cannot use hasattr here because it would try
            # to look for 'region_number' subcollection
            assert 'region_number' not in srv.__dict__
            srv.reload()
            assert 'region_number' not in srv.__dict__

    def test_get_all_w_attributes_str(self, api):
        with HTTMock(servers_mock):
            srv = api.collections.servers.all_include_attributes('region_number')[0]
            assert srv._attributes == 'region_number'
            assert srv.region_number == 0
            srv.reload()
            assert srv.region_number == 0

    def test_get_all_w_attributes_list(self, api):
        with HTTMock(servers_mock):
            srv = api.collections.servers.all_include_attributes(['region_number'])[0]
            assert srv._attributes[0] == 'region_number'
            assert srv.region_number == 0
            srv.reload()
            assert srv.region_number == 0

    def test_get_entity_from_api(self, api):
        with HTTMock(servers_mock):
            srv = api.get_entity('servers', 1)
            srv.reload()
            assert 'region_number' not in srv.__dict__

    def test_get_entity_from_collection(self, api):
        with HTTMock(servers_mock):
            srv = api.collections.servers(1)
            srv.reload()
            assert 'region_number' not in srv.__dict__

    def test_get_entity_w_attributes_from_api(self, api):
        with HTTMock(servers_mock):
            srv = api.get_entity('servers', 1, 'region_number')
            assert srv._attributes == 'region_number'
            assert srv.region_number == 0
            srv.reload()
            assert srv.region_number == 0

    def test_get_entity_w_attributes_from_collection(self, api):
        with HTTMock(servers_mock):
            srv = api.collections.servers(1, 'region_number')
            assert srv._attributes == 'region_number'
            assert srv.region_number == 0
            srv.reload()
            assert srv.region_number == 0
