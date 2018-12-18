# -*- coding: utf-8 -*-
# TODO: WIP WIP WIP WIP!
# I got another stage of this library aside, but this is perfectly usable with some restrictions :)
import json
import logging
import re
import requests
import simplejson
import six
import iso8601
from copy import copy
from distutils.version import LooseVersion
from functools import partial
from wait_for import wait_for

from .filters import Q


class APIException(Exception):
    pass


class ManageIQClient(object):
    def __init__(self, entry_point, auth, logger=None, verify_ssl=True, ca_bundle_path=None):
        """ If ca_bundle_path is specified it replaces the system's trusted root CAs"""
        self._entry_point = entry_point
        self._auth = auth
        self._verify_ssl = verify_ssl
        self._ca_bundle_path = ca_bundle_path
        self._session = requests.Session()
        self._session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
        self._build_auth(auth)
        if not verify_ssl:
            self._session.verify = False
        elif ca_bundle_path:
            self._session.verify = ca_bundle_path
        self.logger = logger or logging.getLogger(__name__)
        self.response = None
        self._load_data()

    def _build_auth(self, auth):
        valid = False
        if isinstance(auth, dict):
            if set(("user", "password")) <= set(auth):
                self._session.auth = (auth["user"], auth["password"])
                valid = True
            if "token" in auth:
                self._session.headers.update({'X-Auth-Token': auth['token']})
                valid = True
        elif isinstance(auth, (tuple, list)):  # for backward compatibility
            self._session.auth = tuple(auth[:2])
            valid = True

        if not valid:
            raise ValueError("Unknown values provided for auth")

    def _load_data(self):
        data = self.get(self._entry_point)
        self.collections = CollectionsIndex(self, data.pop("collections", []))
        self._version = data.pop("version", None)
        self._versions = {}
        for version in data.pop("versions", []):
            self._versions[version["name"]] = version["href"]
        for key, value in data.items():
            setattr(self, key, value)

    @property
    def version(self):
        return self._version

    def _result_processor(self, result):
        # Save last full response
        self.response = result

        result_json = None
        try:
            result_json = result.json()
        except simplejson.scanner.JSONDecodeError:
            result_text = result.text.strip()
            # HTTP methods other than GET and OPTIONS are allowed to return empty result
            if result.request.method in ("GET", "OPTIONS") or result_text:
                raise APIException("JSONDecodeError: {}".format(result_text or "empty result"))

        if result_json and "error" in result_json:
            if isinstance(result_json["error"], dict):
                raise APIException(
                    "{}: {}".format(result_json["error"]["klass"], result_json["error"]["message"]))
            else:
                raise APIException(
                    "{}: {}".format(result_json.get("status", None), result_json["error"]))

        # Check HTTP response status
        if not result:
            raise APIException("The request failed with HTTP status {}: {}".format(
                result.status_code, result.reason))

        return result_json

    def _sending_request(self, func, retries=2):
        while retries:
            try:
                return func()
            except requests.ConnectionError as e:
                last_connection_exception = e
                retries -= 1
        raise last_connection_exception

    def get(self, url, **get_params):
        self.logger.info("[RESTAPI] GET %s %r", url, get_params)
        data = self._sending_request(
            partial(self._session.get, url, params=get_params))
        return self._result_processor(data)

    def post(self, url, **payload):
        self.logger.info("[RESTAPI] POST %s %r", url, payload)
        data = self._sending_request(
            partial(self._session.post, url, data=json.dumps(payload)))
        self.logger.info("[RESTAPI] RESPONSE %s", data)
        return self._result_processor(data)

    def put(self, url, **payload):
        self.logger.info("[RESTAPI] PUT %s %r", url, payload)
        data = self._sending_request(
            partial(self._session.put, url, data=json.dumps(payload)))
        self.logger.info("[RESTAPI] RESPONSE %s", data)
        return self._result_processor(data)

    def patch(self, url, *payload):
        self.logger.info("[RESTAPI] PATCH %s %r", url, payload)
        data = self._sending_request(
            partial(self._session.patch, url, data=json.dumps(payload)))
        self.logger.info("[RESTAPI] RESPONSE %s", data)
        return self._result_processor(data)

    def delete(self, url, **payload):
        self.logger.info("[RESTAPI] DELETE %s %r", url, payload)
        data = self._sending_request(
            partial(self._session.delete, url, data=json.dumps(payload)))
        self.logger.info("[RESTAPI] RESPONSE %s", data)
        return self._result_processor(data)

    def options(self, url, **opt_params):
        self.logger.info("[RESTAPI] OPTIONS %s %r", url, opt_params)
        data = self._sending_request(
            partial(self._session.options, url, params=opt_params))
        return self._result_processor(data)

    def get_entity(self, collection_or_name, entity_id, attributes=None):
        if not isinstance(collection_or_name, Collection):
            collection = Collection(
                self, "{}/{}".format(self._entry_point, collection_or_name), collection_or_name)
        else:
            collection = collection_or_name
        entity = Entity(
            collection,
            {"href": "{}/{}".format(collection._href, entity_id)},
            attributes=attributes)
        return entity

    def api_version(self, version):
        return type(self)(
            self._versions[version],
            self._auth,
            logger=self.logger,
            verify_ssl=self._verify_ssl,
            ca_bundle_path=self._ca_bundle_path)

    @property
    def versions(self):
        return sorted(self._versions.keys(), reverse=True, key=LooseVersion)

    @property
    def latest_version(self):
        return self.versions[0]

    @property
    def on_latest_version(self):
        return self.version == self.latest_version


