# Copyright (c) 2020 the Eclipse BaSyx Authors
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


class CouchDBBackendOfflineMethodsTest(unittest.TestCase):
    def test_parse_source(self):
        couchdb.register_credentials(url="couchdb.plt.rwth-aachen.de:5984",
                                     username="test_user",
                                     password="test_password")

        url = couchdb.CouchDBBackend._parse_source(
            "couchdbs://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        )
        expected_url = "https://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        self.assertEqual(expected_url, url)

        url = couchdb.CouchDBBackend._parse_source(
            "couchdb://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        )
        expected_url = "http://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        self.assertEqual(expected_url, url)

        with self.assertRaises(couchdb.CouchDBSourceError) as cm:
            couchdb.CouchDBBackend._parse_source("wrong_scheme:plt.rwth-aachen.couchdb:5984/path_to_db/path_to_doc")
        self.assertEqual("Source has wrong format. "
                         "Expected to start with {couchdb://, couchdbs://}, got "
                         "{wrong_scheme:plt.rwth-aachen.couchdb:5984/path_to_db/path_to_doc}",
                         str(cm.exception))


@unittest.skipUnless(COUCHDB_OKAY, "No CouchDB is reachable at {}/{}: {}".format(TEST_CONFIG['couchdb']['url'],
                                                                                 TEST_CONFIG['couchdb']['database'],
                                                                                 COUCHDB_ERROR))
class CouchDBBackendTest(unittest.TestCase):
    def setUp(self) -> None:
        self.object_store = couchdb.CouchDBObjectStore(TEST_CONFIG['couchdb']['url'],
                                                       TEST_CONFIG['couchdb']['database'])
        couchdb.register_credentials(TEST_CONFIG["couchdb"]["url"],
                                     TEST_CONFIG["couchdb"]["user"],
                                     TEST_CONFIG["couchdb"]["password"])
        self.object_store.check_database()

    def tearDown(self) -> None:
        self.object_store.clear()

    def test_object_store_add(self):
        test_object = create_example_submodel()
        self.object_store.add(test_object)
        self.assertEqual(test_object.source, source_core+"IRI-https%3A%2F%2Facplt.org%2FTest_Submodel")

    def test_retrieval(self):
        test_object = create_example_submodel()
        self.object_store.add(test_object)

        # When retrieving the object, we should get the *same* instance as we added
        test_object_retrieved = self.object_store.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))
        self.assertIs(test_object, test_object_retrieved)

        # When retrieving it again, we should still get the same object
        del test_object
        test_object_retrieved_again = self.object_store.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))
        self.assertIs(test_object_retrieved, test_object_retrieved_again)

        # However, a changed source should invalidate the cached object, so we should get a new copy
        test_object_retrieved.source = "couchdb://example.com/example/IRI-https%3A%2F%2Facplt.org%2FTest_Submodel"
        test_object_retrieved_third = self.object_store.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))
        self.assertIsNot(test_object_retrieved, test_object_retrieved_third)

    def test_example_submodel_storing(self) -> None:
        example_submodel = create_example_submodel()

        # Add exmaple submodel
        self.object_store.add(example_submodel)
        self.assertEqual(1, len(self.object_store))
        self.assertIn(example_submodel, self.object_store)

        # Restore example submodel and check data
        submodel_restored = self.object_store.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))
        assert (isinstance(submodel_restored, model.Submodel))
        checker = AASDataChecker(raise_immediately=True)
        check_example_submodel(checker, submodel_restored)

        # Delete example submodel
        self.object_store.discard(submodel_restored)
        self.assertNotIn(example_submodel, self.object_store)

    def test_iterating(self) -> None:
        example_data = create_full_example()

        # Add all objects
        for item in example_data:
            self.object_store.add(item)

        self.assertEqual(6, len(self.object_store))

        # Iterate objects, add them to a DictObjectStore and check them
        retrieved_data_store: model.provider.DictObjectStore[model.Identifiable] = model.provider.DictObjectStore()
        for item in self.object_store:
            retrieved_data_store.add(item)
        checker = AASDataChecker(raise_immediately=True)
        check_full_example(checker, retrieved_data_store)

    def test_key_errors(self) -> None:
        # Double adding an object should raise a KeyError
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.object_store.add(example_submodel)
        self.assertEqual("'Identifiable with id Identifier(IRI=https://acplt.org/Test_Submodel) already exists in "
                         "CouchDB database'", str(cm.exception))

        # Querying a deleted object should raise a KeyError
        retrieved_submodel = self.object_store.get_identifiable(
            model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))
        self.object_store.discard(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.object_store.get_identifiable(model.Identifier('https://acplt.org/Test_Submodel',
                                                                model.IdentifierType.IRI))
        self.assertEqual("'No Identifiable with id IRI-https://acplt.org/Test_Submodel found in CouchDB database'",
                         str(cm.exception))

        # Double deleting should also raise a KeyError
        with self.assertRaises(KeyError) as cm:
            self.object_store.discard(retrieved_submodel)
        self.assertEqual("'No AAS object with id Identifier(IRI=https://acplt.org/Test_Submodel) exists in "
                         "CouchDB database'", str(cm.exception))

    def test_conflict_errors(self):
        # Preperation: add object and retrieve it from the database
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)
        retrieved_submodel = self.object_store.get_identifiable(
            model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))

        # Simulate a concurrent modification (Commit submodel, while preventing that the couchdb revision store is
        # updated)
        with unittest.mock.patch("basyx.aas.backend.couchdb.set_couchdb_revision"):
            retrieved_submodel.commit()

        # Committing changes to the retrieved object should now raise a conflict error
        retrieved_submodel.id_short = "myOtherNewIdShort"
        with self.assertRaises(couchdb.CouchDBConflictError) as cm:
            retrieved_submodel.commit()
        self.assertEqual("Could not commit changes to id Identifier(IRI=https://acplt.org/Test_Submodel) due to a "
                         "concurrent modification in the database.", str(cm.exception))

        # Deleting the submodel with safe_delete should also raise a conflict error. Deletion without safe_delete should
        # work
        with self.assertRaises(couchdb.CouchDBConflictError) as cm:
            self.object_store.discard(retrieved_submodel, True)
        self.assertEqual("Object with id Identifier(IRI=https://acplt.org/Test_Submodel) has been modified in the "
                         "database since the version requested to be deleted.", str(cm.exception))
        self.object_store.discard(retrieved_submodel, False)
        self.assertEqual(0, len(self.object_store))

        # Committing after deletion should not raise a conflict error due to removal of the source attribute
        retrieved_submodel.commit()

    def test_editing(self):
        test_object = create_example_submodel()
        self.object_store.add(test_object)

        # Test if commit uploads changes
        test_object.id_short = "SomeNewIdShort"
        test_object.commit()

        # Test if update restores changes
        test_object.id_short = "AnotherIdShort"
        test_object.update()
        self.assertEqual("SomeNewIdShort", test_object.id_short)
