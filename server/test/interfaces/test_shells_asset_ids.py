# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.examples.data.example_aas import create_full_example
from werkzeug.test import Client

from app.interfaces.repository import WSGIApp

BASE_PATH = "/api/v3.1"


def _encode_asset_id(name: str, value: str) -> str:
    payload = json.dumps({"name": name, "value": value})
    return base64.urlsafe_b64encode(payload.encode()).decode()


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
        result = json.loads(response.data)
        returned_ids = [r["id"] for r in result]
        self.assertIn(aas_list[0].id, returned_ids)

    def test_malformed_asset_id_missing_field_returns_400(self) -> None:
        bad_payload = base64.urlsafe_b64encode(b'{"name": "globalAssetId"}').decode()
        response = self.client.get(f"{BASE_PATH}/shells?assetIds={bad_payload}")
        self.assertEqual(400, response.status_code)