class CollectionsIndex(object):
    def __init__(self, api, data):
        self._api = api
        self._data = data
        self._collections = []
        self._load_data()

    def _load_data(self):
        for collection in self._data:
            c = Collection(
                self._api, collection["href"], collection["name"], collection["description"])
            setattr(self, collection["name"], c)
            self._collections.append(c)

    @property
    def all(self):
        return self._collections

    @property
    def all_names(self):
        return map(lambda c: c.name, self.all)

    def __contains__(self, collection):
        if isinstance(collection, six.string_types):
            return collection in self.all_names
        else:
            return collection in self.all


class SearchResult(object):
    def __init__(self, collection, data):
        self.collection = collection
        self.count = data.pop("count", 0)
        self.subcount = data.pop("subcount", 0)
        self.name = data.pop("name")
        self.resources = []
        for resource in data["resources"]:
            self.resources.append(Entity(collection, resource))

    def __iter__(self):
        for resource in self.resources:
            resource.reload()
            yield resource

    def __getitem__(self, position):
        entity = self.resources[position]
        entity.reload()
        return entity

    def __len__(self):
        return self.subcount

    def __repr__(self):
        return "<SearchResult for {!r}>".format(self.collection)


class Collection(object):
    def __init__(self, api, href, name, description=None):
        self._api = api
        self._href = href
        self._data = None
        self._subcollections = None
        self._subcollections_loaded = False
        self.action = ActionContainer(self)
        self.name = name
        self.description = description

    @property
    def api(self):
        return self._api

    @property
    def subcollections(self):
        # it's enought to try to load the subcollections list once
        if not self._subcollections_loaded:
            self._subcollections_loaded = True
            try:
                opts = self._api.options(self._href)
                self._subcollections = opts['subcollections']
            except Exception:
                # OPTIONS are supported only in new versions of API and subcollections are
                # returned only in even newer versions. Many things can go wrong here,
                # hence this broad except.
                self._subcollections = None
                self._api.logger.warning(
                    "[RESTAPI] failed to get subcollections list for %s", self._href)
        return self._subcollections

    def reload(self, expand=False, attributes=None):
        if expand is True:
            kwargs = {"expand": "resources"}
        elif expand:
            kwargs = {"expand": expand}
        else:
            kwargs = {}
        if attributes is not None:
            if isinstance(attributes, six.string_types):
                attributes = [attributes]
            kwargs.update(attributes=",".join(attributes))
        self._data = self._api.get(self._href, **kwargs)
        self._resources = self._data["resources"]
        self._count = self._data.get("count", 0)
        self._subcount = self._data.get("subcount", 0)
        self._actions = self._data.pop("actions", [])
        if self._data["name"] != self.name:
            raise ValueError("Name mishap!")

    def reload_if_needed(self):
        if self._data is None:
            self.reload()

    def query_string(self, **params):
        """Specify query string to use with the collection.

        Returns: :py:class:`SearchResult`
        """
        return SearchResult(self, self._api.get(self._href, **params))

    def raw_filter(self, filters):
        """Sends all filters to the API.

        No fancy, just a wrapper. Any advanced functionality shall be implemented as another method.

        Args:
            filters: List of filters (strings)

        Returns: :py:class:`SearchResult`
        """
        return SearchResult(self, self._api.get(self._href, **{"filter[]": filters}))

    def filter(self, q):
        """Access the ``filter[]`` functionality of ManageIQ.

        Args:
            q: An instance of :py:class:`filters.Q`

        Returns: :py:class:`SearchResult`
        """
        return self.raw_filter(q.as_filters)

    def find_by(self, **params):
        """Searches in ManageIQ using the ``filter[]`` get parameter.

        This method only supports logical AND so all key/value pairs are considered as equality
        comparision and all are logically anded.
        """
        return self.filter(Q.from_dict(params))

    def get(self, **params):
        try:
            return self.find_by(**params)[0]
        except IndexError:
            raise ValueError("No such '{}' matching query {!r}!".format(self.name, params))

    def options(self, **params):
        return self._api.options(self._href, **params)

    @property
    def count(self):
        self.reload_if_needed()
        return self._count

    @property
    def subcount(self):
        self.reload_if_needed()
        return self._subcount

    @property
    def all(self):
        self.reload(expand=True)
        return [Entity(self, r) for r in self._resources]

    def all_include_attributes(self, attributes):
        """Returns all entities present in the collection with ``attributes`` included."""
        self.reload(expand=True, attributes=attributes)
        entities = [Entity(self, r, attributes=attributes) for r in self._resources]
        self.reload()
        return entities

    def __repr__(self):
        return "<Collection {!r} ({!r})>".format(self.name, self.description)

    def __call__(self, entity_id, attributes=None):
        return self._api.get_entity(self, entity_id, attributes=attributes)

    def __iter__(self):
        self.reload(expand=True)
        for resource in self._resources:
            yield Entity(self, resource)

    def __getitem__(self, position):
        self.reload_if_needed()
        entity = Entity(self, self._resources[position])
        entity.reload()
        return entity

    def __len__(self):
        return self.subcount


