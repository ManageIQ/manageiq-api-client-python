# -*- coding: utf-8 -*-
import pytest

from httmock import all_requests, HTTMock
from manageiq_client.api import ManageIQClient


API_CONTENT = {
    "name": "API",
    "description": "REST API",
    "version": "2.4.0",
    "versions": [
        {
            "name": "2.4.0",
            "href": "https://example/api/v2.4.0"
        }
    ],
    "collections": [
        {
            "name": "services",
            "href": "https://example/api/services",
            "description": "Services"
        }
    ]
}


SERVICE_CONTENT = {
    "href": "https://example/api/services/20",
    "id": 20,
    "name": "test_rest_service_5FmcQ",
    "actions": [
        {
            "name": "edit",
            "method": "post",
            "href": "https://example/api/services/20"
        },
        {
            "name": "delete",
            "method": "post",
            "href": "https://example/api/services/20"
        },
        {
            "name": "delete",
            "method": "delete",
            "href": "https://example/api/services/20"
        }
    ]
}


SERVICES_CONTENT = {
    "name": "services",
    "count": 1,
    "subcount": 1,
    "resources": [
        SERVICE_CONTENT
    ],
    "actions": [
        {
            "name": "create",
            "method": "post",
            "href": "https://example/api/services"
        },
        {
            "name": "edit",
            "method": "post",
            "href": "https://example/api/services"
        },
        {
            "name": "delete",
            "method": "post",
            "href": "https://example/api/services"
        }
    ]
}


@pytest.fixture(scope='module')
def service():
    with HTTMock(api_mock):
        api = ManageIQClient('https://example/api', ('admin', 'admin'), verify_ssl=False)
    with HTTMock(services_mock):
        services = api.collections.services
        services.reload()
    with HTTMock(service_mock):
        service = api.collections.services[0]
    return service


@all_requests
def service_mock(url, request):
    return {'status_code': 200,
            'content': SERVICE_CONTENT}


@all_requests
def services_mock(url, request):
    return {'status_code': 200,
            'content': SERVICES_CONTENT}


@all_requests
def api_mock(url, request):
    return {'status_code': 200,
            'content': API_CONTENT}


def test_actions_present():
    with HTTMock(api_mock):
        api = ManageIQClient('https://example/api', ('admin', 'admin'), verify_ssl=False)
    with HTTMock(services_mock):
        services = api.collections.services
        services.reload()
        assert hasattr(services.action.create, 'POST')
        assert hasattr(services.action.edit, 'POST')
        assert not hasattr(services.action.edit, 'PATCH')
        assert not hasattr(services.action.edit, 'PUT')
        assert hasattr(services.action.delete, 'POST')
    with HTTMock(service_mock):
        service = api.collections.services[0]
        assert hasattr(service.action.edit, 'PATCH')
        assert hasattr(service.action.edit, 'POST')
        assert hasattr(service.action.edit, 'PUT')
        assert hasattr(service.action.delete, 'POST')
        assert hasattr(service.action.delete, 'DELETE')


def test_edit_patch(service, captured_log):
    with HTTMock(service_mock):
        outcome = service.action.edit.PATCH({
            "action": "edit",
            "path": "name",
            "value": "new"
        })
        assert outcome.id == service.id
    assert '[RESTAPI] PATCH' in captured_log.getvalue()
    assert service.collection._api.response.request.method == 'PATCH'


def test_edit_post(service, captured_log):
    with HTTMock(service_mock):
        outcome = service.action.edit.POST(name='new')
        assert outcome.id == service.id
    assert '[RESTAPI] POST' in captured_log.getvalue()
    response = service.collection._api.response
    assert response.request.method == 'POST'
    assert 'action' in response.request.body
    assert 'resource' in response.request.body


def test_edit_put(service, captured_log):
    with HTTMock(service_mock):
        outcome = service.action.edit.PUT(name='new')
        assert outcome.id == service.id
    assert '[RESTAPI] PUT' in captured_log.getvalue()
    response = service.collection._api.response
    assert response.request.method == 'PUT'
    assert 'action' not in response.request.body
    assert 'resource' not in response.request.body
