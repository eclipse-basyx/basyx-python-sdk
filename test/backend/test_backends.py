from unittest import mock
import unittest

from aas.backend import backends


class BackendsTest(unittest.TestCase):
    def test_backend_store(self):
        with mock.patch("aas.backend.backends.Backend") as mock_backend:
            backends.register_backend("mockScheme", mock_backend)
            self.assertEqual(backends.get_backend("mockScheme:x-test:test_backend"), mock_backend)

            backends.register_backend("<this is totally a valid uri>", mock_backend)
            with self.assertRaises(ValueError) as cm:
                backends.get_backend("<this is totally a valid uri>")
            self.assertEqual("<this is totally a valid uri> is not a valid URL with URI scheme.", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
