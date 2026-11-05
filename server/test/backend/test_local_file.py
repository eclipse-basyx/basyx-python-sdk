# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import os.path
import shutil
from unittest import TestCase, mock

from app import model
from app.backend import local_file
from app.model import provider

store_path: str = os.path.dirname(__file__) + "/local_file_test_folder"
source_core: str = "file://localhost/{}/".format(store_path)


class LocalFileBackendTest(TestCase):
    def setUp(self) -> None:
        self.descriptor_store = local_file.LocalFileDescriptorStore(store_path)
        self.descriptor_store.check_directory(create=True)
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

    def tearDown(self) -> None:
        try:
            self.descriptor_store.clear()
        finally:
            shutil.rmtree(store_path)

    def test_add(self) -> None:
        self.descriptor_store.add(self.aasd1)
        # Note that this test is only checking that there are no errors during adding.
        # The actual logic is tested together with retrieval in `test_retrieval`.

    def test_retrieval(self) -> None:
        self.descriptor_store.add(self.sd1)

        # When retrieving the object, we should get the *same* instance as we added
        retrieved_descriptor = self.descriptor_store.get_item("https://example.org/SubmodelDescriptor/1")
        self.assertIs(self.sd1, retrieved_descriptor)

    def test_iterating(self) -> None:
        self.descriptor_store.add(self.sd1)
        self.descriptor_store.add(self.sd2)
        self.descriptor_store.add(self.aasd1)
        self.descriptor_store.add(self.aasd2)
        self.assertEqual(4, len(self.descriptor_store))

        # Iterate objects, add them to a DictDescriptorStore and check them
        retrieved_descriptor_store = provider.DictDescriptorStore()
        for item in self.descriptor_store:
            retrieved_descriptor_store.add(item)
        self.assertEqual(4, len(retrieved_descriptor_store))
        self.assertIn(self.sd1, retrieved_descriptor_store)
        self.assertIn(self.sd2, retrieved_descriptor_store)
        self.assertIn(self.aasd1, retrieved_descriptor_store)
        self.assertIn(self.aasd2, retrieved_descriptor_store)

    def test_len_and_iter_ignore_non_json_entries(self) -> None:
        self.descriptor_store.add(self.sd1)
        self.descriptor_store.add(self.aasd1)

        # Foreign entries in the storage directory (e.g. lost+found at the root of an ext4 volume, .DS_Store)
        # must be ignored by len() and __iter__()
        os.mkdir(os.path.join(store_path, "lost+found"))
        with open(os.path.join(store_path, ".DS_Store"), "w") as file:
            file.write("not json")
        self.assertEqual(2, len(self.descriptor_store))

        retrieved_descriptor_store = provider.DictDescriptorStore()
        for item in self.descriptor_store:
            retrieved_descriptor_store.add(item)
        self.assertEqual(2, len(retrieved_descriptor_store))
        self.assertIn(self.sd1, retrieved_descriptor_store)
        self.assertIn(self.aasd1, retrieved_descriptor_store)

    def test_failed_commit_keeps_previous_file(self) -> None:
        self.descriptor_store.add(self.sd1)
        stored_files = [f for f in os.listdir(store_path) if f.endswith(".json")]
        self.assertEqual(1, len(stored_files))
        file_path = os.path.join(store_path, stored_files[0])
        with open(file_path, "r") as file:
            content_before = file.read()

        # Simulate a failure during serialization (e.g. crash or full disk): the previously stored file must
        # stay intact instead of being truncated
        with mock.patch("app.backend.local_file.json.dump", side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                self.descriptor_store.commit(self.sd1)
        with open(file_path, "r") as file:
            self.assertEqual(content_before, file.read())
        # No temp file must be left behind
        self.assertEqual([], [f for f in os.listdir(store_path) if f.endswith(".tmp")])

    def test_failed_add_leaves_no_file(self) -> None:
        with mock.patch("app.backend.local_file.json.dump", side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                self.descriptor_store.add(self.sd1)
        self.assertNotIn(self.sd1, self.descriptor_store)
        self.assertEqual([], os.listdir(store_path))

    def test_key_errors(self) -> None:
        self.descriptor_store.add(self.aasd1)
        with self.assertRaises(KeyError) as cm:
            self.descriptor_store.add(self.aasd1)
        self.assertEqual(
            "'Descriptor with id https://example.org/AASDescriptor/1 already exists in local file database'",
            str(cm.exception),
        )

        self.descriptor_store.discard(self.aasd1)
        with self.assertRaises(KeyError) as cm:
            self.descriptor_store.get_item("https://example.org/AASDescriptor/1")
        self.assertIsNone(self.descriptor_store.get("https://example.org/AASDescriptor/1"))
        self.assertEqual(
            "'No Identifiable with id https://example.org/AASDescriptor/1 found in local file database'",
            str(cm.exception),
        )

    def test_reload_discard(self) -> None:
        self.descriptor_store.add(self.sd1)
        self.descriptor_store = local_file.LocalFileDescriptorStore(store_path)
        self.descriptor_store.discard(self.sd1)
        self.assertNotIn(self.sd1, self.descriptor_store)
