import unittest

from aas.backend import couchdb


class CouchDBBackendTest(unittest.TestCase):
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
