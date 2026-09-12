import abc
import json
from typing import Any, Callable, Optional

import app.adapter
from basyx.aas import adapter
from basyx.aas.adapter._generic import XML_NS_MAP
from lxml import etree
from werkzeug.test import Client, TestResponse


class FormatClient(abc.ABC):
    """
    Wraps a :class:`werkzeug.test.Client` and hides the request/response *format* (JSON or XML) behind a small,
    format-agnostic API, so an endpoint test can be written once and run against every format.

    * request helpers (:meth:`get` / :meth:`post` / ...) inject the ``Accept`` / ``Content-Type`` headers and
      serialize model objects passed as ``obj`` with :meth:`serialize`,
    * parsing helpers (:meth:`parse_object` / :meth:`parse_collection` / :meth:`identifier` / ...) turn a response
      body into plain Python values that are identical for both formats.
    """

    content_type: str

    def __init__(self, client: Client):
        self.client = client

    def request(self, method: str, path: str, obj: Optional[object] = None, data: Any = None, **kwargs) -> TestResponse:
        """
        Issue a request, setting the ``Accept`` header to the class' :attr:`content_type`.

        :param method: HTTP method to perform the request with
        :param path: path to perform the request to
        :param obj: If given, the object is parsed to :attr:`content_type` using :meth:`serialize` and sent as body.
        :param data: If given, this is directly sent as body. Caution: gets overridden by :param:`obj`
        :param kwargs: Additional arguments passed directly to :meth:`werkzeug.test.Client.open`. Can be used to set
                        different ``Content-Type`` for :param:`data`.
        :return: The :class:`~werkzeug.test.TestResponse` object
        """
        headers = dict(kwargs.get("headers", {}))
        headers["Accept"] = self.content_type

        if obj is not None:
            data = self.serialize(obj)
            kwargs["content_type"] = self.content_type

        kwargs.update({"data": data, "headers": headers})

        return self.client.open(
            path, method=method, **kwargs
        )

    def get(self, path: str, **kwargs) -> TestResponse:
        return self.request("GET", path, **kwargs)

    def get_paginated(self, path: str, limit: int, max_pages:int, **kwargs) -> list[list[Any]]:
        """
        Iteratively query the paginated endpoint :param:`path` with the given :param:`limit` until
        the server indicates the complete collection was read.

        :param path: path to perform the request to.
        :param limit: the limit for the paginated request, controls maximum size of each page.
        :param max_pages: request fails if more than these pages are returned by endpoint.
        :param kwargs: additional arguments to pass to the query.
        :return: list of returned pages, each page is a list as returned by :meth:`parse_collection`.
        """
        pages: list[list[str]] = []
        cursor: str | None = None
        while True:
            start_or_and = "?" if "?" not in path else "&"
            query = f"{path}{start_or_and}limit={limit}"
            if cursor is not None:
                query += f"&cursor={cursor}"
            response = self.get(query, **kwargs)
            assert 200 == response.status_code
            page_content = self.parse_collection(response)
            assert limit >= len(page_content), "paginated result contains more than limit items"
            pages.append(page_content)
            cursor = self.next_cursor(response)
            if cursor is None:
                break
            assert len(pages) <= max_pages, "cursor never signalled the last page"

        return pages

    def post(self, path: str, obj: Optional[object] = None, **kwargs: Any) -> TestResponse:
        return self.request("POST", path, obj=obj, **kwargs)

    def put(self, path: str, obj: Optional[object] = None, **kwargs: Any) -> TestResponse:
        return self.request("PUT", path, obj=obj, **kwargs)

    def patch(self, path: str, obj: Optional[object] = None, **kwargs: Any) -> TestResponse:
        return self.request("PATCH", path, obj=obj, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> TestResponse:
        return self.request("DELETE", path, **kwargs)

    # ------------------------------------------------------------------ format-specific hooks

    @abc.abstractmethod
    def serialize(self, obj: object) -> bytes:
        """Serialize a model object to a request body in the format under test."""

    @abc.abstractmethod
    def parse_object(self, response: TestResponse) -> Any:
        """Return the single-object node of an object response (accepted by :meth:`identifier`, :meth:`field`, ...)."""

    @abc.abstractmethod
    def parse_collection(self, response: TestResponse) -> list[Any]:
        """Return the list of item nodes of a collection response, in document order."""

    @abc.abstractmethod
    def identifier(self, node: Any) -> str:
        """The ``id`` of an Identifiable from a :meth:`parse_object` / :meth:`parse_collection` node."""

    @abc.abstractmethod
    def reference_target(self, node: Any) -> str:
        """The value of the last key of a Reference node (a single-reference response or a collection item)."""

    @abc.abstractmethod
    def field(self, node: Any, name: str) -> Optional[str]:
        """The text of a direct scalar child ``name`` of ``node`` (JSON member / ``aas:``-prefixed XML element)."""

    @abc.abstractmethod
    def result_success(self, response: TestResponse) -> bool:
        """The value of the ``success`` flag in a ``Result`` body."""

    @abc.abstractmethod
    def next_cursor(self, response: TestResponse) -> Optional[str]:
        """The paging cursor pointing at the next page, or ``None`` once the last page has been returned."""


class JsonFormatClient(FormatClient):
    content_type = "application/json"

    def serialize(self, obj: object) -> bytes:
        return json.dumps(obj, cls=app.adapter.jsonization.ServerAASToJsonEncoder).encode("utf-8")

    def _payload(self, response: TestResponse) -> Any:
        return json.loads(response.get_data(as_text=True))

    def parse_object(self, response: TestResponse) -> Any:
        return self._payload(response)

    def parse_collection(self, response: TestResponse) -> list[Any]:
        payload = self._payload(response)
        if isinstance(payload, dict) and "result" in payload:
            return list(payload["result"])
        return list(payload)

    def identifier(self, node: Any) -> str:
        return node["id"]

    def reference_target(self, node: Any) -> str:
        return node["keys"][-1]["value"]

    def field(self, node: Any, name: str) -> Optional[str]:
        return node.get(name)

    def result_success(self, response: TestResponse) -> bool:
        body = self._payload(response)
        return "success" not in body or bool(body["success"])

    def next_cursor(self, response: TestResponse) -> Optional[str]:
        payload = self._payload(response)
        if isinstance(payload, dict):
            return payload.get("paging_metadata", {}).get("cursor")
        return None


class XmlFormatClient(FormatClient):
    content_type = "application/xml"

    def serialize(self, obj: object) -> bytes:
        item_elem = adapter.xml.object_to_xml_element(obj)
        etree.cleanup_namespaces(item_elem, top_nsmap=XML_NS_MAP)
        return etree.tostring(item_elem, xml_declaration=True, encoding="utf-8")

    def _root(self, response: TestResponse) -> etree._Element:
        return etree.fromstring(response.data)

    def parse_object(self, response: TestResponse) -> Any:
        # An object response is <response> with the object's children hoisted onto it, so the root itself is the
        # object node and `identifier` / `field` find e.g. <aas:id> directly beneath it.
        return self._root(response)

    def parse_collection(self, response: TestResponse) -> list[Any]:
        # A collection response is <response> with one child element per item.
        return list(self._root(response))

    def identifier(self, node: Any) -> str:
        found = node.findtext("aas:id", namespaces=XML_NS_MAP)
        assert found is not None
        return found

    def reference_target(self, node: Any) -> str:
        values = node.findall(".//aas:key/aas:value", namespaces=XML_NS_MAP)
        assert values, "no keys in reference node"
        return values[-1].text

    def field(self, node: Any, name: str) -> Optional[str]:
        return node.findtext(f"aas:{name}", namespaces=XML_NS_MAP)

    def result_success(self, response: TestResponse) -> bool:
        # <response><success>true|false</success>...</response> -- not namespaced in Result bodies.
        success_elem = self._root(response).find("success")
        return success_elem is None or success_elem.text == "true"

    def next_cursor(self, response: TestResponse) -> Optional[str]:
        # The cursor is an attribute on the <response> root; it is unconditionally serialized, so a
        # missing next page shows up as the literal string "None" rather than an absent attribute.
        cursor = self._root(response).get("cursor")
        return cursor if cursor not in (None, "None") else None


def with_json_client(func):
    client_types = getattr(func, "_client_types", [])
    client_types.append(("json", JsonFormatClient))
    func._client_types = client_types
    return func

def with_xml_client(func):
    client_types = getattr(func, "_client_types", [])
    client_types.append(("xml", XmlFormatClient))
    func._client_types = client_types
    return func

def with_custom_client(name: str, client_type: type[FormatClient]):
    def wrapper(func):
        client_types = getattr(func, "_client_types", [])
        client_types.append((name, client_type))
        func._client_types = client_types
        return func
    return wrapper

def inject_format_clients(cls):
    """Decorator to use on :class:`unittest.TestCase` when decorating functions with
    :meth:`with_json_client`, :meth:`with_xml_client` or :meth:`with_custom_client`. For each
    :class:`FormatClient` that is defined via these decorators on a function, a new function is
    added to the class. The new function gets the specfied :class:`FormatcClient` injected as second
    parameter. The name of the new function gets the format name as suffix.
    """

    def build_test(method: Callable[[Any, FormatClient], Any], format_client_type: type[FormatClient]):
        def wrapper(self):
            formatted_client = format_client_type(getattr(cls, "client"))
            return method(self, formatted_client)
        return wrapper

    for name, method in list(vars(cls).items()):
        method_client_type: Optional[list[str]] = getattr(method, "_client_types", None)
        if method_client_type is None:
            continue

        # Method was decorated -> remove original method and insert new methods
        delattr(cls, name)
        for (format_name, format_client_type) in method_client_type:
            setattr(cls, f"{name}_{format_name}", build_test(method, format_client_type))
    return cls
