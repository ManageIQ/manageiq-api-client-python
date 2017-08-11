# -*- coding: utf-8 -*-
from manageiq_client.api import Collection, ActionContainer, Action


def test_get_entity_from_href():
    url_base = "http://example.com/api/"
    test_data = [
        # resource url, expected collection name, expected collection href
        ("rates/1/subcol/3r45/?test=/foo/bar", "subcol", "rates/1/subcol"),
        ("service_catalogs/000/", "service_catalogs", "service_catalogs"),
        ("service_catalogs/000/templates/123", "templates", "service_catalogs/000/templates"),
        ("users/0000034", "users", "users"),
        ("collection", "collection", "collection")
    ]

    collection = Collection(None, "{}collection".format(url_base), "collection")
    action_container = ActionContainer(collection)
    action = Action(action_container, "create", "post", "{}collection/123".format(url_base))

    for url, col_name, col_href in test_data:
        col_href = "{}{}".format(url_base, col_href)
        result = {"href": "{}{}".format(url_base, url)}
        entity = action._get_entity_from_href(result)
        assert entity.collection.name == col_name
        assert entity.collection._href == col_href
        assert entity._href == result['href']