class Entity(object):
    # TODO: Extend these fields
    TIME_FIELDS = {
        "updated_on", "created_on", "last_scan_attempt_on", "state_changed_on", "lastlogon",
        "updated_at", "created_at", "last_scan_on", "last_sync_on", "last_refresh_date",
        "retires_on"}
    COLLECTION_MAPPING = dict(
        ems_id="providers",
        storage_id="data_stores",
        zone_id="zones",
        host_id="hosts",
        current_group_id="groups",
        miq_user_role_id="roles",
        evm_owner_id="users",
        task_id="tasks",
    )
    EXTENDED_COLLECTIONS = dict(
        roles={"features"},
    )

    def __init__(self, collection, data, incomplete=False, attributes=None):
        self.collection = collection
        self.action = ActionContainer(self)
        self._data = data
        self._incomplete = incomplete
        self._attributes = attributes
        self._href = None
        self._load_data()

    def _load_data(self):
        if "id" in self._data:  # We have complete data
            self.reload(get=False)
        elif "href" in self._data:  # We have only href
            self._href = self._data["href"]
            # self._data = None
        else:  # Malformed
            raise ValueError("Malformed data: {!r}".format(self._data))

    def reload(self, expand=None, get=True, attributes=None):
        kwargs = {}
        if expand:
            if isinstance(expand, (list, tuple)):
                expand = ",".join(map(str, expand))
            kwargs.update(expand=expand)
        if attributes is None:
            attributes = self._attributes
        if attributes:
            if isinstance(attributes, six.string_types):
                attributes = [attributes]
            kwargs.update(attributes=",".join(attributes))
        if "href" in self._data:
            self._href = self._data["href"]
        if get and self._href:
            new = self.collection._api.get(self._href, **kwargs)
            if self._data is None:
                self._data = new
            else:
                self._data.update(new)
        self._actions = self._data.pop("actions", [])
        for key, value in self._data.items():
            if value is None:
                continue
            if key in self.TIME_FIELDS:
                setattr(self, key, iso8601.parse_date(value))
            elif key in self.COLLECTION_MAPPING.keys():
                setattr(
                    self,
                    re.sub(r"_id$", "", key),
                    self.collection._api.get_entity(self.COLLECTION_MAPPING[key], value)
                )
                setattr(self, key, value)
            elif (isinstance(value, dict) and self._href and
                  "count" in value and "resources" in value):
                href = self._href
                if not href.endswith("/"):
                    href += "/"
                subcol = Collection(self.collection._api, href + key, key)
                setattr(self, key, subcol)
            elif (isinstance(value, list) and self._href and
                  key in self.EXTENDED_COLLECTIONS.get(self.collection.name, set([]))):
                href = self._href
                if not href.endswith("/"):
                    href += "/"
                subcol = Collection(self.collection._api, href + key, key)
                setattr(self, key, subcol)
            else:
                setattr(self, key, value)

    @property
    def exists(self):
        try:
            self.reload()
        except APIException:
            return False
        else:
            return True

    @property
    def subcollections(self):
        return self.collection.subcollections

    def wait_for_existence(self, existence, **kwargs):
        return wait_for(
            lambda: self.exists, fail_condition=not existence, **kwargs)

    def wait_exists(self, **kwargs):
        return self.wait_for_existence(True, **kwargs)

    def wait_not_exists(self, **kwargs):
        return self.wait_for_existence(False, **kwargs)

    def reload_if_needed(self):
        if self._data is None or self._incomplete or not hasattr(self, "_actions"):
            self.reload()
            self._incomplete = False

    def __getattr__(self, attr):
        self.reload()
        if attr in self.__dict__:
            # It got loaded
            return self.__dict__[attr]
        if self.subcollections is not None:
            if attr not in self.subcollections:
                raise AttributeError("No such attribute/subcollection {}".format(attr))
        if not self._href:
            raise AttributeError("Can't get URL of attribute/subcollection {}".format(attr))
        # Try to get subcollection
        href = self._href
        if not href.endswith("/"):
            href += "/"
        subcol = Collection(self.collection._api, href + attr, attr)
        try:
            subcol.reload()
        except APIException:
            raise AttributeError("No such attribute/subcollection {}".format(attr))
        else:
            return subcol

    def __getitem__(self, item):
        # Backward compatibility
        return getattr(self, item)

    def __repr__(self):
        return "<Entity {!r}>".format(self._href if self._href else self._data["id"])

    def _ref_repr(self):
        return {"href": self._href} if self._href else {"id": self._data["id"]}


