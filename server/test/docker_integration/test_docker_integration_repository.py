import json
import unittest
import urllib.error
import urllib.request

from app.interfaces.repository import SUPPORTED_PROFILES
from app.util.converters import base64url_encode
from basyx.aas.adapter.json import AASFromJsonDecoder, AASToJsonEncoder
from basyx.aas.examples.data.example_aas import (
    AASDataChecker,
    check_example_asset_administration_shell,
    create_example_asset_administration_shell,
)

from test._helper.test_helpers import REQUIRE_SERVER, SERVER_ERROR, SERVER_OKAY, TEST_CONFIG

SERVER_BASE_URL = TEST_CONFIG["server"]["url"]


@unittest.skipUnless(
    SERVER_OKAY or REQUIRE_SERVER, f"No server reachable at {SERVER_BASE_URL}: {SERVER_ERROR}"
)
class ServerDockerIntegrationTest(unittest.TestCase):
    """
    Smoke tests against a real, already-running server instance (e.g. started via
    ``docker run -p 8080:80 basyx-python-server``), analogous to how ``test_couchdb.py`` tests
    against a real CouchDB instance: skipped entirely if no server is reachable at ``SERVER_BASE_URL``.

    Set the ``REQUIRE_SERVER_INTEGRATION_TESTS`` environment variable to make this test class fail instead of
    being skipped when no server is reachable (see ``test._helper.test_helpers``). CI uses this to ensure a
    broken Docker container is reported as a failure rather than silently skipping the tests.
    """

    @classmethod
    def setUpClass(cls) -> None:
        if not SERVER_OKAY:
            raise RuntimeError(
                f"REQUIRE_SERVER_INTEGRATION_TESTS is set, but no server is reachable at "
                f"{SERVER_BASE_URL}: {SERVER_ERROR}"
            )

    def tearDown(self) -> None:
        self._delete_shell(create_example_asset_administration_shell().id, ignore_missing=True)

    @staticmethod
    def _delete_shell(shell_id: str, ignore_missing: bool = False) -> None:
        request = urllib.request.Request(f"{SERVER_BASE_URL}/shells/{base64url_encode(shell_id)}", method="DELETE")
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

    # ------------------------------------------------------------------ POST/GET/DELETE /shells

    def test_shell_roundtrip(self):
        shell = create_example_asset_administration_shell()
        body = json.dumps(shell, cls=AASToJsonEncoder).encode("utf-8")
        shell_path = f"{SERVER_BASE_URL}/shells/{base64url_encode(shell.id)}"

        post_request = urllib.request.Request(
            SERVER_BASE_URL + "/shells", data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(post_request) as response:
            self.assertEqual(201, response.status)

        with urllib.request.urlopen(shell_path) as response:
            self.assertEqual(200, response.status)
            retrieved = json.loads(response.read(), cls=AASFromJsonDecoder)

        checker = AASDataChecker(raise_immediately=True)
        check_example_asset_administration_shell(checker, retrieved)

    def test_shell_duplicate_post(self):
        shell = create_example_asset_administration_shell()
        body = json.dumps(shell, cls=AASToJsonEncoder).encode("utf-8")
        post_request = urllib.request.Request(
            SERVER_BASE_URL + "/shells", data=body, headers={"Content-Type": "application/json"}, method="POST"
        )

        with urllib.request.urlopen(post_request) as response:
            self.assertEqual(201, response.status)

        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(post_request)
        self.assertEqual(409, cm.exception.code)

    def test_shell_update(self):
        shell = create_example_asset_administration_shell()
        body = json.dumps(shell, cls=AASToJsonEncoder).encode("utf-8")
        shell_path = f"{SERVER_BASE_URL}/shells/{base64url_encode(shell.id)}"

        post_request = urllib.request.Request(
            SERVER_BASE_URL + "/shells", data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(post_request) as response:
            self.assertEqual(201, response.status)

        shell.id_short = "UpdatedIdShort"
        updated_body = json.dumps(shell, cls=AASToJsonEncoder).encode("utf-8")
        put_request = urllib.request.Request(
            shell_path, data=updated_body, headers={"Content-Type": "application/json"}, method="PUT"
        )
        with urllib.request.urlopen(put_request) as response:
            self.assertEqual(204, response.status)

        with urllib.request.urlopen(shell_path) as response:
            self.assertEqual(200, response.status)
            retrieved = json.loads(response.read(), cls=AASFromJsonDecoder)
        self.assertEqual("UpdatedIdShort", retrieved.id_short)

    # ------------------------------------------------------------------ GET/PUT/DELETE on a missing /shells/<aas_id>

    def test_shell_not_found(self):
        missing_shell_path = f"{SERVER_BASE_URL}/shells/{base64url_encode('https://example.org/unknown-shell')}"

        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(missing_shell_path)
        self.assertEqual(404, cm.exception.code)

        delete_request = urllib.request.Request(missing_shell_path, method="DELETE")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(delete_request)
        self.assertEqual(404, cm.exception.code)
