# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import os
import tempfile
import unittest
from unittest import mock

from app.backend import LocalFileDescriptorStore
from app.model import AssetAdministrationShellDescriptor, DictDescriptorStore

from ..adapter.descriptor_utils import example_aas_descriptor
from .support import run_module, write_registry_input

DEFAULT_ENV = dict({
    "STORAGE_PERSISTENCY": "false"
})

class RegistryEntrypointTest(unittest.TestCase):

    def test_loads_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            expected_ids = write_registry_input(input_dir)

            env = dict(DEFAULT_ENV)
            env["INPUT"] = input_dir
            with run_module("app.services.run_registry", env) as registry_run:
                storage = registry_run.application.object_store
                self.assertIsInstance(storage, DictDescriptorStore)
                self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})

    def test_missing_input_directory(self) -> None:
        with (tempfile.TemporaryDirectory() as input_dir):
            env = dict(DEFAULT_ENV)
            env["INPUT"] = os.path.join(input_dir, "non_existent")
            with self.assertLogs("app.services.run_registry", level="WARNING") as logs:
                with run_module("app.services.run_registry", env) as registry_run:
                    storage = registry_run.application.object_store
                    self.assertIsInstance(storage, DictDescriptorStore)
                    self.assertEqual(0, len(storage))

            self.assertTrue(any('non_existent" not found' in message for message in logs.output))

    def test_empty_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            env = dict(DEFAULT_ENV)
            env["INPUT"] = input_dir
            with run_module("app.services.run_registry", env) as registry_run:
                storage = registry_run.application.object_store
                self.assertIsInstance(storage, DictDescriptorStore)
                self.assertEqual(0, len(storage))

    def test_defaults(self) -> None:
        with run_module("app.services.run_registry", DEFAULT_ENV) as mod:
            self.assertEqual("/input", mod.env_input)
            self.assertEqual("/storage", mod.env_storage)
            self.assertIsInstance(mod.storage_files, DictDescriptorStore)

    def test_first_run_creates_storage_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_registry_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")
            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "false"
            })
            with run_module("app.services.run_registry", env) as registry_run:
                storage = registry_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileDescriptorStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})

    def test_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_registry_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")

            # Add altered AAS descriptor to storage directory
            local_storage = LocalFileDescriptorStore(storage_dir)
            local_storage.check_directory(create=True)
            aasd = example_aas_descriptor("https://example.org/AASDescriptor")
            aasd.asset_type = "http://example.org/ChangedAssetType"
            local_storage.add(aasd)
            del local_storage

            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "false"
            })
            with run_module("app.services.run_registry", env) as registry_run:
                storage = registry_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileDescriptorStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})
            # Assert altered AAS descriptor is not overwritten
            retrieved_aasd = storage.get(aasd.id)
            if not isinstance(retrieved_aasd, AssetAdministrationShellDescriptor):
                self.fail("No AAS descriptor in synced storage!")
            self.assertEqual(aasd.asset_type, retrieved_aasd.asset_type)


    def test_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_registry_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")

            #Add altered AAS descriptor to storage directory
            local_storage = LocalFileDescriptorStore(storage_dir)
            local_storage.check_directory(create=True)
            aasd = example_aas_descriptor("https://example.org/AASDescriptor")
            aasd.asset_type = "http://example.org/ChangedAssetType"
            local_storage.add(aasd)
            del local_storage

            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "true"
            })
            with run_module("app.services.run_registry", env) as registry_run:
                storage = registry_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileDescriptorStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})
            # Assert altered AAS descriptor was overwritten
            retrieved_aasd = storage.get(aasd.id)
            if not isinstance(retrieved_aasd, AssetAdministrationShellDescriptor):
                self.fail("No AAS descriptor in synced storage!")
            self.assertNotEqual(aasd.asset_type, retrieved_aasd.asset_type)

    def test_base_path(self) -> None:
        env = dict({
            **DEFAULT_ENV,
            "API_BASE_PATH": "/custom-path"
        })
        with mock.patch("app.interfaces.registry.RegistryAPI", autospec=True) as app_mock:
            with run_module("app.services.run_registry", env):
                app_mock.assert_called_with(mock.ANY, base_path="/custom-path")

    def test_persistency_truthy_values_use_local_file_store(self) -> None:
        for value in ("1", "true", "yes", "True", "YES"):
            with self.subTest(value=value):
                with tempfile.TemporaryDirectory() as storage_dir:
                    env = {"STORAGE_PERSISTENCY": value, "STORAGE": storage_dir}
                    with run_module("app.services.run_registry", env) as mod:
                        self.assertIsInstance(mod.storage_files, LocalFileDescriptorStore)

    def test_persistency_falsy_or_unset_uses_dict_store(self) -> None:
        for value in (None, "false", "0", "no"):
            with self.subTest(value=value):
                env = {} if value is None else {"STORAGE_PERSISTENCY": value}
                with run_module("app.services.run_registry", env) as mod:
                    self.assertIsInstance(mod.storage_files, DictDescriptorStore)
