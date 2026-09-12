"""
Endpoint tests for :class:`~app.interfaces.discovery.DiscoveryAPI`.

The routes follow the *Discovery Service Specification* (SSP-001, "full" profile) from ``aas-specs-api``.
Where this server deviates from the spec's documented status codes, the test asserts the *implemented*
behavior and the deviation is called out in a comment.

Requests and responses go through the shared :class:`~..format_utils.JsonFormatClient` (as in
``test/interfaces/repository/test_shells.py``). Only ``GET /lookup/shells/{aasIdentifier}`` returns
AAS model objects (``SpecificAssetId``), so it is additionally run against the XML
:class:`~..format_utils.FormatClient`; every other route returns plain strings / JSON objects that the
SDK XML serializer cannot render, so those are JSON only.
"""

import json
import os
import unittest
from typing import List, Tuple

from app.interfaces.discovery import DiscoveryAPI, DiscoveryStore
from app.util.converters import base64url_encode
from basyx.aas.model import SpecificAssetId
from werkzeug.test import Client, TestResponse

from .format_utils import FormatClient, JsonFormatClient, inject_format_clients, with_json_client, with_xml_client


def _b64url_json(payload: object) -> str:
    return base64url_encode(json.dumps(payload))


class DiscoveryEndpointTestBase(unittest.TestCase):
    __test__ = False

    AAS_ID = "https://example.org/aas/1"
    AAS_ID_2 = "https://example.org/aas/2"
    UNKNOWN_ID = "https://example.org/unknown"

    store: DiscoveryStore
    discovery_server: DiscoveryAPI
    client: Client
    format_client: JsonFormatClient

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.store = DiscoveryStore()
        cls.discovery_server = DiscoveryAPI(cls.store, base_path="")
        cls.client = Client(cls.discovery_server)
        cls.format_client = JsonFormatClient(cls.client)

    def setUp(self) -> None:
        self.store.aas_id_to_asset_ids.clear()
        self.store.asset_id_to_aas_ids.clear()

    # ------------------------------------------------------------------ helpers

    def register(self, aas_id: str, asset_ids: List[Tuple[str, str]]) -> None:
        assets: list[SpecificAssetId] = [SpecificAssetId(name, value) for name, value in asset_ids]
        self.store.add_specific_asset_ids_to_aas(aas_id, assets)
        for asset in assets:
            self.store._add_aas_id_to_specific_asset_id(asset, aas_id)

    def assert_ok(self, response: TestResponse) -> None:
        self.assertEqual(200, response.status_code, msg=response.get_data(as_text=True))

    def assert_error(self, response: TestResponse, status_code: int) -> None:
        self.assertEqual(status_code, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn("success", response.get_data(as_text=True), msg=response.get_data(as_text=True))


# ====================================================================== /description


class DiscoveryServiceDescriptionTest(DiscoveryEndpointTestBase):
    __test__ = True

    def test_description_ok(self) -> None:
        response = self.format_client.get("/description")

        self.assert_ok(response)
        profiles = self.format_client.parse_object(response)["profiles"]
        self.assertIn("https://admin-shell.io/aas/API/3/1/DiscoveryServiceSpecification/SSP-001", profiles)
        self.assertIn("https://admin-shell.io/aas/API/3/1/DiscoveryServiceSpecification/SSP-002", profiles)


# ====================================================================== POST /lookup/shellsByAssetLink


class SearchShellsByAssetLinkEndpointTest(DiscoveryEndpointTestBase):
    __test__ = True

    def test_search_match(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.post("/lookup/shellsByAssetLink", obj=[{"name": "serial", "value": "123"}])

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID], self.format_client.parse_collection(response))

    def test_search_no_match_returns_empty(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.post(
            "/lookup/shellsByAssetLink", obj=[{"name": "serial", "value": "does-not-exist"}]
        )

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    def test_search_empty_body_returns_empty(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.post("/lookup/shellsByAssetLink", obj=[])

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    def test_search_multiple_links_unions_results(self) -> None:
        self.register(self.AAS_ID, [("serial", "1")])
        self.register(self.AAS_ID_2, [("serial", "2")])

        response = self.format_client.post(
            "/lookup/shellsByAssetLink",
            obj=[{"name": "serial", "value": "1"}, {"name": "serial", "value": "2"}],
        )

        self.assert_ok(response)
        self.assertEqual({self.AAS_ID, self.AAS_ID_2}, set(self.format_client.parse_collection(response)))

    def test_search_supports_pagination(self) -> None:
        self.register(self.AAS_ID, [("serial", "1")])
        self.register(self.AAS_ID_2, [("serial", "1")])

        response = self.format_client.post("/lookup/shellsByAssetLink?limit=1", obj=[{"name": "serial", "value": "1"}])

        self.assert_ok(response)
        self.assertEqual(1, len(self.format_client.parse_collection(response)))
        self.assertIsNotNone(self.format_client.next_cursor(response))

    def test_search_malformed_json_returns_400(self) -> None:
        response = self.format_client.post(
            "/lookup/shellsByAssetLink", data=b"{not json", content_type="application/json"
        )

        self.assert_error(response, 400)

    def test_search_asset_link_missing_value_returns_400(self) -> None:
        self.assert_error(self.format_client.post("/lookup/shellsByAssetLink", obj=[{"name": "serial"}]), 400)


# ====================================================================== GET /lookup/shells (deprecated)


class GetShellsByAssetLinkQueryEndpointTest(DiscoveryEndpointTestBase):
    """The deprecated ``GET /lookup/shells?assetIds=...`` route (kept for BaSyx UI interoperability)."""

    __test__ = True

    def test_query_match(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.get(f"/lookup/shells?assetIds={_b64url_json({'name': 'serial', 'value': '123'})}")

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID], self.format_client.parse_collection(response))

    def test_query_accepts_list_payload(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.get(
            f"/lookup/shells?assetIds={_b64url_json([{'name': 'serial', 'value': '123'}])}"
        )

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID], self.format_client.parse_collection(response))

    def test_query_missing_parameter_returns_400(self) -> None:
        self.assert_error(self.format_client.get("/lookup/shells"), 400)

    def test_query_invalid_base64_returns_400(self) -> None:
        self.assert_error(self.format_client.get("/lookup/shells?assetIds=not-base64!!!"), 400)

    def test_query_decoded_value_not_json_returns_400(self) -> None:
        self.assert_error(self.format_client.get(f"/lookup/shells?assetIds={base64url_encode('not json')}"), 400)

    def test_query_payload_not_object_or_list_returns_400(self) -> None:
        self.assert_error(self.format_client.get(f"/lookup/shells?assetIds={_b64url_json(123)}"), 400)

    def test_query_payload_item_not_object_returns_400(self) -> None:
        self.assert_error(self.format_client.get(f"/lookup/shells?assetIds={_b64url_json([1, 2])}"), 400)


