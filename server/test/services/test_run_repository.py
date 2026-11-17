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

from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.backend.local_file import LocalFileIdentifiableStore
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_asset_administration_shell
from basyx.aas.model import AssetAdministrationShell
from basyx.aas.model.provider import DictIdentifiableStore

from .support import run_module, write_repository_input

DEFAULT_ENV = dict({
    "STORAGE_PERSISTENCY": "false"
})

class RepositoryEntrypointTest(unittest.TestCase):
    def test_loads_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            expected_ids = write_repository_input(input_dir)

            env = dict(DEFAULT_ENV)
            env["INPUT"] = input_dir
            with run_module("app.services.run_repository", env) as repo_run:
                storage = repo_run.application.object_store
                self.assertIsInstance(storage, DictIdentifiableStore)
                self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})

                self.assertIsInstance(repo_run.application.file_store, DictSupplementaryFileContainer)

    def test_missing_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            env = dict(DEFAULT_ENV)
            env["INPUT"] = os.path.join(input_dir, "non_existent")
            with self.assertLogs("app.services.run_repository", level="WARNING") as logs:
                with run_module("app.services.run_repository", env) as repo_run:
                    storage = repo_run.application.object_store
                    self.assertIsInstance(storage, DictIdentifiableStore)
                    self.assertEqual(0, len(storage))

            self.assertTrue(any("non_existent\" not found" in message for message in logs.output))

    def test_empty_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            env = dict(DEFAULT_ENV)
            env["INPUT"] = input_dir
            with run_module("app.services.run_repository", env) as repo_run:
                storage = repo_run.application.object_store
                self.assertIsInstance(storage, DictIdentifiableStore)
                self.assertEqual(0, len(storage))

    def test_defaults(self) -> None:
        with run_module("app.services.run_repository", DEFAULT_ENV) as mod:
            self.assertEqual("/input", mod.env_input)
            self.assertEqual("/storage", mod.env_storage)
            self.assertIsInstance(mod.storage_files, DictIdentifiableStore)

    def test_first_run_creates_storage_directory(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_repository_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")
            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "false"
            })
            with run_module("app.services.run_repository", env) as repo_run:
                storage = repo_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileIdentifiableStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})

    def test_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_repository_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")

            # Add altered AAS to storage directory
            local_storage = LocalFileIdentifiableStore(storage_dir)
            local_storage.check_directory(create=True)
            aas = create_example_asset_administration_shell()
            aas.asset_information.asset_type = "http://example.org/ChangedAssetType"
            local_storage.add(aas)
            del local_storage

            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "false"
            })
            with run_module("app.services.run_repository", env) as repo_run:
                storage = repo_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileIdentifiableStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})
            # Assert altered AAS is not overwritten
            retrieved_aas = storage.get(aas.id)
            if not isinstance(retrieved_aas, AssetAdministrationShell):
                self.fail("No AAS in synced storage!")
            self.assertEqual(aas.asset_information.asset_type, retrieved_aas.asset_information.asset_type)


    def test_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as tmp_dir:
            expected_ids = write_repository_input(input_dir)
            storage_dir = os.path.join(tmp_dir, "storage")

            # Add altered AAS to storage directory
            local_storage = LocalFileIdentifiableStore(storage_dir)
            local_storage.check_directory(create=True)
            aas = create_example_asset_administration_shell()
            aas.asset_information.asset_type = "http://example.org/ChangedAssetType"
            local_storage.add(aas)
            del local_storage

            env = dict({
                "INPUT": input_dir,
                "STORAGE": storage_dir,
                "STORAGE_PERSISTENCY": "true",
                "STORAGE_OVERWRITE": "true"
            })
            with run_module("app.services.run_repository", env) as repo_run:
                storage = repo_run.application.object_store

            self.assertTrue(os.path.isdir(storage_dir))
            if not isinstance(storage, LocalFileIdentifiableStore):
                self.fail("Storage is not persistent!")
            self.assertEqual(expected_ids, {identifiable.id for identifiable in storage})
            # Assert AAS was overwritten
            retrieved_aas = storage.get(aas.id)
            if not isinstance(retrieved_aas, AssetAdministrationShell):
                self.fail("No AAS in synced storage!")
            self.assertNotEqual(aas.asset_information.asset_type, retrieved_aas.asset_information.asset_type)

    def test_base_path(self) -> None:
        env = dict({
            **DEFAULT_ENV,
            "API_BASE_PATH": "/custom-path"
        })
        with mock.patch("app.interfaces.repository.WSGIApp", autospec=True) as app_mock:
            with run_module("app.services.run_repository", env):
                app_mock.assert_called_with(mock.ANY, mock.ANY, base_path="/custom-path")

    def test_persistency_truthy_values_use_local_file_store(self) -> None:
        for value in ("1", "true", "yes", "True", "YES"):
            with self.subTest(value=value):
                with tempfile.TemporaryDirectory() as storage_dir:
                    env = {"STORAGE_PERSISTENCY": value, "STORAGE": storage_dir}
                    with run_module("app.services.run_repository", env) as mod:
                        self.assertIsInstance(mod.storage_files, LocalFileIdentifiableStore)

    def test_persistency_falsy_or_unset_uses_dict_store(self) -> None:
        for value in (None, "false", "0", "no"):
            with self.subTest(value=value):
                env = {} if value is None else {"STORAGE_PERSISTENCY": value}
                with run_module("app.services.run_repository", env) as mod:
                    self.assertIsInstance(mod.storage_files, DictIdentifiableStore)
