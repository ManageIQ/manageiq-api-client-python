# -*- coding: utf-8 -*-
import pytest

from manageiq_client.api import Collection, ActionContainer, Action


url_bases = [
    "https://example.com/api/v2.4.0/",
    "https://example.com/api/",
    "http://127.0.0.1:8080//api",
]

url_variants = [
    # resource url, expected collection name, expected collection href
    ("users/34", "users", "users"),
    ("groups/1/", "groups", "groups"),
    ("service_catalogs/42/templates/123", "templates", "service_catalogs/42/templates"),
    ("col/1/subcol/1r45/?test=/foo/bar", "subcol", "col/1/subcol"),
    ("collection", "collection", "collection"),
]

malformed_urls = [
    "https://example.com/col/123",
    "example.com/api/col/subcol/0001",
    "api/col/subcol/0001",
]


@pytest.fixture(scope="function")
def action(url_base):
    collection = Collection(None, "{}/collection".format(url_base), "collection")
    action_container = ActionContainer(collection)
    return Action(action_container, "create", "post", "{}/collection/123".format(url_base))


@pytest.mark.parametrize("test_data", url_variants, ids=[variant[0] for variant in url_variants])
@pytest.mark.parametrize(
    "url_base", url_bases, ids=["addr{}".format(idx) for idx, __ in enumerate(url_bases)])
def test_get_entity_from_href(url_base, test_data, action):
    url, col_name, col_href = test_data
    col_href = "{}/{}".format(url_base, col_href)
    result = {"href": "{}/{}".format(url_base, url)}
    entity = action._get_entity_from_href(result)
    assert entity.collection.name == col_name
    assert entity.collection._href == col_href
    assert entity._href == result["href"]


@pytest.mark.parametrize("test_data", malformed_urls)
@pytest.mark.parametrize("url_base", ("https://example.com/api",), ids=['addr0'])
def test_malformed_href(test_data, action):
    result = {"href": test_data}
    with pytest.raises(ValueError):
        action._get_entity_from_href(result)
