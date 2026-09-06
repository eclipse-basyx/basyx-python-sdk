import unittest
from typing import TypeVar
from unittest import mock

from app.interfaces import repository
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
    create_example_submodel,
)
from basyx.aas.model import Identifiable
from werkzeug.test import Client, TestResponse

from ..format_utils import FormatClient, inject_format_clients, with_json_client, with_xml_client

T = TypeVar('T')

class RepositoryEndpointTestBase(unittest.TestCase):
    __test__ = False

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

    @classmethod
    def two_shells_store(cls):
        store = model.DictIdentifiableStore()
        store.add(create_example_asset_administration_shell())
        second_shell = create_example_asset_administration_shell()
        second_shell.id = "https://example.org/Test_AssetAdministrationShell_Second"
        store.add(second_shell)
        return store

    # ------------------------------------------------------------------ shared assertion helpers

    def assert_ok(self, response: TestResponse) -> None:
        self.assertEqual(200, response.status_code, msg=response.get_data(as_text=True))

    def assert_error(self, response: TestResponse, status_code: int) -> None:
        self.assertEqual(status_code, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn("success", response.get_data(as_text=True), msg=response.get_data(as_text=True))


class TestServiceDescription(RepositoryEndpointTestBase):
    __test__ = True

    def test_description(self):
        response = self.client.get("/description")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn("AssetAdministrationShellRepositoryServiceSpecification/SSP-001", body)
        self.assertIn("SubmodelRepositoryServiceSpecification/SSP-001", body)

@inject_format_clients
class TestPagination(RepositoryEndpointTestBase):
    """
    Endpoint testing of the shared pagination strategy, shared by multiple endpoints. Ensures
    that all results are returned and pages do not overlap. As testing endpoints ``/submodels`` is used.

    Bodies are written once against the format-agnostic ``format_client`` helper. For each test two
    variants are generated where the :class:`~..format_utils.JsonFormatClient` and
    :class:`~..format_utils.XmlFormatClient` are injected respectively.
    """

    __test__ = True

    EXAMPLE_ID = "https://example.org/Test_Submodel_Missing"
    SECOND_ID = "https://example.org/ExampleSubmodel_Second"
    THIRD_ID = "https://example.org/ExampleSubmodel_Third"

    @with_json_client
    @with_xml_client
    def test_pagination_walks_all_items(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())
        second_sm = create_example_submodel()
        second_sm.id = self.SECOND_ID
        self.object_store.add(second_sm)
        third_sm = create_example_submodel()
        third_sm.id = self.THIRD_ID
        self.object_store.add(third_sm)

        pages = format_client.get_paginated("/submodels", limit=2, max_pages=2)

        seen = [format_client.identifier(node) for page in pages for node in page]
        self.assertEqual([2, 1], [len(page) for page in pages])
        self.assertEqual(len(seen), len(set(seen)), "an item was returned on more than one page")
        self.assertEqual({self.EXAMPLE_ID, self.SECOND_ID, self.THIRD_ID}, set(seen))

    def test_submodels_get_negative_limit_returns_400(self):
        self.object_store.add(create_example_submodel())

        response = self.client.get("/submodels?limit=-1")

        self.assert_error(response, 400)
