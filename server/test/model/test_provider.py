import json
import os
import shutil
import unittest
from typing import Any, Dict, Iterable, Union

from app import adapter, model
from app.backend.local_file import DESCRIPTOR_TYPE_TO_STRING
from app.model.provider import DictDescriptorStore, load_directory

_Descriptor = Union[model.AssetAdministrationShellDescriptor, model.SubmodelDescriptor]


class DictDescriptorStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_endpoint = model.Endpoint(
            interface="AAS-3.0", protocol_information=model.ProtocolInformation(href="https://example.org/")
        )
        self.aasd1 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self.aasd2 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/2", endpoints=[self.mock_endpoint]
        )
        self.sd1 = model.SubmodelDescriptor(
            id_="https://example.org/SubmodelDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self.sd2 = model.SubmodelDescriptor(
            id_="https://example.org/SubmodelDescriptor/2", endpoints=[self.mock_endpoint]
        )

    def test_store_retrieve(self) -> None:
        descriptor_store: DictDescriptorStore = DictDescriptorStore()
        descriptor_store.add(self.aasd1)
        descriptor_store.add(self.aasd2)
        self.assertIn(self.aasd1, descriptor_store)
        self.assertFalse(self.sd1 in descriptor_store)

        aasd3 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        with self.assertRaises(KeyError) as cm:
            descriptor_store.add(aasd3)
        self.assertEqual(
            "'Descriptor object with same id https://example.org/AASDescriptor/1 is already stored in this store'",
            str(cm.exception),
        )
        self.assertEqual(2, len(descriptor_store))
        self.assertIs(self.aasd1, descriptor_store.get("https://example.org/AASDescriptor/1"))

        descriptor_store.discard(self.aasd1)
        with self.assertRaises(KeyError) as cm:
            descriptor_store.get_item("https://example.org/AASDescriptor/1")
        self.assertIsNone(descriptor_store.get("https://example.org/AASDescriptor/1"))
        self.assertEqual("'https://example.org/AASDescriptor/1'", str(cm.exception))
        self.assertIs(self.aasd2, descriptor_store.pop())
        self.assertEqual(0, len(descriptor_store))

    def test_store_update(self) -> None:
        descriptor_store1: DictDescriptorStore = DictDescriptorStore()
        descriptor_store2: DictDescriptorStore = DictDescriptorStore()
        descriptor_store1.add(self.sd1)
        descriptor_store2.add(self.sd2)
        descriptor_store1.update(descriptor_store2)
        self.assertIsInstance(descriptor_store1, DictDescriptorStore)
        self.assertIn(self.sd2, descriptor_store1)


class LoadDirectoryTest(unittest.TestCase):
    """
    Tests for :func:`~app.model.provider.load_directory`.

    Descriptor JSON files must carry a ``modelType`` field for each descriptor so that
    ``ServerAASFromJsonDecoder`` recognizes and converts them (descriptors aren't ``Referable``, so the SDK's
    encoder never writes ``modelType`` on its own -- see ``LocalFileDescriptorStore.add()``/``commit()``,
    which inject it for the same reason). ``_descriptor_to_json_dict()`` below replicates that injection to
    build valid fixture files.
    """

    TEST_DIR = os.path.join(os.path.dirname(__file__), "load_directory_test_folder")

    def setUp(self) -> None:
        os.makedirs(self.TEST_DIR, exist_ok=True)
        self.mock_endpoint = model.Endpoint(
            interface="AAS-3.0", protocol_information=model.ProtocolInformation(href="https://example.org/")
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.TEST_DIR)

    @staticmethod
    def _descriptor_to_json_dict(desc: _Descriptor) -> Dict[str, Any]:
        data: Dict[str, Any] = json.loads(json.dumps(desc, cls=adapter.ServerAASToJsonEncoder))
        data["modelType"] = DESCRIPTOR_TYPE_TO_STRING[type(desc)]
        return data

    def _write_file(
        self,
        filename: str,
        aas_descriptors: Iterable[model.AssetAdministrationShellDescriptor] = (),
        submodel_descriptors: Iterable[model.SubmodelDescriptor] = (),
    ) -> None:
        data = {
            "assetAdministrationShellDescriptors": [self._descriptor_to_json_dict(d) for d in aas_descriptors],
            "submodelDescriptors": [self._descriptor_to_json_dict(d) for d in submodel_descriptors],
        }
        with open(os.path.join(self.TEST_DIR, filename), "w") as f:
            json.dump(data, f)

    def test_loads_descriptors_from_single_file(self) -> None:
        aasd = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        sd = model.SubmodelDescriptor(id_="https://example.org/SubmodelDescriptor/1", endpoints=[self.mock_endpoint])
        self._write_file("descriptors.json", aas_descriptors=[aasd], submodel_descriptors=[sd])

        store = load_directory(self.TEST_DIR)

        self.assertEqual(2, len(store))
        self.assertIn("https://example.org/AASDescriptor/1", store)
        self.assertIn("https://example.org/SubmodelDescriptor/1", store)

    def test_merges_descriptors_from_multiple_files(self) -> None:
        aasd1 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        aasd2 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/2", endpoints=[self.mock_endpoint]
        )
        self._write_file("a.json", aas_descriptors=[aasd1])
        self._write_file("b.json", aas_descriptors=[aasd2])

        store = load_directory(self.TEST_DIR)

        self.assertEqual(2, len(store))
        self.assertIn("https://example.org/AASDescriptor/1", store)
        self.assertIn("https://example.org/AASDescriptor/2", store)

    def test_duplicate_ids_across_files_are_skipped_not_raised(self) -> None:
        aasd1 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        aasd2 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self._write_file("a.json", aas_descriptors=[aasd1])
        self._write_file("b.json", aas_descriptors=[aasd2])

        store = load_directory(self.TEST_DIR)  # must not raise despite the duplicate id

        self.assertEqual(1, len(store))
        self.assertIn("https://example.org/AASDescriptor/1", store)

    def test_ignores_non_json_files(self) -> None:
        with open(os.path.join(self.TEST_DIR, "readme.txt"), "w") as f:
            f.write("not a descriptor file")
        aasd = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self._write_file("a.json", aas_descriptors=[aasd])

        store = load_directory(self.TEST_DIR)

        self.assertEqual(1, len(store))

    def test_empty_directory_returns_empty_store(self) -> None:
        store = load_directory(self.TEST_DIR)

        self.assertEqual(0, len(store))
