# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

from typing import Any, Callable, TypeVar
from unittest import mock

from app.interfaces import repository
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
)
from basyx.aas.model import Identifiable
from werkzeug.test import Client

from ..format_utils import AssertResponseMixin, FormatClient

T = TypeVar('T')

class RepositoryEndpointTestBase(AssertResponseMixin):
    object_store: model.SetIdentifiableStore[Identifiable]
    file_store: mock.Mock
    repository_server: repository.WSGIApp
    client: Client

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.object_store = model.SetIdentifiableStore()  # DictIdentifiableStore breaks, when IDs change
        cls.file_store = mock.Mock(spec=aasx.AbstractSupplementaryFileContainer)
        cls.repository_server = repository.WSGIApp(cls.object_store, cls.file_store, base_path="")
        cls.client = Client(cls.repository_server)

    def setUp(self) -> None:
        self.object_store.clear()
        self.file_store.reset_mock()

    def assert_extent_toggles_blob_value(
        self, format_client: FormatClient, path: str, locate_blob: Callable[[Any], Any],
    ) -> None:
        """
        Ensures the BLOB value is only serialized with ``extent=WithBLOBValue``. ``WithoutBLOBValue`` is the default.

        :param locate_blob: Returns the Blob node from the parsed response body
        """
        with self.subTest(extent="WithBLOBValue"):
            response = format_client.get(f"{path}?extent=WithBLOBValue")
            self.assert_ok(response)
            blob = locate_blob(format_client.parse_object(response))
            self.assertIn("value", blob)

        for omit_query in ("?extent=WithoutBLOBValue", ""):
            with self.subTest(extent=omit_query or "default"):
                response = format_client.get(f"{path}{omit_query}")
                self.assert_ok(response)
                blob = locate_blob(format_client.parse_object(response))
                self.assertNotIn("value", blob)

    def assert_xml_requires_blob_value(self, format_client: FormatClient, path: str) -> None:
        """
        Ensures Normal XML responses are only served with ``extent=WithBLOBValue`` and ``level=deep``, as the XML
        serialization can neither omit BLOB values nor children. Every other combination must be rejected with
        ``406 Not Acceptable``.
        """
        for query in ("", "?extent=WithoutBLOBValue", "?extent=WithBLOBValue&level=core"):
            with self.subTest(query=query or "default"):
                self.assert_error(format_client.get(f"{path}{query}"), 406)
        with self.subTest(query="?extent=WithBLOBValue"):
            self.assert_ok(format_client.get(f"{path}?extent=WithBLOBValue"))

    @classmethod
    def two_shells_store(cls):
        store = model.DictIdentifiableStore()
        store.add(create_example_asset_administration_shell())
        second_shell = create_example_asset_administration_shell()
        second_shell.id = "https://example.org/Test_AssetAdministrationShell_Second"
        store.add(second_shell)
        return store
