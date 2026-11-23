# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import configparser
import http.client
import os
import os.path
import unittest
import urllib.request
from typing import Final, Optional

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
REQUIRE_SCHEMAS: Final[bool] = env_flag("REQUIRE_SCHEMA_TESTS")

# Likewise, the CouchDB tests are skipped when no CouchDB is reachable. Set this environment variable to fail them
# instead (see require_couchdb()).
REQUIRE_COUCHDB_INTEGRATION_TESTS: Final[bool] = env_flag("REQUIRE_COUCHDB_INTEGRATION_TESTS")

# Check if the CouchDB test database is reachable. The timeout keeps an unresponsive server from stalling the test run.
# OSError covers HTTP errors (urllib's URLError) as well as refused connections and timeouts. HTTPException covers
# malformed responses, e.g. from a service on the port that does not speak HTTP.
COUCHDB_ERROR: Optional[Exception] = None
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
    urllib.request.urlopen(request, timeout=5).close()
except (OSError, http.client.HTTPException) as e:
    COUCHDB_ERROR = e


def require_couchdb() -> None:
    """
    Skip the calling test if no CouchDB is reachable, or fail it if ``REQUIRE_COUCHDB_INTEGRATION_TESTS`` is set.

    Call it in ``setUpClass()`` of a test class or at the beginning of a test method.
    """
    if COUCHDB_ERROR is None:
        return
    location = "{}/{}".format(TEST_CONFIG["couchdb"]["url"], TEST_CONFIG["couchdb"]["database"])
    if REQUIRE_COUCHDB_INTEGRATION_TESTS:
        raise RuntimeError(
            f"REQUIRE_COUCHDB_INTEGRATION_TESTS is set, but no CouchDB is reachable at {location}: {COUCHDB_ERROR}"
        )
    raise unittest.SkipTest(f"No CouchDB is reachable at {location}: {COUCHDB_ERROR}, skipping test")