# ====================================================================== /lookup/shells/{aasIdentifier}


@inject_format_clients
class AssetLinksByIdEndpointTest(DiscoveryEndpointTestBase):
    """Tests for GET/POST/DELETE on ``/lookup/shells/{aasIdentifier}``."""

    __test__ = True

    # ------------------------------------------------------------------ GET (returns SpecificAssetId objects)

    @with_json_client
    @with_xml_client
    def test_get_returns_stored_asset_ids(self, format_client: FormatClient) -> None:
        self.register(self.AAS_ID, [("serial", "123"), ("globalAssetId", "https://example.org/asset/1")])

        response = format_client.get(f"/lookup/shells/{base64url_encode(self.AAS_ID)}")

        self.assertEqual(200, response.status_code, msg=response.get_data(as_text=True))
        pairs = {
            (format_client.field(node, "name"), format_client.field(node, "value"))
            for node in format_client.parse_collection(response)
        }
        self.assertEqual({("serial", "123"), ("globalAssetId", "https://example.org/asset/1")}, pairs)

    @with_json_client
    @with_xml_client
    def test_get_unknown_aas_returns_empty(self, format_client: FormatClient) -> None:
        # Spec allows 404 here; this server returns 200 with an empty collection instead.
        response = format_client.get(f"/lookup/shells/{base64url_encode(self.UNKNOWN_ID)}")

        self.assertEqual(200, response.status_code, msg=response.get_data(as_text=True))
        self.assertEqual([], format_client.parse_collection(response))

    # ------------------------------------------------------------------ POST

    def test_post_creates_asset_links(self) -> None:
        response = self.format_client.post(
            f"/lookup/shells/{base64url_encode(self.AAS_ID)}",
            obj=[{"name": "serial", "value": "123"}],
        )

        # Spec documents 201 for creation; this server responds 200 with the updated mapping.
        self.assert_ok(response)
        body = self.format_client.parse_object(response)
        self.assertEqual([("serial", "123")], [(a["name"], a["value"]) for a in body[self.AAS_ID]])
        self.assertEqual(
            [self.AAS_ID],
            self.format_client.parse_collection(
                self.format_client.post("/lookup/shellsByAssetLink", obj=[{"name": "serial", "value": "123"}])
            ),
        )

    def test_post_accepts_single_object_body(self) -> None:
        response = self.format_client.post(
            f"/lookup/shells/{base64url_encode(self.AAS_ID)}", obj={"name": "serial", "value": "123"}
        )

        self.assert_ok(response)
        self.assertEqual(
            [("serial", "123")],
            [(a["name"], a["value"]) for a in self.format_client.parse_object(response)[self.AAS_ID]],
        )

    def test_post_is_additive(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.post(
            f"/lookup/shells/{base64url_encode(self.AAS_ID)}", obj=[{"name": "batch", "value": "xyz"}]
        )

        self.assert_ok(response)
        stored = {(a["name"], a["value"]) for a in self.format_client.parse_object(response)[self.AAS_ID]}
        self.assertEqual({("serial", "123"), ("batch", "xyz")}, stored)

    def test_post_malformed_json_returns_400(self) -> None:
        response = self.format_client.post(
            f"/lookup/shells/{base64url_encode(self.AAS_ID)}", data=b"{not json", content_type="application/json"
        )

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ DELETE

    def test_delete_removes_asset_links(self) -> None:
        self.register(self.AAS_ID, [("serial", "123")])

        response = self.format_client.delete(f"/lookup/shells/{base64url_encode(self.AAS_ID)}")

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        self.assertEqual(
            [],
            self.format_client.parse_object(self.format_client.get(f"/lookup/shells/{base64url_encode(self.AAS_ID)}")),
        )
        self.assertEqual(
            [],
            self.format_client.parse_collection(
                self.format_client.post("/lookup/shellsByAssetLink", obj=[{"name": "serial", "value": "123"}])
            ),
        )

    def test_delete_unknown_aas_returns_204(self) -> None:
        # Spec allows 404 here; this server always returns 204.
        response = self.format_client.delete(f"/lookup/shells/{base64url_encode(self.UNKNOWN_ID)}")

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))


