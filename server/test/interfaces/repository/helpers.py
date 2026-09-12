import unittest
from typing import TypeVar
from unittest import mock

from app.interfaces import repository
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
)
from basyx.aas.model import Identifiable
from werkzeug.test import Client, TestResponse

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
