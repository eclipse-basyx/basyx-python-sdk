# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import base64
import configparser
import copy
import os
import unittest
import unittest.mock
import urllib.request
import urllib.error

from aas.backend import backends, couchdb
from aas.examples.data.example_aas import *


TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read((os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
                  os.path.join(os.path.dirname(__file__), "..", "test_config.ini")))

source_core: str = "couchdb://" + TEST_CONFIG["couchdb"]["url"].lstrip("http://") + "/" + \
                   TEST_CONFIG["couchdb"]["database"] + "/"


# Check if CouchDB database is available. Otherwise, skip tests.
try:
    request = urllib.request.Request(
        "{}/{}".format(TEST_CONFIG['couchdb']['url'], TEST_CONFIG['couchdb']['database']),
        headers={
            'Authorization': 'Basic %s' % base64.b64encode(
                ('%s:%s' % (TEST_CONFIG['couchdb']['user'], TEST_CONFIG['couchdb']['password']))
                .encode('ascii')).decode("ascii")
            },
        method='HEAD')
    urllib.request.urlopen(request)
    COUCHDB_OKAY = True
    COUCHDB_ERROR = None
except urllib.error.URLError as e:
    COUCHDB_OKAY = False
    COUCHDB_ERROR = e


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
                             "Expected to start with {couchdb, couchdbs}, got "
                             "{wrong_scheme:plt.rwth-aachen.couchdb:5984/path_to_db/path_to_doc}",
                             cm.exception)


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
        backends.register_backend("couchdb", couchdb.CouchDBBackend)
        self.object_store.check_database()

    def tearDown(self) -> None:
        self.object_store.clear()

    def test_object_store_add(self):
        test_object = create_example_submodel()
        self.object_store.add(test_object)
        self.assertEqual(test_object.source, source_core+"IRI-https%3A%2F%2Facplt.org%2FTest_Submodel")

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
        with unittest.mock.patch("aas.backend.couchdb.set_couchdb_revision"):
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
