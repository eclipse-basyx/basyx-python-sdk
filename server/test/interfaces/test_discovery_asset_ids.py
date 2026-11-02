# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

"""Client-error mapping for discovery ``GET /lookup/shells?assetIds=...`` (#672)."""

import base64
import json
import unittest

from app.interfaces.discovery import DiscoveryAPI, DiscoveryStore
from werkzeug.test import Client


def _b64url_json(obj) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class DiscoveryAssetIdsClientErrorsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(DiscoveryAPI(DiscoveryStore(), base_path=""))

    def test_asset_ids_missing_value_returns_400(self) -> None:
        response = self.client.get(f"/lookup/shells?assetIds={_b64url_json({'name': 'serial'})}")
        self.assertEqual(400, response.status_code)

    def test_asset_ids_missing_name_returns_400(self) -> None:
        response = self.client.get(f"/lookup/shells?assetIds={_b64url_json({'value': '123'})}")
        self.assertEqual(400, response.status_code)
