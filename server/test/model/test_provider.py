# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import json
import os
import tempfile
import unittest
from typing import Iterable

from app import adapter, model
from app.model.provider import DictDescriptorStore, load_directory

from ..adapter.descriptor_utils import example_aas_descriptor, example_submodel_descriptor


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
    which inject it for the same reason). ``_write_file()`` below replicates that injection to build valid
    fixture files.
    """

    @staticmethod
    def _write_file(
        directory: str,
        filename: str,
        aas_descriptors: Iterable[model.AssetAdministrationShellDescriptor] = (),
        submodel_descriptors: Iterable[model.SubmodelDescriptor] = (),
    ) -> None:
        data = {
            "assetAdministrationShellDescriptors": list(aas_descriptors),
            "submodelDescriptors": list(submodel_descriptors),
        }

        # Hack in the "modelType" to deserialize into the right classes
        json_save = json.loads(json.dumps(data, cls=adapter.ServerAASToJsonEncoder))
        for aas in json_save["assetAdministrationShellDescriptors"]:
            aas["modelType"] = "AssetAdministrationShellDescriptor"
        for sm in json_save["submodelDescriptors"]:
            sm["modelType"] = "SubmodelDescriptor"

        with open(os.path.join(directory, filename), "w") as f:
            json.dump(json_save, f)

    def test_loads_descriptors_from_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            aasd = example_aas_descriptor("https://example.org/AASDescriptor/1")
            sd = example_submodel_descriptor("https://example.org/SubmodelDescriptor/1")
            self._write_file(tmp_dir, "descriptors.json", aas_descriptors=[aasd], submodel_descriptors=[sd])

            store = load_directory(tmp_dir)

            self.assertEqual(2, len(store))
            self.assertIn("https://example.org/AASDescriptor/1", store)
            self.assertIn("https://example.org/SubmodelDescriptor/1", store)

    def test_merges_descriptors_from_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            aasd1 = example_aas_descriptor("https://example.org/AASDescriptor/1")
            sd1 = example_submodel_descriptor("https://example.org/SubmodelDescriptor/1")
            aasd2 = example_aas_descriptor("https://example.org/AASDescriptor/2")
            sd2 = example_submodel_descriptor("https://example.org/SubmodelDescriptor/2")
            self._write_file(tmp_dir, "a.json", aas_descriptors=[aasd1], submodel_descriptors=[sd1])
            self._write_file(tmp_dir, "b.json", aas_descriptors=[aasd2], submodel_descriptors=[sd2])

            store = load_directory(tmp_dir)

            self.assertEqual(4, len(store))
            self.assertIn("https://example.org/AASDescriptor/1", store)
            self.assertIn("https://example.org/AASDescriptor/2", store)
            self.assertIn("https://example.org/SubmodelDescriptor/1", store)
            self.assertIn("https://example.org/SubmodelDescriptor/2", store)

    def test_duplicate_ids_across_files_are_skipped_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            aasd1 = example_aas_descriptor("https://example.org/AASDescriptor/1")
            aasd2 = example_aas_descriptor("https://example.org/AASDescriptor/1")
            sd1 = example_submodel_descriptor("https://example.org/SubmodelDescriptor/1")
            sd2 = example_submodel_descriptor("https://example.org/SubmodelDescriptor/1")
            self._write_file(tmp_dir, "a.json", aas_descriptors=[aasd1], submodel_descriptors=[sd1])
            self._write_file(tmp_dir, "b.json", aas_descriptors=[aasd2], submodel_descriptors=[sd2])

            store = load_directory(tmp_dir)  # must not raise despite the duplicate ids

            self.assertEqual(2, len(store))
            self.assertIn("https://example.org/AASDescriptor/1", store)
            self.assertIn("https://example.org/SubmodelDescriptor/1", store)

    def test_ignores_non_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "readme.txt"), "w") as f:
                f.write("not a descriptor file")
            aasd = example_aas_descriptor("https://example.org/AASDescriptor/1")
            sd = example_submodel_descriptor("https://example.org/SubmodelDescriptor/1")
            self._write_file(tmp_dir, "a.json", aas_descriptors=[aasd], submodel_descriptors=[sd])

            store = load_directory(tmp_dir)

            self.assertEqual(2, len(store))

    def test_empty_directory_returns_empty_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = load_directory(tmp_dir)

            self.assertEqual(0, len(store))
