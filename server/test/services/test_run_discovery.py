# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import os
import tempfile
import unittest
from contextlib import contextmanager

from app.interfaces.discovery import DiscoveryStore
from basyx.aas.model import SpecificAssetId

from .support import run_module


@contextmanager
def _run_discovery(env):
    """
    Wraps :func:`~.support.run_module` for ``app.services.run_discovery``.

    That module registers a ``persist_store`` atexit hook on every (re)load, including the very first, unpatched
    import that ``run_module()`` itself performs. Since ``persist_store()`` reads ``storage_path``/``discovery_store``
    from the module's globals at call time rather than binding them when defined, resetting ``storage_path`` once
    this ``with`` block ends keeps any such leftover hook a no-op at real interpreter shutdown, instead of it trying
    to write into a temp directory the test has already cleaned up.
    """
    with run_module("app.services.run_discovery", env) as discovery_run:
        try:
            yield discovery_run
        finally:
            setattr(discovery_run, "storage_path", None)


class DiscoveryEntrypointTest(unittest.TestCase):
    def test_no_storage_path_starts_with_empty_in_memory_store(self) -> None:
        with _run_discovery({}) as discovery_run:
            store = discovery_run.application.persistent_store
            self.assertIsInstance(store, DiscoveryStore)
            self.assertEqual({}, store.aas_id_to_asset_ids)

    def test_loads_existing_storage_file_on_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = os.path.join(tmp_dir, "discovery_store.json")
            store = DiscoveryStore()
            store.add_specific_asset_ids_to_aas(
                "https://example.org/aas/1", [SpecificAssetId("globalAssetId", "urn:asset:1")]
            )
            store.to_file(storage_path)

            with _run_discovery({"storage_path": storage_path}) as discovery_run:
                loaded = discovery_run.application.persistent_store
                self.assertEqual(store.aas_id_to_asset_ids, loaded.aas_id_to_asset_ids)

    def test_creates_storage_file_and_missing_directories_if_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = os.path.join(tmp_dir, "nested", "discovery_store.json")

            with _run_discovery({"storage_path": storage_path}) as discovery_run:
                store = discovery_run.application.persistent_store
                self.assertIsInstance(store, DiscoveryStore)
                self.assertEqual({}, store.aas_id_to_asset_ids)

            self.assertTrue(os.path.exists(storage_path))
            self.assertEqual({}, DiscoveryStore.from_file(storage_path).aas_id_to_asset_ids)

    def test_persists_store_to_file_on_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = os.path.join(tmp_dir, "discovery_store.json")

            with _run_discovery({"storage_path": storage_path}) as discovery_run:
                discovery_run.discovery_store.add_specific_asset_ids_to_aas(
                    "https://example.org/aas/1", [SpecificAssetId("globalAssetId", "urn:asset:1")]
                )

                # Simulate the atexit hook firing on shutdown instead of actually exiting the interpreter.
                discovery_run.persist_store()

            reloaded = DiscoveryStore.from_file(storage_path)
            self.assertEqual(
                {"https://example.org/aas/1": {SpecificAssetId("globalAssetId", "urn:asset:1")}},
                reloaded.aas_id_to_asset_ids,
            )

    def test_persist_store_without_storage_path_is_a_no_op(self) -> None:
        with _run_discovery({}) as discovery_run:
            discovery_run.discovery_store.add_specific_asset_ids_to_aas(
                "https://example.org/aas/1", [SpecificAssetId("globalAssetId", "urn:asset:1")]
            )

            discovery_run.persist_store()  # must not raise despite the missing storage_path
