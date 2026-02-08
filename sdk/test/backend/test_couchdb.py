# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import unittest
import unittest.mock
import urllib.error

from basyx.aas.backend import couchdb
from basyx.aas.examples.data.example_aas import *

from test._helper.test_helpers import TEST_CONFIG, COUCHDB_OKAY, COUCHDB_ERROR


source_core: str = "couchdb://" + TEST_CONFIG["couchdb"]["url"].lstrip("http://") + "/" + \
                   TEST_CONFIG["couchdb"]["database"] + "/"


@unittest.skipUnless(COUCHDB_OKAY, "No CouchDB is reachable at {}/{}: {}".format(TEST_CONFIG['couchdb']['url'],
                                                                                 TEST_CONFIG['couchdb']['database'],
                                                                                 COUCHDB_ERROR))
class CouchDBBackendTest(unittest.TestCase):
    def setUp(self) -> None:
        self.couch_identifiable_store = couchdb.CouchDBIdentifiableStore(TEST_CONFIG['couchdb']['url'],
                                                                         TEST_CONFIG['couchdb']['database'])
        couchdb.register_credentials(TEST_CONFIG["couchdb"]["url"],
                                     TEST_CONFIG["couchdb"]["user"],
                                     TEST_CONFIG["couchdb"]["password"])
        self.couch_identifiable_store.check_database()

    def tearDown(self) -> None:
        self.couch_identifiable_store.clear()

    def test_identifiable_store_add(self):
        test_object = create_example_submodel()
        self.couch_identifiable_store.add(test_object)
        # Note that this test is only checking that there are no errors during adding.
        # The actual logic is tested together with retrieval in `test_retrieval`.

    def test_retrieval(self):
        test_object = create_example_submodel()
        self.couch_identifiable_store.add(test_object)

        # When retrieving the object, we should get the *same* instance as we added
        test_object_retrieved = self.couch_identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertIs(test_object, test_object_retrieved)

        # When retrieving it again, we should still get the same object
        del test_object
        test_object_retrieved_again = self.couch_identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertIs(test_object_retrieved, test_object_retrieved_again)

    def test_example_submodel_storing(self) -> None:
        example_submodel = create_example_submodel()

        # Add exmaple submodel
        self.couch_identifiable_store.add(example_submodel)
        self.assertEqual(1, len(self.couch_identifiable_store))
        self.assertIn(example_submodel, self.couch_identifiable_store)

        # Restore example submodel and check data
        submodel_restored = self.couch_identifiable_store.get_item('https://acplt.org/Test_Submodel')
        assert (isinstance(submodel_restored, model.Submodel))
        checker = AASDataChecker(raise_immediately=True)
        check_example_submodel(checker, submodel_restored)

        # Delete example submodel
        self.couch_identifiable_store.discard(submodel_restored)
        self.assertNotIn(example_submodel, self.couch_identifiable_store)

    def test_iterating(self) -> None:
        example_data = create_full_example()

        # Add all objects
        for item in example_data:
            self.couch_identifiable_store.add(item)

        self.assertEqual(5, len(self.couch_identifiable_store))

        # Iterate objects, add them to a DictIdentifiableStore and check them
        retrieved_data_store: model.provider.DictIdentifiableStore[model.Identifiable] = (
            model.provider.DictIdentifiableStore()
        )
        for item in self.couch_identifiable_store:
            retrieved_data_store.add(item)
        checker = AASDataChecker(raise_immediately=True)
        check_full_example(checker, retrieved_data_store)

    def test_key_errors(self) -> None:
        # Double adding an object should raise a KeyError
        example_submodel = create_example_submodel()
        self.couch_identifiable_store.add(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.couch_identifiable_store.add(example_submodel)
        self.assertEqual("'Identifiable with id https://acplt.org/Test_Submodel already exists in "
                         "CouchDB database'", str(cm.exception))

        # Querying a deleted object should raise a KeyError
        retrieved_submodel = self.couch_identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.couch_identifiable_store.discard(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.couch_identifiable_store.get_item('https://acplt.org/Test_Submodel')
        self.assertEqual("'No Identifiable with id https://acplt.org/Test_Submodel found in CouchDB database'",
                         str(cm.exception))

        # Double deleting should also raise a KeyError
        with self.assertRaises(KeyError) as cm:
            self.couch_identifiable_store.discard(retrieved_submodel)
        self.assertEqual("'No AAS object with id https://acplt.org/Test_Submodel exists in "
                         "CouchDB database'", str(cm.exception))
