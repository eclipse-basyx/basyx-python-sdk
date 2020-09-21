import unittest

from aas.backend import couchdb


class CouchDBBackendTest(unittest.TestCase):
    def test_parse_source(self):
        couchdb.register_credentials(uri="couchdb.plt.rwth-aachen.de:5984",
                                     username="test_user",
                                     password="test_password")

        url, usr, psw = couchdb.CouchDBBackend._parse_source(
            "couchdbs:couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        )
        expected_url = "https://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        expected_user = "test_user"
        expected_password = "test_password"
        self.assertEqual(expected_url, url)
        self.assertEqual(expected_user, usr)
        self.assertEqual(expected_password, psw)

        url, usr, psw = couchdb.CouchDBBackend._parse_source(
            "couchdb:couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        )
        expected_url = "http://couchdb.plt.rwth-aachen.de:5984/path_to_db/path_to_doc"
        self.assertEqual(expected_url, url)
        self.assertEqual(expected_user, usr)
        self.assertEqual(expected_password, psw)

        with self.assertRaises(couchdb.CouchDBSourceError) as cm:
            couchdb.CouchDBBackend._parse_source("wrong_scheme:plt.rwth-aachen.couchdb:5984/path_to_db/path_to_doc")
            self.assertEqual("Source has wrong format. "
                             "Expected to start with {couchdb, couchdbs}, got "
                             "{wrong_scheme:plt.rwth-aachen.couchdb:5984/path_to_db/path_to_doc}",
                             cm.exception)

    def test_credential_store(self):
        couchdb.register_credentials(uri="test_host:5984",
                                     username="test_user",
                                     password="test_password")
        usr, psw = couchdb.get_credentials("test_host:5984")
        self.assertEqual("test_user", usr)
        self.assertEqual("test_password", psw)
