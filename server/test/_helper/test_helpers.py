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


# By default, the Docker integration tests are skipped whenever no server is reachable, so that a plain local
# `python -m unittest` run doesn't require a running Docker container. Set this environment variable to any
# non-empty value (e.g. in CI) to instead make those tests fail loudly if no server is reachable, so a broken
# Docker container can't silently cause the tests to be skipped without anyone noticing.
REQUIRE_SERVER = bool(os.environ.get("REQUIRE_SERVER_INTEGRATION_TESTS"))

# Check if the server is available. Otherwise, skip tests (unless REQUIRE_SERVER is set, see above).
try:
    urllib.request.urlopen(TEST_CONFIG["server"]["url"] + "/description", timeout=2)
    SERVER_OKAY = True
    SERVER_ERROR = None
except urllib.error.URLError as e:
    SERVER_OKAY = False
    SERVER_ERROR = e
