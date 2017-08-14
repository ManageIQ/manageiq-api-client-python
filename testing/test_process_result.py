# -*- coding: utf-8 -*-
import pytest

from manageiq_client.api import Collection, ActionContainer, Action


url_variants = [
    # resource url, expected collection name, expected collection href
    ("users/34", "users", "users"),
    ("groups/1/", "groups", "groups"),
    ("service_catalogs/42/templates/123", "templates", "service_catalogs/42/templates"),
    ("col/1/subcol/1r45/?test=/foo/bar", "subcol", "col/1/subcol"),
    ("collection", "collection", "collection"),
]


@pytest.mark.parametrize('test_data', url_variants, ids=[variant[0] for variant in url_variants])
def test_get_entity_from_href(test_data):
    url_base = "http://example.com/api/"

    collection = Collection(None, "{}collection".format(url_base), "collection")
    action_container = ActionContainer(collection)
    action = Action(action_container, "create", "post", "{}collection/123".format(url_base))

    url, col_name, col_href = test_data
    col_href = "{}{}".format(url_base, col_href)
    result = {"href": "{}{}".format(url_base, url)}
    entity = action._get_entity_from_href(result)
    assert entity.collection.name == col_name
    assert entity.collection._href == col_href
    assert entity._href == result['href']
