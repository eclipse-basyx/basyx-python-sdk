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
import os
import unittest
import urllib.request
import urllib.error

from aas.backend import backends, couchdb
from aas import model
from aas.examples.data.example_aas import *


TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read((os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
                  os.path.join(os.path.dirname(__file__), "..", "test_config.ini")))

source_core: str = "couchdb:" + TEST_CONFIG["couchdb"]["url"].lstrip("http://") + "/" + \
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
            "couchdbs:couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        )
        expected_url = "https://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        self.assertEqual(expected_url, url)

        url = couchdb.CouchDBBackend._parse_source(
            "couchdb:couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
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
    def test_authorization(self):
        couchdb.register_credentials(TEST_CONFIG["couchdb"]["url"].lstrip("http://"),
                                     TEST_CONFIG["couchdb"]["user"],
                                     TEST_CONFIG["couchdb"]["password"])
        req = urllib.request.Request("{}/{}".format(TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"]),
                                     headers={'Content-type': 'application/json'})
        couchdb.CouchDBBackend._do_request(req)

    def test_commit_object(self):
        test_object = create_example_submodel()
        test_object.source = source_core + "example_submodel"
        couchdb.CouchDBBackend.commit_object(test_object, test_object, [])
        # Cleanup CouchDB
        couchdb.CouchDBBackend.delete_object(test_object)

    def test_commit_nested_object(self):
        backends.register_backend("couchdb", couchdb.CouchDBBackend)
        test_submodel = create_example_submodel()
        test_submodel.source = source_core + "another_example_submodel"
        test_property = test_submodel.get_referable("ExampleSubmodelCollectionOrdered").get_referable("ExampleProperty")
        self.assertIsInstance(test_property, model.Property)
        test_property.commit()
        # Cleanup CouchDB
        couchdb.CouchDBBackend.delete_object(test_submodel)

    def test_update_object(self):
        test_object = create_example_submodel()
        test_object.source = source_core + "example_submodel"
        couchdb.CouchDBBackend.commit_object(test_object, test_object, [])
        couchdb.CouchDBBackend.update_object(test_object, test_object, [])
        # Cleanup CouchDB
        test_object.source = source_core + "example_submodel"
        # todo: remove the line above, when the json de/serialization is fixed
        couchdb.CouchDBBackend.delete_object(test_object)

    def test_update_nested_object(self):
        test_submodel = create_example_submodel()
        test_submodel.source = source_core + "another_example_submodel"
        test_submodel.commit()
        test_property = test_submodel.get_referable("ExampleSubmodelCollectionOrdered").get_referable("ExampleProperty")
        self.assertIsInstance(test_property, model.Property)
        test_property.value = "A new value"
        test_property.update()
        self.assertEqual(test_property.value, 'exampleValue')
        # Cleanup CouchDB
        test_submodel.source = source_core + "another_example_submodel"
        # todo: remove the line above, when the json de/serialization is fixed
        couchdb.CouchDBBackend.delete_object(test_submodel)

    def test_commit_overwrite(self):
        test_submodel = create_example_submodel()
        test_submodel.source = source_core + "another_example_submodel"
        test_submodel.commit()

        test_property = test_submodel.get_referable("ExampleSubmodelCollectionOrdered").get_referable("ExampleProperty")
        self.assertIsInstance(test_property, model.Property)
        test_property.value = "A new value"
        test_property.commit()

        test_property.value = "Something else"
        test_property.update()
        self.assertEqual(test_property.value, "A new value")
        # Cleanup Couchdb
        test_submodel.source = source_core + "another_example_submodel"
        # todo: remove the line above, when the json de/serialization is fixed
        couchdb.CouchDBBackend.delete_object(test_submodel)
