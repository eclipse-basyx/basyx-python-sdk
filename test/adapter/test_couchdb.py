# Copyright 2019 PyI40AAS Contributors
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
import concurrent.futures
import configparser
import os
import unittest
import urllib.request
import urllib.error

from aas import model
from aas.adapter import couchdb

from aas.examples import example_create_aas
from .._helper.helpers import ExampleHelper


TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read((os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
                  os.path.join(os.path.dirname(__file__), "..", "test_config.ini")))


# Check if CouchDB database is avalable. Otherwise, skip tests.
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


@unittest.skipUnless(COUCHDB_OKAY, "No CouchDB is reachable at {}/{}: {}".format(TEST_CONFIG['couchdb']['url'],
                                                                                 TEST_CONFIG['couchdb']['database'],
                                                                                 COUCHDB_ERROR))
class CouchDBTest(ExampleHelper):
    def setUp(self) -> None:
        # Create CouchDB store, login and check database
        self.db = couchdb.CouchDBObjectStore(TEST_CONFIG['couchdb']['url'], TEST_CONFIG['couchdb']['database'])
        self.db.login(TEST_CONFIG['couchdb']['user'], TEST_CONFIG['couchdb']['password'])
        # TODO create clean database before test
        self.db.check_database()

    def tearDown(self) -> None:
        self.db.clear()
        self.db.logout()

    def test_example_submodel_storing(self) -> None:
        example_submodel = example_create_aas.create_example_submodel()

        # Add exmaple submodel
        self.db.add(example_submodel)
        self.assertEqual(1, len(self.db))
        self.assertIn(example_submodel, self.db)

        # Restore example submodel and check data
        submodel_restored = self.db.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))
        assert(isinstance(submodel_restored, model.Submodel))
        self.assert_example_submodel(submodel_restored)

        # Delete example submodel
        self.db.discard(submodel_restored)
        self.assertNotIn(example_submodel, self.db)

    def test_iterating(self) -> None:
        example_data = example_create_aas.create_full_example()

        # Add all objects
        for item in example_data:
            self.db.add(item)

        self.assertEqual(6, len(self.db))

        # Iterate objects, add them to a DictObjectStore and check them
        retrieved_data_store: model.registry.DictObjectStore[model.Identifiable] = model.registry.DictObjectStore()
        for item in self.db:
            retrieved_data_store.add(item)
        self.assert_full_example(retrieved_data_store)

    def test_parallel_iterating(self) -> None:
        example_data = example_create_aas.create_full_example()
        ids = [item.identification for item in example_data]

        # Add objects via thread pool executor
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.map(self.db.add, example_data)
        list(result)  # Iterate Executor result to raise exceptions

        self.assertEqual(6, len(self.db))

        # Retrieve objects via thread pool executor
        with concurrent.futures.ThreadPoolExecutor() as pool:
            retrieved_objects = pool.map(self.db.get_identifiable, ids)

        retrieved_data_store: model.registry.DictObjectStore[model.Identifiable] = model.registry.DictObjectStore()
        for item in retrieved_objects:
            retrieved_data_store.add(item)
        self.assertEqual(6, len(retrieved_data_store))
        self.assert_full_example(retrieved_data_store)

        # Delete objects via thread pool executor
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.map(self.db.discard, example_data)
        list(result)  # Iterate Executor result to raise exceptions

        self.assertEqual(0, len(self.db))

    def test_key_errors(self) -> None:
        # Double adding an object should raise a KeyError
        example_submodel = example_create_aas.create_example_submodel()
        self.db.add(example_submodel)
        with self.assertRaises(KeyError):
            self.db.add(example_submodel)

        # Querying a deleted object should raise a KeyError
        self.db.get_identifiable(model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))
        self.db.discard(example_submodel)
        with self.assertRaises(KeyError):
            self.db.get_identifiable(model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))

    def test_editing(self) -> None:
        example_submodel = example_create_aas.create_example_submodel()
        self.db.add(example_submodel)

        # Retrieve submodel from database and change ExampleCapability's semanticId
        submodel = self.db.get_identifiable(
            model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))
        assert(isinstance(submodel, couchdb.CouchDBSubmodel))
        capability = submodel.submodel_element.get_referable('ExampleCapability')
        capability.semantic_id = model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                  local=False,
                                                  value='http://acplt.org/Capabilities/AnotherCapability',
                                                  id_type=model.KeyType.IRDI),))

        # Commit changes
        submodel.commit_changes()

        # Change ExampleSubmodelCollectionOrdered's description
        collection = submodel.submodel_element.get_referable('ExampleSubmodelCollectionOrdered')
        collection.description['de'] = "Eine sehr wichtige Sammlung von Elementen"   # type: ignore

        # Commit changes
        submodel.commit_changes()

        # Check version in database
        new_submodel = self.db.get_identifiable(
            model.Identifier('https://acplt.org/Test_Submodel', model.IdentifierType.IRI))
        assert(isinstance(new_submodel, couchdb.CouchDBSubmodel))
        capability = new_submodel.submodel_element.get_referable('ExampleCapability')
        assert(isinstance(capability, model.Capability))
        self.assertEqual('http://acplt.org/Capabilities/AnotherCapability',
                         capability.semantic_id.key[0].value)  # type: ignore
        collection = new_submodel.submodel_element.get_referable('ExampleSubmodelCollectionOrdered')
        self.assertEqual("Eine sehr wichtige Sammlung von Elementen", collection.description['de'])  # type: ignore
