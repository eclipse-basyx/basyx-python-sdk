# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import configparser
import os.path
import urllib.error
import urllib.request

from app._config import API_BASE_PATH

TEST_CONFIG = configparser.ConfigParser()
TEST_CONFIG.read(
    (
        os.path.join(os.path.dirname(__file__), "..", "test_config.default.ini"),
        os.path.join(os.path.dirname(__file__), "..", "test_config.ini"),
    )
)
if TEST_CONFIG.get("server", "base_path", fallback="default").lower() == "default":
    TEST_CONFIG.set("server", "base_path", API_BASE_PATH)
TEST_CONFIG.set("server", "url", TEST_CONFIG.get("server", "host") + TEST_CONFIG.get("server", "base_path"))

# Set this environment variable, to fail (instead of skip) the integration test when server is not reachable
REQUIRE_SERVER = os.environ.get("REQUIRE_SERVER_INTEGRATION_TESTS", "false").lower() in {"1", "true", "yes"}

# Check if the server is available. Otherwise, skip tests (unless REQUIRE_SERVER is set, see above).
try:
    urllib.request.urlopen(TEST_CONFIG["server"]["url"] + "/description", timeout=2)
    SERVER_OKAY = True
    SERVER_ERROR = None
except urllib.error.URLError as e:
    SERVER_OKAY = False
    SERVER_ERROR = e
