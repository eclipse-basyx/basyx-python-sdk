# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import concurrent.futures
import gc
import os.path
import shutil
import tempfile
import threading
from typing import Callable
from unittest import TestCase, mock

from basyx.aas.backend import local_file
from basyx.aas.examples.data.example_aas import *

store_path: str = os.path.dirname(__file__) + "/local_file_test_folder"
source_core: str = "file://localhost/{}/".format(store_path)


def run_threads(fns: list[Callable]):
    fn_futures: list[concurrent.futures.Future] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fns)) as executor:
        for fn in fns:
            fn_futures.append(executor.submit(fn))

    concurrent.futures.wait(fn_futures)
    for future in fn_futures:
        ex = future.exception()
        if ex is not None:
            raise ex


class DirectoryLockTest(TestCase):

    @mock.patch("basyx.aas.backend.local_file._fcntl", None)
    def test_non_fcntl_strict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir, strict_locking=True)

            with self.assertRaises(RuntimeError) as cm:
                lock.acquire()
            self.assertIn("fcntl unavailable", cm.exception.args[0])

    @mock.patch("basyx.aas.backend.local_file._fcntl", None)
    def test_non_fcntl_non_strict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir, strict_locking=False)

            with self.assertLogs(level="WARNING") as cm:
                lock.acquire()
            self.assertTrue(any("fcntl unavailable" in log for log in cm.output))

    def test_double_locking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir)
            lock.acquire()
            lock.acquire()

            with self.assertRaises(RuntimeError):
                lock2 = local_file.DirectoryLock(tmpdir)
                lock2.acquire()

    def test_releasing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir)
            lock.acquire()
            self.assertTrue(lock._is_locked_flag)
            lock.release()
            self.assertFalse(lock._is_locked_flag)

    def test_context_manager_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir)

            with self.assertRaises(RuntimeError) as cm:
                with lock.ensure_locked():
                    pass
        self.assertIn("is not locked", cm.exception.args[0])

    def test_context_manager_concurrency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir)
            lock.acquire()

            barrier = threading.Barrier(parties=3, timeout=5)

            def first():
                with lock.ensure_locked():
                    barrier.wait()
                    barrier.wait()

            def second():
                with lock.ensure_locked():
                    barrier.wait()
                    barrier.wait()

            def asserts():
                barrier.wait()
                self.assertEqual(2, lock._active_accesses)
                barrier.wait()
                lock.release()
                self.assertEqual(0, lock._active_accesses)

            run_threads([first, second, asserts])

    def test_context_manager_finish_before_release(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = local_file.DirectoryLock(tmpdir)
            lock.acquire()

            access_barrier = threading.Barrier(parties=2, timeout=5)
            release_barrier = threading.Barrier(parties=2, timeout=5)

            def access():
                with lock.ensure_locked():
                    access_barrier.wait()
                    access_barrier.wait()
                access_barrier.wait()

            def release():
                release_barrier.wait()
                lock.release()
                release_barrier.wait()

            def asserts():
                access_barrier.wait()
                self.assertTrue(lock._is_locked_flag)  # in ensure_locked()
                release_barrier.wait()
                self.assertTrue(lock._is_locked_flag)  # in ensure_locked(), release() started
                access_barrier.wait()
                access_barrier.wait()
                release_barrier.wait()
                self.assertFalse(lock._is_locked_flag)  # out of ensure_locked(), release() finished

            run_threads([access, release, asserts])


class LocalFileBackendTest(TestCase):
    def setUp(self) -> None:
        self.identifiable_store = local_file.LocalFileIdentifiableStore(store_path)
        self.identifiable_store.check_directory(create=True)

    def tearDown(self) -> None:
        try:
            self.identifiable_store.clear()
        finally:
            self.identifiable_store.close()
            shutil.rmtree(store_path)

    @mock.patch("basyx.aas.backend.local_file._fcntl", None)
    def test_fail_on_non_fcntl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError) as cm:
                local_file.LocalFileIdentifiableStore(tmpdir)

        self.assertIn("fcntl unavailable", cm.exception.args[0])

    def test_multi_instance_fail_on_init(self):
        # Create second store for same path and expect it to fail
        with self.assertRaises(RuntimeError) as cm:
            local_file.LocalFileIdentifiableStore(store_path)

        self.assertIn("is already in use", cm.exception.args[0])

    def test_multi_instance_fail_on_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "localdb")

            store1 = local_file.LocalFileIdentifiableStore(path)
            store2 = local_file.LocalFileIdentifiableStore(path)

            store1.check_directory(create=True)
            with self.assertRaises(RuntimeError) as cm:
                store2.check_directory()

            self.assertIn("is already in use", cm.exception.args[0])

    def test_dir_lock_fail_add(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "localdb")
            store = local_file.LocalFileIdentifiableStore(path)
            # store did not acquire dir_lock as path does not exist yet

            with self.assertRaises(RuntimeError) as cm:
                store.add(create_example_submodel())

            self.assertIn("is not locked", cm.exception.args[0])

    def test_identifiable_store_add(self):
        test_object = create_example_submodel()
        self.identifiable_store.add(test_object)
        # Note that this test is only checking that there are no errors during adding.
        # The actual logic is tested together with retrieval in `test_retrieval`.

    def test_retrieval(self):
        test_object = create_example_submodel()
        self.identifiable_store.add(test_object)

        # When retrieving the object, we should get the *same* instance as we added
        test_object_retrieved = self.identifiable_store.get_item(
            "https://example.org/Test_Submodel"
        )
        self.assertIs(test_object, test_object_retrieved)

        # When retrieving it again, we should still get the same object
        del test_object
        test_object_retrieved_again = self.identifiable_store.get_item(
            "https://example.org/Test_Submodel"
        )
        self.assertIs(test_object_retrieved, test_object_retrieved_again)

    def test_example_submodel_storing(self) -> None:
        example_submodel = create_example_submodel()

        # Add exmaple submodel
        self.identifiable_store.add(example_submodel)
        self.assertEqual(1, len(self.identifiable_store))
        self.assertIn(example_submodel, self.identifiable_store)

        # Restore example submodel and check data
        submodel_restored = self.identifiable_store.get_item(
            "https://example.org/Test_Submodel"
        )
        assert isinstance(submodel_restored, model.Submodel)
        checker = AASDataChecker(raise_immediately=True)
        check_example_submodel(checker, submodel_restored)

        # Delete example submodel
        self.identifiable_store.discard(submodel_restored)
        self.assertNotIn(example_submodel, self.identifiable_store)

    def test_check_directory(self) -> None:
        # Make sure the test directory does not exist at the beginning of the test
        if os.path.exists(store_path):
            shutil.rmtree(store_path)

        # If create=False, check_directory should raise a FileNotFoundError,
        # if the directory does not exist
        with self.assertRaises(FileNotFoundError) as cm:
            self.identifiable_store.check_directory(create=False)
        expected_error = "The given directory ({}) does not exist".format(store_path)
        self.assertEqual(expected_error, str(cm.exception))

        # If create=True, check_directory should create the directory if it does not exist
        self.identifiable_store.check_directory(create=True)
        self.assertTrue(os.path.exists(store_path))

        # If the directory exists, create=False should not raise an error
        self.identifiable_store.check_directory(create=False)

    def test_iterating(self) -> None:
        example_data = create_full_example()

        # Add all objects
        for item in example_data:
            self.identifiable_store.add(item)

        self.assertEqual(5, len(self.identifiable_store))

        # Iterate objects, add them to a DictIdentifiableStore and check them
        retrieved_data_store: model.provider.DictIdentifiableStore[
            model.Identifiable
        ] = model.provider.DictIdentifiableStore()
        for item in self.identifiable_store:
            retrieved_data_store.add(item)
        checker = AASDataChecker(raise_immediately=True)
        check_full_example(checker, retrieved_data_store)

    def test_key_errors(self) -> None:
        # Double adding an object should raise a KeyError
        example_submodel = create_example_submodel()
        self.identifiable_store.add(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.add(example_submodel)
        self.assertEqual(
            "'Identifiable with id https://example.org/Test_Submodel already exists in "
            "local file database'",
            str(cm.exception),
        )

        # Querying a deleted object should raise a KeyError
        retrieved_submodel = self.identifiable_store.get_item(
            "https://example.org/Test_Submodel"
        )
        self.identifiable_store.discard(example_submodel)
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.get_item("https://example.org/Test_Submodel")
        self.assertEqual(
            "'No Identifiable with id https://example.org/Test_Submodel "
            "found in local file database'",
            str(cm.exception),
        )

        # Double deleting should also raise a KeyError
        with self.assertRaises(KeyError) as cm:
            self.identifiable_store.discard(retrieved_submodel)
        self.assertEqual(
            "'No AAS object with id https://example.org/Test_Submodel exists in "
            "local file database'",
            str(cm.exception),
        )

    def test_add_and_len_consistent(self) -> None:
        # Each add() must increment len() by exactly 1
        example_data = list(create_full_example())
        for i, item in enumerate(example_data):
            self.identifiable_store.add(item)
            self.assertEqual(i + 1, len(self.identifiable_store))

        # Stray non-json file must not be counted
        stray = os.path.join(store_path, ".DS_Store")
        with open(stray, "w") as f:
            f.write("stray")
        self.assertEqual(len(example_data), len(self.identifiable_store))
        os.remove(stray)

    def test_iter_ignores_non_json_files(self) -> None:
        example_data = create_full_example()
        for item in example_data:
            self.identifiable_store.add(item)

        # Stray files must not crash the iterator or be yielded
        stray = os.path.join(store_path, ".DS_Store")
        with open(stray, "w") as f:
            f.write("stray")
        items = list(self.identifiable_store)
        self.assertEqual(5, len(items))
        os.remove(stray)

    def test_mutation_persistence(self) -> None:
        submodel = model.Submodel(
            id_="https://example.org/MutationTest",
            submodel_element={
                model.Property(
                    id_short="Prop", value_type=model.datatypes.String, value="before"
                )
            },
        )
        self.identifiable_store.add(submodel)

        retrieved = self.identifiable_store.get_item("https://example.org/MutationTest")
        assert isinstance(retrieved, model.Submodel)
        prop = retrieved.get_referable(["Prop"])
        assert isinstance(prop, model.Property)
        prop.update_from(
            model.Property(
                id_short="Prop", value_type=model.datatypes.String, value="after"
            )
        )
        self.identifiable_store.commit(retrieved)

        # Drop all strong references to evict the WeakValueDictionary cache
        del submodel, retrieved, prop
        gc.collect()

        fresh = self.identifiable_store.get_item("https://example.org/MutationTest")
        assert isinstance(fresh, model.Submodel)
        fresh_prop = fresh.get_referable(["Prop"])
        assert isinstance(fresh_prop, model.Property)
        self.assertEqual("after", fresh_prop.value)

    def test_reload_discard(self) -> None:
        # Load example submodel
        example_submodel = create_example_submodel()
        self.identifiable_store.add(example_submodel)

        # Reload the store: release the existing lock before opening a new instance
        self.identifiable_store.close()
        self.identifiable_store = local_file.LocalFileIdentifiableStore(store_path)
        self.identifiable_store.discard(example_submodel)
        self.assertNotIn(example_submodel, self.identifiable_store)


class _GatedLocalFileStore(local_file.LocalFileIdentifiableStore):
    """
    Patch :meth:`_write_atomic()` to control and enforce concurrent writes.
    """

    def __init__(self, directory_path: str, *args, **kwargs):
        super().__init__(directory_path)
        self._gate = threading.Event()  # gate to run _write_atomic()
        self._gate.set()
        self._inside = threading.Event()  # signal _write_atomic() entry

    def _write_atomic(self, x: model.Identifiable) -> None:
        self._inside.set()
        self._gate.wait(timeout=5)
        super()._write_atomic(x)


class LocalFileBackendConcurrencyTest(TestCase):
    def setUp(self):
        self.store = _GatedLocalFileStore(store_path)
        self.store.check_directory(create=True)

    def tearDown(self):
        try:
            self.store.clear()
        finally:
            self.store.close()
            shutil.rmtree(store_path)

    def _example_submodels(self) -> tuple[model.Submodel, model.Submodel]:
        first_submodel = model.Submodel(
            id_='https://example.org/BackendTest',
            submodel_element={
                model.Property(id_short='Prop', value_type=model.datatypes.String, value='first')
            }
        )

        second_submodel = model.Submodel(
            id_='https://example.org/BackendTest',
            submodel_element={
                model.Property(id_short='Prop', value_type=model.datatypes.String, value='second')
            }
        )

        return first_submodel, second_submodel

    def test_concurrent_add(self):
        """Checks that second add for same ID fails"""
        first_submodel, second_submodel = self._example_submodels()

        self.store._gate.clear()
        self.store._inside.clear()
        barrier = threading.Barrier(2, timeout=5)
        all_done = threading.Barrier(3, timeout=5)

        def first():
            self.store.add(first_submodel)
            all_done.wait()

        def second():
            self.store._inside.wait()
            barrier.wait()
            with self.assertRaises(KeyError) as ex:
                self.store.add(second_submodel)

            all_done.wait()
            self.assertIn("already exists", ex.exception.args[0])

        def control():
            self.store._inside.wait()
            barrier.wait()
            self.store._gate.set()

            all_done.wait()
            submodel = self.store.get_item("https://example.org/BackendTest")
            self.assertIsInstance(submodel, model.Submodel)
            sm_property = submodel.get_referable("Prop")
            self.assertIsInstance(sm_property, model.Property)
            self.assertEqual(sm_property.value, "first")

        run_threads([first, second, control])

    def test_concurrent_commit_discard(self):
        """Checks that discard is not overwritten by concurrent commit"""
        submodel, altered_submodel = self._example_submodels()
        self.store.add(submodel)

        self.store._gate.clear()
        self.store._inside.clear()
        barrier = threading.Barrier(2, timeout=5)
        all_done = threading.Barrier(3, timeout=5)

        def first():
            self.store.commit(submodel)
            all_done.wait()

        def second():
            self.store._inside.wait()
            barrier.wait()
            self.store.discard(submodel)
            all_done.wait()

        def control():
            self.store._inside.wait()
            barrier.wait()
            self.store._gate.set()

            all_done.wait()
            with self.assertRaises(KeyError) as ex:
                self.store.get_item("https://example.org/BackendTest")

            self.assertIn("No Identifiable", ex.exception.args[0])

        run_threads([first, second, control])
