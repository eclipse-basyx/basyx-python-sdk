import json
import unittest
import urllib.error
import urllib.request

from app.adapter.jsonization import ServerAASToJsonEncoder
from app.interfaces.registry import SUPPORTED_PROFILES
from app.model import AssetAdministrationShellDescriptor
from app.util.converters import base64url_encode

from test._helper.test_helpers import REQUIRE_SERVER, SERVER_ERROR, SERVER_OKAY, TEST_CONFIG

SERVER_BASE_URL = TEST_CONFIG["server"]["url"]


@unittest.skipUnless(
    SERVER_OKAY or REQUIRE_SERVER, f"No server reachable at {SERVER_BASE_URL}: {SERVER_ERROR}"
)
class RegistryDockerIntegrationTest(unittest.TestCase):
    """
    Testing against a real, already-running registry server instance, analogous to ``test_docker_integration_repository.py`` for the
    repository profile: skipped entirely if no server is reachable at ``SERVER_BASE_URL``.

    Set the ``REQUIRE_SERVER_INTEGRATION_TESTS`` environment variable to make this test class fail instead of
    being skipped when no server is reachable (see ``test._helper.test_helpers``).
    """

    DESCRIPTOR_ID = "https://example.org/Test_AssetAdministrationShellDescriptor"

    @classmethod
    def setUpClass(cls) -> None:
        if not SERVER_OKAY:
            raise RuntimeError(
                f"REQUIRE_SERVER_INTEGRATION_TESTS is set, but no server is reachable at "
                f"{SERVER_BASE_URL}: {SERVER_ERROR}"
            )

    def tearDown(self) -> None:
        self._delete_descriptor(self.DESCRIPTOR_ID, ignore_missing=True)

    @staticmethod
    def _delete_descriptor(descriptor_id: str, ignore_missing: bool = False) -> None:
        request = urllib.request.Request(
            f"{SERVER_BASE_URL}/shell-descriptors/{base64url_encode(descriptor_id)}", method="DELETE"
        )
        try:
            urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            e.close()
            if not (ignore_missing and e.code == 404):
                raise

    # ------------------------------------------------------------------ GET /description

    def test_description_profiles(self):
        with urllib.request.urlopen(SERVER_BASE_URL + "/description") as response:
            self.assertEqual(200, response.status)
            data = json.loads(response.read())

        expected_profiles = {profile.value for profile in SUPPORTED_PROFILES.profiles}
        self.assertEqual(expected_profiles, set(data["profiles"]))

    # ------------------------------------------------------------------ POST/GET/DELETE /shell-descriptors

    def test_shell_descriptor_roundtrip(self):
        descriptor = AssetAdministrationShellDescriptor(id_=self.DESCRIPTOR_ID, id_short="TestDescriptor")
        body = json.dumps(descriptor, cls=ServerAASToJsonEncoder).encode("utf-8")
        descriptor_path = f"{SERVER_BASE_URL}/shell-descriptors/{base64url_encode(descriptor.id)}"

        post_request = urllib.request.Request(
            SERVER_BASE_URL + "/shell-descriptors",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_request) as response:
            self.assertEqual(201, response.status)

        with urllib.request.urlopen(descriptor_path) as response:
            self.assertEqual(200, response.status)
            retrieved = json.loads(response.read())
        self.assertEqual(descriptor.id, retrieved["id"])
        self.assertEqual("TestDescriptor", retrieved["idShort"])

        delete_request = urllib.request.Request(descriptor_path, method="DELETE")
        with urllib.request.urlopen(delete_request) as response:
            self.assertEqual(204, response.status)

        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(descriptor_path)
        self.assertEqual(404, cm.exception.code)
