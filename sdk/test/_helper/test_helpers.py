# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import configparser
import os.path
import urllib.error
import urllib.request

TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read(
    (
        os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
        os.path.join(os.path.dirname(__file__), "..", "test_config.ini"),
    )
)


# Check if CouchDB database is available. Otherwise, skip tests.
try:
    request = urllib.request.Request(
        "{}/{}".format(
            TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"]
        ),
        headers={
            "Authorization": "Basic %s"
            % base64.b64encode(
                (
                    "%s:%s"
                    % (
                        TEST_CONFIG["couchdb"]["user"],
                        TEST_CONFIG["couchdb"]["password"],
                    )
                ).encode("ascii")
            ).decode("ascii")
        },
        method="HEAD",
    )
    urllib.request.urlopen(request)
    COUCHDB_OKAY = True
    COUCHDB_ERROR = None
except urllib.error.URLError as e:
    COUCHDB_OKAY = False
    COUCHDB_ERROR = e