# ====================================================================== DiscoveryStore.from_file()/to_file()


class DiscoveryStorePersistenceTest(unittest.TestCase):
    STORE_FILE = os.path.join(os.path.dirname(__file__), "discovery_store_persistence_test.json")

    def tearDown(self) -> None:
        for path in (self.STORE_FILE, f"{self.STORE_FILE}.tmp"):
            if os.path.exists(path):
                os.remove(path)

    def test_roundtrip_rebuilds_reverse_index(self) -> None:
        store = DiscoveryStore()
        asset_1 = SpecificAssetId("globalAssetId", "urn:asset:1")
        asset_2 = SpecificAssetId("serialNumber", "SN-42")
        asset_3 = SpecificAssetId("globalAssetId", "urn:asset:1")  # shared by both AAS
        store.add_specific_asset_ids_to_aas("https://example.org/aas/1", [asset_1, asset_2])
        store.add_specific_asset_ids_to_aas("https://example.org/aas/2", [asset_3])
        store.to_file(self.STORE_FILE)

        loaded = DiscoveryStore.from_file(self.STORE_FILE)

        self.assertEqual(store.aas_id_to_asset_ids, loaded.aas_id_to_asset_ids)
        self.assertEqual(
            {"https://example.org/aas/1", "https://example.org/aas/2"},
            loaded.asset_id_to_aas_ids[asset_1],
        )
        self.assertEqual({"https://example.org/aas/1"}, loaded.asset_id_to_aas_ids[asset_2])

    def test_roundtrip_empty_store(self) -> None:
        store = DiscoveryStore()
        store.to_file(self.STORE_FILE)

        loaded = DiscoveryStore.from_file(self.STORE_FILE)

        self.assertEqual({}, loaded.aas_id_to_asset_ids)
        self.assertEqual({}, loaded.asset_id_to_aas_ids)

    def test_to_file_does_not_leave_temp_file_behind(self) -> None:
        store = DiscoveryStore()
        store.add_specific_asset_ids_to_aas(
            "https://example.org/aas/1", [SpecificAssetId("globalAssetId", "urn:asset:1")]
        )

        store.to_file(self.STORE_FILE)

        self.assertTrue(os.path.exists(self.STORE_FILE))
        self.assertFalse(os.path.exists(f"{self.STORE_FILE}.tmp"))
