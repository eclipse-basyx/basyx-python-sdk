# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0

from typing import List
import unittest

from aas.backend import backends
from aas.model import Referable


class ExampleBackend(backends.Backend):
    @classmethod
    def commit_object(cls, committed_object: Referable, store_object: Referable, relative_path: List[str]) -> None:
        raise NotImplementedError("This is a mock")

    @classmethod
    def update_object(cls, updated_object: Referable, store_object: Referable, relative_path: List[str]) -> None:
        raise NotImplementedError("This is a mock")


class BackendsTest(unittest.TestCase):
    def test_backend_store(self):
        backends.register_backend("mockScheme", ExampleBackend)
        self.assertIs(backends.get_backend("mockScheme:x-test:test_backend"), ExampleBackend)

        backends.register_backend("<this is totally a valid uri>", ExampleBackend)
        with self.assertRaises(ValueError) as cm:
            backends.get_backend("<this is totally a valid uri>")
        self.assertEqual("<this is totally a valid uri> is not a valid URL with URI scheme.", str(cm.exception))

        with self.assertRaises(backends.UnknownBackendException):
            backends.get_backend("some-unkown-scheme://example.com")