class ActionContainer(object):
    def __init__(self, obj):
        self._obj = obj

    def reload(self):
        self._obj.reload_if_needed()
        reloaded_actions = []
        for action in self._obj._actions:

            def _add_method(method=None):
                """Adds HTTP method to Action, e.g. ``.delete.POST()``."""
                method = method or action["method"]
                new_name = method.upper()
                base_action_obj = self.__dict__[action["name"]]
                if not hasattr(base_action_obj, new_name):
                    action_obj = base_action_obj if method == base_action_obj._method else Action(
                        self, action["name"], method, action["href"])
                    setattr(base_action_obj, new_name, action_obj)

            # There can be multiple actions with the same name and different HTTP methods
            # (e.g. action "delete" with HTTP methods POST or DELETE).
            # Create action ``.name()`` with default (first) method.
            # For each method, create action ``.name.METHOD()``.
            # E.g. default action ``.delete()`` with method POST and actions
            # ``.delete.POST()`` and ``.delete.DELETE()``.
            if action["name"] not in reloaded_actions:
                reloaded_actions.append(action["name"])
                action_obj = Action(self, action["name"], action["method"], action["href"])
                setattr(self, action["name"], action_obj)
            _add_method()

            # Edit actions on entities can be performed using PATCH and PUT methods as well.
            # These methods are not listed in "actions", therefore adding
            # them explicitly - see https://bugzilla.redhat.com/show_bug.cgi?id=1491336
            if action["name"] == "edit" and isinstance(self._obj, Entity):
                for edit_method in ("patch", "put"):
                    _add_method(method=edit_method)

    def execute_action(self, action_name, *args, **kwargs):
        # To circumvent bad method names, like `import`, you can use this one directly
        action = getattr(self, action_name)
        action_method = kwargs.pop('action_method', None)
        if action_method:
            action = getattr(action, action_method)
        return action(*args, **kwargs)

    @property
    def all(self):
        self.reload()
        return map(lambda a: a["name"], self._obj._actions)

    @property
    def collection(self):
        if isinstance(self._obj, Collection):
            return self._obj
        elif isinstance(self._obj, Entity):
            return self._obj.collection
        else:
            raise ValueError("ActionContainer assigned to wrong object!")

    def __getattr__(self, attr):
        self.reload()
        if attr not in self.__dict__:
            raise AttributeError("No such action {}".format(attr))
        return self.__dict__[attr]

    def __contains__(self, action):
        return action in self.all


