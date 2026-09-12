import datetime
import json
import re
import unittest
from typing import Optional
from unittest import mock

from app.interfaces import base
from basyx.aas import model
from basyx.aas.adapter._generic import XML_NS_MAP
from lxml import etree
from werkzeug.exceptions import BadRequest


class TestPagination(unittest.TestCase):
    """
    Testing of the shared pagination strategy, shared by multiple endpoints.
    """

    __test__ = True

    @staticmethod
    def _build_request(limit: Optional[str] = None, cursor: Optional[str] = None):
        request = mock.Mock()
        def mock_get(key, default = None):
            if key == "limit":
                return limit or default
            elif key == "cursor":
                return cursor or default
            else:
                return default
        request.args.get.side_effect = mock_get
        return request

    def test_pagination_on_empty_set(self):
        page, metadata = base.BaseWSGIApp._get_slice(self._build_request('3'), [])
        self.assertEqual(0, len(list(page)))
        if not metadata:
            self.fail("no metadata")
        self.assertIsNone(metadata.cursor)

    def test_pagination_with_one_page(self):
        page, metadata = base.BaseWSGIApp._get_slice(self._build_request("3"), [1, 2])
        self.assertEqual([1, 2], list(page))
        if not metadata:
            self.fail("no metadata")
        self.assertIsNone(metadata.cursor)

    def test_pagination_walks_all_items(self):
        all_objects = [i for i in range(20)]

        pages: list[list] = []
        cursor = None
        for _ in range(1000):
            page, metadata = base.BaseWSGIApp._get_slice(self._build_request('6', cursor), all_objects)
            result = list(page)
            pages.append(result)
            if not metadata:
                self.fail("no paging_metadata returned")
            cursor = metadata.cursor
            if cursor is None:
                break
            if len(pages) > 4 or len(pages) < 1:
                self.fail("cursor never signalled end")

        self.assertEqual([6, 6, 6, 2], [len(page) for page in pages])
        seen = [i for page in pages for i in page]
        self.assertEqual(len(seen), len(set(seen)), "an item was returned on more than one page")
        self.assertEqual(set(range(20)), set(seen))

    def test_pagination_requires_positive_limit(self):
        with self.assertRaises(BadRequest):
            base.BaseWSGIApp._get_slice(self._build_request('-1'), [])

    def test_pagination_requires_positive_cursor(self):
        with self.assertRaises(BadRequest):
            base.BaseWSGIApp._get_slice(self._build_request('5', '-1'), [])


class TestJsonResponse(unittest.TestCase):

    __test__ = True

    def test_empty_response(self):
        response = base.JsonResponse(None)
        self.assertEqual(204, response.status_code)
        self.assertEqual(0, len(response.get_data()))

    def test_example_single_object(self):
        response = base.JsonResponse(model.Submodel(id_="https://example.org/Example_Submodel"))

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))
        if not isinstance(parsed_body, dict):
            self.fail("Response is no JSON object")
        self.assertEqual("Submodel", parsed_body["modelType"])
        self.assertEqual("https://example.org/Example_Submodel", parsed_body["id"])

    def test_example_list(self):
        response = base.JsonResponse([
            model.Submodel(id_="https://example.org/Example_Submodel"),
            model.Submodel(id_="https://example.org/Second_Submodel")
        ])

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))
        if not isinstance(parsed_body, list):
            self.fail("Response is no JSON list")
        ids = [sm["id"] for sm in parsed_body]
        self.assertEqual(2, len(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_example_empty_list(self):
        response = base.JsonResponse([])

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))

        if not isinstance(parsed_body, list):
            self.fail("Response is no JSON list")
        self.assertEqual(0, len(parsed_body))

    def test_paging_metadata(self):
        response = base.JsonResponse(
            obj=[model.Submodel(id_="https://example.org/Example_Submodel")],
            paging_metadata=base.PagingMetadata(cursor="asdf")
        )

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))
        if not isinstance(parsed_body, dict):
            self.fail("Response is no JSON object")
        self.assertEqual("asdf", parsed_body["paging_metadata"]["cursor"])
        if not isinstance(parsed_body["result"], list):
            self.fail("Result part contains no list")
        self.assertEqual("https://example.org/Example_Submodel", parsed_body["result"][0]["id"])

    def test_paging_metadata_no_cursor(self):
        response = base.JsonResponse(
            obj=[model.Submodel(id_="https://example.org/Example_Submodel")],
            paging_metadata=base.PagingMetadata(cursor=None),
        )

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))
        if not isinstance(parsed_body, dict):
            self.fail("Response is no JSON object")
        self.assertIn("paging_metadata", parsed_body)
        self.assertNotIn("cursor", parsed_body["paging_metadata"])

    def test_result(self):
        response = base.JsonResponse(
            base.Result(False, [
                base.Message("BAD_CODE", "test", base.MessageType.ERROR, datetime.datetime.now())
            ])
        )

        self.assertEqual("application/json", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = json.loads(response.get_data(as_text=True))
        if not isinstance(parsed_body, dict):
            self.fail("Response is no JSON object")
        self.assertFalse(parsed_body["success"])
        if not isinstance(parsed_body["messages"], list):
            self.fail("messages is no list")
        message = parsed_body["messages"][0]
        self.assertEqual("BAD_CODE", message["code"])
        self.assertEqual("test", message["text"])
        self.assertEqual("Error", message["messageType"])
        isodatetime = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}$")
        self.assertIsNotNone(isodatetime.match(message["timestamp"]))

