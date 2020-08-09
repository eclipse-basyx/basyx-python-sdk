from unittest import mock
import unittest

from aas.model import *
from .model import test_base


class BackendTest:
    def test_backend_commit_object(self):
        with mock.patch("aas.backends.Backend") as mock_backend:
            backends.register_backend("mockScheme", mock_backend)
            test_referable = test_base.ExampleReferable()
            test_referable.source = "mockScheme:x-test:test_referable"
            test_referable.commit()
            mock_backend.commit_object.assert_called()
            mock_backend.commit_object.assert_called_with(test_referable, test_referable, [])

    def test_backend_update_object(self):
        with mock.patch("aas.backends.Backend") as mock_backend:
            backends.register_backend("mockScheme", mock_backend)
            test_referable = test_base.ExampleReferable()
            test_referable.source = "mockScheme:x-test:test_referable"
            test_referable.update()
            mock_backend.update_object.assert_called_with(test_referable, test_referable, [])


class BackendsTest(unittest.TestCase):
    def test_backend_store(self):
        with mock.patch("aas.backends.Backend") as mock_backend:
            backends.register_backend("mockScheme", mock_backend)
            self.assertEqual(backends.get_backend("mockScheme:x-test:test_backend"), mock_backend)

            backends._backends_map = {}
            backends.register_backend("<this is totally a valid uri>", mock_backend)
            with self.assertRaises(ValueError) as cm:
                backends.get_backend("<this is totally a valid uri>")
            self.assertEqual("<this is totally a valid uri> is not a valid URL with URI scheme.", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