class Action(object):
    def __init__(self, container, name, method, href):
        self._container = container
        self._method = method
        self._href = href
        self._name = name

    @property
    def collection(self):
        return self._container.collection

    @property
    def api(self):
        return self.collection.api

    def __call__(self, *args, **kwargs):
        # TODO: for backwards compatibility - can be removed when no longer used
        # possibility to override HTTP method that will be used with the action
        # (e.g. force_method='delete')
        force_method = kwargs.pop('force_method', None)
        if force_method:
            return getattr(self, force_method.upper())(*args, **kwargs)

        if self._method == "post":
            resources = []
            # We got resources to post
            for res in args:
                if isinstance(res, Entity):
                    resources.append(res._ref_repr())
                else:
                    resources.append(res)
            query_dict = {"action": self._name}
            if resources:
                query_dict["resources"] = []
                for resource in resources:
                    new_res = dict(resource)
                    if kwargs:
                        new_res.update(kwargs)
                    query_dict["resources"].append(new_res)
            else:
                if kwargs:
                    query_dict["resource"] = kwargs

            result = self.api.post(self._href, **query_dict)
        elif self._method == "patch":
            result = self.api.patch(self._href, *args)
        elif self._method in ("delete", "put"):
            result = getattr(self.api, self._method)(self._href, **kwargs)
        else:
            raise NotImplementedError
        if result is None:
            return None
        # Make sure that HTTP response from action is not overriden during result processing
        action_response = self.api.response
        try:
            if "results" in result:
                outcome = map(self._process_result, result["results"])
            else:
                outcome = self._process_result(result)
        finally:
            self.api.response = action_response
        return outcome

    def _get_entity_from_href(self, result):
        """Returns entity in correct collection.

        If the "href" value in result doesn't match the current collection,
        try to find the collection that the "href" refers to.
        """
        href_result = result['href']

        if self.collection._href.startswith(href_result):
            return Entity(self.collection, result, incomplete=True)

        href_match = re.match(r"(https?://.+/api[^?]*)/([a-z_-]+)", href_result)
        if not href_match:
            raise ValueError("Malformed href: {}".format(href_result))
        collection_name = href_match.group(2)
        entry_point = href_match.group(1)
        new_collection = Collection(
            self.collection.api,
            "{}/{}".format(entry_point, collection_name),
            collection_name
        )
        return Entity(new_collection, result, incomplete=True)

    def _process_result(self, result):
        if result is None:
            return None
        elif "href" in result:
            return self._get_entity_from_href(result)
        elif "id" in result:
            d = copy(result)
            d["href"] = "{}/{}".format(self.collection._href, result["id"])
            return Entity(self.collection, d, incomplete=True)
        elif "task_href" in result:
            collection = self.api.collections.tasks
            # reuse task_href and task_id, no other data is relevant
            d = {"href": result.get("task_href"), "id": result.get("task_id")}
            return Entity(collection, d, incomplete=True)
        elif "message" in result:
            return result
        else:
            raise NotImplementedError

    def __repr__(self):
        return "<Action {} {}#{}>".format(self._method, self._container._obj._href, self._name)
