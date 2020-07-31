from unittest import mock
import unittest

from aas import model, backends


class BackendTest:
    pass


class BackendsTest(unittest.TestCase):
    def test_mock_get_backend(self):
        with mock.patch("model.Referable.Backend") as mock_backend:
            with mock.patch("model.Referable.get_backend") as mock_get_backend:
                mock_get_backend.method.return_value = mock_backend
                test_referable = model.Referable()
                test_referable.source = "test_source"
                self.assertEqual(mock_backend, mock_get_backend(test_referable.source))
                # I know this tests how mock works and not how get_backend works, but I wanted to try this. This is
                # temporary.

    def test_backend_store(self):
        with mock.patch("model.Referable.Backend") as mock_backend:
            backends.register_backend("urn:x-test:test_backend", mock_backend)
            self.assertEqual(backends._backends_map["urn:x-test:test_backend"], mock_backend)
            self.assertEqual(backends.get_backend("urn:x-test:test_backend"), mock_backend)

            backends._backends_map = {}
            backends.register_backend("<this is totally a valid uri>", mock_backend)
            with self.assertRaises(ValueError) as cm:
                backends.get_backend("<this is totally a valid uri>")
            self.assertEqual("<this is totally a valid uri> is not a valid URL with URI scheme.", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
