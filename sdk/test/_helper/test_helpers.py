import configparser
import os.path
import urllib.request
import urllib.error
import base64

TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read((os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
                  os.path.join(os.path.dirname(__file__), "..", "test_config.ini")))


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