class TestXmlResponse(unittest.TestCase):
    __test__ = True

    def test_empty_response(self):
        response = base.XmlResponse(None)
        self.assertEqual(204, response.status_code)
        self.assertEqual(0, len(response.get_data()))

    def test_example_single_object(self):
        response = base.XmlResponse(model.Submodel(id_="https://example.org/Example_Submodel"))

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        returned_id = parsed_body.findtext("aas:id", namespaces=XML_NS_MAP)
        self.assertEqual("https://example.org/Example_Submodel", returned_id)

    def test_example_list(self):
        response = base.XmlResponse(
            [
                model.Submodel(id_="https://example.org/Example_Submodel"),
                model.Submodel(id_="https://example.org/Second_Submodel"),
            ]
        )

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        ids = [elem.text for elem in parsed_body.findall("aas:submodel/aas:id", namespaces=XML_NS_MAP)]
        self.assertEqual(2, len(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_example_empty_list(self):
        response = base.XmlResponse([])

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        self.assertEqual(0, len(list(parsed_body.iterchildren())))

    def test_paging_metadata(self):
        response = base.XmlResponse(
            obj=[model.Submodel(id_="https://example.org/Example_Submodel")],
            paging_metadata=base.PagingMetadata(cursor="asdf"),
        )

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        self.assertEqual("asdf", parsed_body.get("cursor"))
        ids = [elem.text for elem in parsed_body.findall("aas:submodel/aas:id", namespaces=XML_NS_MAP)]
        self.assertEqual(["https://example.org/Example_Submodel"], ids)

    def test_paging_metadata_no_cursor(self):
        response = base.XmlResponse(
            obj=[model.Submodel(id_="https://example.org/Example_Submodel")],
            paging_metadata=None,
        )

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        self.assertIsNone(parsed_body.get("cursor"))

    def test_result(self):
        response = base.XmlResponse(
            base.Result(False, [base.Message("BAD_CODE", "test", base.MessageType.ERROR, datetime.datetime.now())])
        )

        self.assertEqual("application/xml", response.content_type)
        self.assertEqual(200, response.status_code)
        parsed_body = etree.fromstring(response.get_data())

        self.assertEqual("response", parsed_body.tag)
        self.assertEqual("false", parsed_body.findtext("success"))

        messages = parsed_body.findall("messages/message")
        self.assertEqual(1, len(messages))
        self.assertEqual("BAD_CODE", messages[0].findtext("code"))
        self.assertEqual("test", messages[0].findtext("text"))
        self.assertEqual("Error", messages[0].findtext("messageType"))
        isodatetime = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}$")
        self.assertIsNotNone(isodatetime.match(messages[0].findtext("timestamp") or ""))
