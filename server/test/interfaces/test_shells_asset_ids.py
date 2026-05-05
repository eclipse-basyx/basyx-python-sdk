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


def _encode_asset_id(name: str, value: str) -> str:
    payload = json.dumps({"name": name, "value": value})
    return base64.urlsafe_b64encode(payload.encode()).decode()


class ShellsAssetIdsTest(unittest.TestCase):
    def setUp(self) -> None:
        app = WSGIApp(create_full_example(), DictSupplementaryFileContainer())
        self.client = Client(app)

    def test_malformed_asset_id_missing_field_returns_400(self) -> None:
        bad_payload = base64.urlsafe_b64encode(b'{"name": "globalAssetId"}').decode()
        response = self.client.get(f"/api/v3.1/shells?assetIds={bad_payload}")
        self.assertEqual(400, response.status_code)
