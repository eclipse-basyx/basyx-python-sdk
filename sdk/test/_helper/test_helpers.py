# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import configparser
import os
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


def env_flag(name: str) -> bool:
    """Return whether the environment variable ``name`` is set to "1", "true" or "yes" (case-insensitive)."""
    return os.environ.get(name, "false").lower() in {"1", "true", "yes"}


# By default, the schema validation tests are skipped when the AAS schema files are missing, so that a plain local
# `python -m unittest` run doesn't require downloading them first. Set this environment variable to "1"/"true"
# (e.g. in CI) to instead make those tests fail if the files are missing, so a broken download can't silently cause
# the tests to be skipped without anyone noticing.
REQUIRE_SCHEMAS = env_flag("REQUIRE_SCHEMA_TESTS")

# Likewise, the CouchDB tests are skipped when no CouchDB is reachable. Set this environment variable to fail them
# instead.
REQUIRE_COUCHDB_INTEGRATION_TESTS = env_flag("REQUIRE_COUCHDB_INTEGRATION_TESTS")

# Check if CouchDB database is available. Otherwise, skip tests (unless REQUIRE_COUCHDB_INTEGRATION_TESTS is set).
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

COUCHDB_UNREACHABLE_MESSAGE = "No CouchDB is reachable at {}/{}: {}".format(
    TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"], COUCHDB_ERROR
)
