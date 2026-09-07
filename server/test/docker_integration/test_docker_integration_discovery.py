import json
import unittest
import urllib.error
import urllib.request

from app.interfaces.discovery import SUPPORTED_PROFILES
from app.util.converters import base64url_encode

from test._helper.test_helpers import REQUIRE_SERVER, SERVER_ERROR, SERVER_OKAY, TEST_CONFIG

SERVER_BASE_URL = TEST_CONFIG["server"]["url"]


@unittest.skipUnless(
    SERVER_OKAY or REQUIRE_SERVER, f"No server reachable at {SERVER_BASE_URL}: {SERVER_ERROR}"
)
class DiscoveryDockerIntegrationTest(unittest.TestCase):
    """
    Smoke tests against a real, already-running discovery server instance (e.g. started via
    ``docker run -p 8080:80 basyx-python-discovery``), analogous to ``test_docker_integration_repository.py`` for the
    repository profile: skipped entirely if no server is reachable at ``SERVER_BASE_URL``.

    Set the ``REQUIRE_SERVER_INTEGRATION_TESTS`` environment variable to make this test class fail instead of
    being skipped when no server is reachable (see ``test._helper.test_helpers``).
    """

    AAS_ID = "https://example.org/Test_AssetAdministrationShell_Discovery"
    ASSET_LINK = {"name": "MySerialNumber", "value": "SN-12345"}

    @classmethod
    def setUpClass(cls) -> None:
        if not SERVER_OKAY:
            raise RuntimeError(
                f"REQUIRE_SERVER_INTEGRATION_TESTS is set, but no server is reachable at "
                f"{SERVER_BASE_URL}: {SERVER_ERROR}"
            )

    def tearDown(self) -> None:
        delete_request = urllib.request.Request(
            f"{SERVER_BASE_URL}/lookup/shells/{base64url_encode(self.AAS_ID)}", method="DELETE"
        )
        urllib.request.urlopen(delete_request).close()

    # ------------------------------------------------------------------ GET /description

    def test_description_profiles(self):
        with urllib.request.urlopen(SERVER_BASE_URL + "/description") as response:
            self.assertEqual(200, response.status)
            data = json.loads(response.read())

        expected_profiles = {profile.value for profile in SUPPORTED_PROFILES.profiles}
        self.assertEqual(expected_profiles, set(data["profiles"]))

    # ------------------------------------------------------------------ POST/GET/DELETE /lookup/shells/<aas_id>

    def test_asset_link_roundtrip(self):
        aas_asset_links_path = f"{SERVER_BASE_URL}/lookup/shells/{base64url_encode(self.AAS_ID)}"
        body = json.dumps([self.ASSET_LINK]).encode("utf-8")

        post_request = urllib.request.Request(
            aas_asset_links_path, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(post_request) as response:
            self.assertEqual(200, response.status)

        with urllib.request.urlopen(aas_asset_links_path) as response:
            self.assertEqual(200, response.status)
            retrieved = json.loads(response.read())
        self.assertIn(self.ASSET_LINK, retrieved)

        delete_request = urllib.request.Request(aas_asset_links_path, method="DELETE")
        with urllib.request.urlopen(delete_request) as response:
            self.assertEqual(204, response.status)

        with urllib.request.urlopen(aas_asset_links_path) as response:
            self.assertEqual(200, response.status)
            self.assertEqual([], json.loads(response.read()))
