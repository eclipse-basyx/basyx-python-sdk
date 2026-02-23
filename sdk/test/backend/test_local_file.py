# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import os.path
import shutil

from unittest import TestCase

from basyx.aas.backend import local_file
from basyx.aas.examples.data.example_aas import *


store_path: str = os.path.dirname(__file__) + "/local_file_test_folder"
source_core: str = "file://localhost/{}/".format(store_path)


class LocalFileBackendTest(TestCase):
    def setUp(self) -> None:
        self.identifiable_store = local_file.LocalFileIdentifiableStore(store_path)
        self.identifiable_store.check_directory(create=True)

    def tearDown(self) -> None:
        try:
            self.identifiable_store.clear()
        finally:
            shutil.rmtree(store_path)

    def test_identifiable_store_add(self):
        test_object = create_example_submodel()
        self.identifiable_store.add(test_object)
        # Note that this test is only checking that there are no errors during adding.
        # The actual logic is tested together with retrieval in `test_retrieval`.

    def test_retrieval(self):
        test_object = create_example_submodel()
        self.identifiable_store.add(test_object)

        # When retrieving the object, we should get the *same* instance as we added
        test_object_retrieved = self.identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertIs(test_object, test_object_retrieved)

        # When retrieving it again, we should still get the same object
        del test_object
        test_object_retrieved_again = self.identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertIs(test_object_retrieved, test_object_retrieved_again)

    def test_example_submodel_storing(self) -> None:
        example_submodel = create_example_submodel()

        # Add exmaple submodel
        self.identifiable_store.add(example_submodel)
        self.assertEqual(1, len(self.identifiable_store))
        self.assertIn(example_submodel, self.identifiable_store)

        # Restore example submodel and check data
        submodel_restored = self.identifiable_store.get_item('https://acplt.org/Test_Submodel')
        assert (isinstance(submodel_restored, model.Submodel))
        checker = AASDataChecker(raise_immediately=True)
        check_example_submodel(checker, submodel_restored)

        # Delete example submodel
        self.identifiable_store.discard(submodel_restored)
        self.assertNotIn(example_submodel, self.identifiable_store)

    def test_iterating(self) -> None:
        example_data = create_full_example()

        # Add all objects
        for item in example_data:
            self.identifiable_store.add(item)

        self.assertEqual(5, len(self.identifiable_store))

        # Iterate objects, add them to a DictIdentifiableStore and check them
        retrieved_data_store: model.provider.DictIdentifiableStore[model.Identifiable] = (
            model.provider.DictIdentifiableStore()
        )
        for item in self.identifiable_store:
            retrieved_data_store.add(item)
        checker = AASDataChecker(raise_immediately=True)
        check_full_example(checker, retrieved_data_store)

    def test_key_errors(self) -> None:
        # Double adding an object should raise a KeyError
        example_submodel = create_example_submodel()
        self.identifiable_store.add(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.add(example_submodel)
        self.assertEqual("'Identifiable with id https://acplt.org/Test_Submodel already exists in "
                         "local file database'", str(cm.exception))

        # Querying a deleted object should raise a KeyError
        retrieved_submodel = self.identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.identifiable_store.discard(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertEqual("'No Identifiable with id https://acplt.org/Test_Submodel "
                         "found in local file database'",
                         str(cm.exception))

        # Double deleting should also raise a KeyError
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.discard(retrieved_submodel)
        self.assertEqual("'No AAS object with id https://acplt.org/Test_Submodel exists in "
                         "local file database'", str(cm.exception))

    def test_reload_discard(self) -> None:
        # Load example submodel
        example_submodel = create_example_submodel()
        self.identifiable_store.add(example_submodel)

        # Reload the DictIdentifiableStore and discard the example submodel
        self.identifiable_store = local_file.LocalFileIdentifiableStore(store_path)
        self.identifiable_store.discard(example_submodel)
        self.assertNotIn(example_submodel, self.identifiable_store)
