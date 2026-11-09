# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import json
import unittest

from app._config import API_BASE_PATH as BASE_PATH
from app.interfaces.repository import WSGIApp
from basyx.aas import model
from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.examples.data.example_aas import create_full_example
from werkzeug.test import Client


def _encode_asset_id(name: str, value: str) -> str:
    payload = json.dumps({"name": name, "value": value})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _result_ids(response) -> list:
    return [shell["id"] for shell in json.loads(response.data)["result"]]


class ShellsAssetIdsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.example_data = create_full_example()
        app = WSGIApp(self.example_data, DictSupplementaryFileContainer())
        self.client = Client(app)

    def test_multiple_global_asset_ids_returns_matching_results(self) -> None:
        aas_list = [obj for obj in self.example_data if isinstance(obj, model.AssetAdministrationShell)]
        known_id = aas_list[0].asset_information.global_asset_id
        assert known_id is not None
        unknown_id = "http://example.org/nonexistent_asset"
        id1 = _encode_asset_id("globalAssetId", known_id)
        id2 = _encode_asset_id("globalAssetId", unknown_id)
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={id1}&assetIds={id2}")
        self.assertEqual(200, response.status_code)
        returned_ids = _result_ids(response)
        self.assertIn(aas_list[0].id, returned_ids)

    def test_malformed_asset_id_missing_field_returns_400(self) -> None:
        bad_payload = base64.urlsafe_b64encode(b'{"name": "globalAssetId"}').decode()
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={bad_payload}")
        self.assertEqual(400, response.status_code)

    def test_spec_specific_asset_id_without_match_returns_empty(self) -> None:
        # AAS Part 2, v3.1.1: each assetIds value is a base64url-encoded SpecificAssetId.
        # A query for an id no shell carries must return an empty result, not all shells.
        spec_id = _encode_asset_id("serialNumber", "does-not-exist")
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={spec_id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual([], _result_ids(response))

    def test_spec_specific_asset_id_with_match_returns_shell(self) -> None:
        aas_list = [obj for obj in self.example_data if isinstance(obj, model.AssetAdministrationShell)]
        known_specific_id = next(iter(aas_list[0].asset_information.specific_asset_id))
        spec_id = _encode_asset_id(known_specific_id.name, known_specific_id.value)
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={spec_id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual([aas_list[0].id], _result_ids(response))

    def test_spec_specific_asset_ids_all_must_match(self) -> None:
        aas_list = [obj for obj in self.example_data if isinstance(obj, model.AssetAdministrationShell)]
        known_specific_id = next(iter(aas_list[0].asset_information.specific_asset_id))
        matching_id = _encode_asset_id(known_specific_id.name, known_specific_id.value)
        non_matching_id = _encode_asset_id("serialNumber", "does-not-exist")
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={matching_id}&assetIds={non_matching_id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual([], _result_ids(response))

    def test_malformed_asset_id_json_returns_400(self) -> None:
        # A value that is not valid JSON must be rejected with 400, not escape as a 500.
        bad_payload = base64.urlsafe_b64encode(b"foo").decode()
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={bad_payload}")
        self.assertEqual(400, response.status_code)

    def test_old_specific_asset_id_wrapper_no_longer_matches(self) -> None:
        # The pre-spec wrapper {"name": "specificAssetId", "value": "<SpecificAssetId as JSON string>"}
        # is no longer understood: it decodes as a SpecificAssetId named "specificAssetId", which no
        # shell carries, so the result is empty. This documents the breaking change of this fix.
        aas_list = [obj for obj in self.example_data if isinstance(obj, model.AssetAdministrationShell)]
        known_specific_id = next(iter(aas_list[0].asset_information.specific_asset_id))
        wrapper = _encode_asset_id(
            "specificAssetId",
            json.dumps({"name": known_specific_id.name, "value": known_specific_id.value}),
        )
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={wrapper}")
        self.assertEqual(200, response.status_code)
        self.assertEqual([], _result_ids(response))
