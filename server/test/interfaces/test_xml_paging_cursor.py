# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from app._config import API_BASE_PATH as BASE_PATH
from app.interfaces.repository import WSGIApp
from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.examples.data.example_aas import create_full_example
from lxml import etree
from werkzeug.test import Client


class XmlPagingCursorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.example_data = create_full_example()
        app = WSGIApp(self.example_data, DictSupplementaryFileContainer())
        self.client = Client(app)

    def test_last_page_omits_cursor(self) -> None:
        response = self.client.get(f"{BASE_PATH}/submodels?limit=100", headers={"Accept": "application/xml"})
        self.assertEqual(200, response.status_code)
        root = etree.fromstring(response.data)
        self.assertIsNone(root.get("cursor"))

    def test_next_page_has_cursor(self) -> None:
        response = self.client.get(f"{BASE_PATH}/submodels?limit=1", headers={"Accept": "application/xml"})
        self.assertEqual(200, response.status_code)
        root = etree.fromstring(response.data)
        self.assertEqual("2", root.get("cursor"))
