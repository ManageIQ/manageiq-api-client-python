# -*- coding: utf-8 -*-
import pytest

from httmock import all_requests, HTTMock
from manageiq_client.api import APIException, ManageIQClient


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


NOTFOUND_RESPONSE = {
    "error": {
        "kind": "not_found",
        "message": "Couldn't find Service with 'id'=21",
        "klass": "ActiveRecord::RecordNotFound"
    }
}


@pytest.fixture(scope='module')
def api():
    with HTTMock(api_mock):
        api = ManageIQClient('https://example/api', ('admin', 'admin'), verify_ssl=False)
    return api


@pytest.fixture(scope='module')
def service(api):
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


@all_requests
def notfound_mock(url, request):
    return {'status_code': 404,
            'content': NOTFOUND_RESPONSE}


@all_requests
def interror_mock(url, request):
    return {'status_code': 500,
            'content': ''}


@all_requests
def empty_response_mock(url, request):
    return {'status_code': 200,
            'content': ''}


@all_requests
def invalid_response_mock(url, request):
    return {'status_code': 500,
            'content': 'invalid'}


class TestActionMethods(object):
    def test_actions_present(self, api):
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

    def test_actions_absent(self, api):
        with HTTMock(services_mock), pytest.raises(AttributeError) as excinfo:
            services = api.collections.services
            services.reload()
            getattr(services.action, 'foo')
        assert 'No such action foo' == str(excinfo.value)
        with HTTMock(service_mock), pytest.raises(AttributeError) as excinfo:
            service = api.collections.services[0]
            getattr(service.action, 'foo')
        assert 'No such action foo' == str(excinfo.value)

    def test_methods(self, api):
        with HTTMock(services_mock):
            services = api.collections.services
            services.reload()
            assert services.action.create.POST._method == 'post'
            assert services.action.edit.POST._method == 'post'
            assert services.action.delete.POST._method == 'post'
        with HTTMock(service_mock):
            service = api.collections.services[0]
            assert service.action.edit.PATCH._method == 'patch'
            assert service.action.edit.POST._method == 'post'
            assert service.action.edit.PUT._method == 'put'
            assert service.action.delete.POST._method == 'post'
            assert service.action.delete.DELETE._method == 'delete'

    def test_edit_patch(self, service, captured_log):
        with HTTMock(service_mock):
            outcome = service.action.edit.PATCH({
                "action": "edit",
                "path": "name",
                "value": "new"
            })
            assert outcome.id == service.id
        assert '[RESTAPI] PATCH' in captured_log.getvalue()
        assert service.collection._api.response.request.method == 'PATCH'

    def test_edit_post(self, service, captured_log):
        with HTTMock(service_mock):
            outcome = service.action.edit.POST(name='new')
            assert outcome.id == service.id
        assert '[RESTAPI] POST' in captured_log.getvalue()
        response = service.collection._api.response
        assert response.request.method == 'POST'
        assert 'action' in response.request.body
        assert 'resource' in response.request.body

    def test_edit_put(self, service, captured_log):
        with HTTMock(service_mock):
            outcome = service.action.edit.PUT(name='new')
            assert outcome.id == service.id
        assert '[RESTAPI] PUT' in captured_log.getvalue()
        response = service.collection._api.response
        assert response.request.method == 'PUT'
        assert 'action' not in response.request.body
        assert 'resource' not in response.request.body


class TestFailedResults(object):
    def test_notfound(self, api):
        with HTTMock(notfound_mock), pytest.raises(APIException) as excinfo:
            api.get('https://example/api/services/21')
        assert 'ActiveRecord::RecordNotFound' in str(excinfo.value)
        assert api.response.status_code == 404

    def test_interror(self, service):
        with HTTMock(interror_mock), pytest.raises(APIException) as excinfo:
            service.action.edit.POST(foo='bar')
        assert 'failed with HTTP status 500' in str(excinfo.value)
        assert service.collection._api.response.status_code == 500

    def test_empty_get(self, api):
        with HTTMock(empty_response_mock), pytest.raises(APIException) as excinfo:
            api.get('https://example/api/services/21')
        assert 'JSONDecodeError: empty result' in str(excinfo.value)
        assert api.response.status_code == 200

    def test_invalid_response(self, api):
        with HTTMock(invalid_response_mock), pytest.raises(APIException) as excinfo:
            api.get('https://example/api/services/21')
        assert 'JSONDecodeError: invalid' in str(excinfo.value)
        assert api.response.status_code == 500
