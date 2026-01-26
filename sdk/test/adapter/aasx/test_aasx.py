# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import datetime
import hashlib
import io
import os
import tempfile
import unittest
import warnings

import pyecma376_2
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.examples.data import example_aas, example_aas_mandatory_attributes, _helper


class TestAASXUtils(unittest.TestCase):
    def test_supplementary_file_container(self) -> None:
        container = aasx.DictSupplementaryFileContainer()
        with open(os.path.join(os.path.dirname(__file__), 'TestFile.pdf'), 'rb') as f:
            saved_file_name = container.add_file("/TestFile.pdf", f, "application/pdf")
            # Name should not be modified, since there is no conflict
            self.assertEqual("/TestFile.pdf", saved_file_name)
            f.seek(0)
            # Add the same file again with the same name
            same_file_with_same_name = container.add_file("/TestFile.pdf", f, "application/pdf")
        # Name should not be modified, since there is still no conflict
        self.assertEqual("/TestFile.pdf", same_file_with_same_name)

        # Add other file with the same name to create a conflict
        with open(__file__, 'rb') as f:
            saved_file_name_2 = container.add_file("/TestFile.pdf", f, "application/pdf")
        # Now, we have a conflict
        self.assertNotEqual(saved_file_name, saved_file_name_2)
        self.assertIn(saved_file_name_2, container)

        # Rename file to a new unique name
        renamed = container.rename_file(saved_file_name_2, "/RenamedTestFile.pdf")
        self.assertIn(renamed, container)
        # Old name should no longer exist
        self.assertNotIn(saved_file_name_2, container)
        self.assertEqual(renamed, "/RenamedTestFile.pdf")

        # Renaming to the same name should be no-op
        renamed_same = container.rename_file(renamed, renamed)
        self.assertEqual(renamed, renamed_same)

        # Renaming to an existing name should create a conflict
        renamed_conflict = container.rename_file(renamed, "/TestFile.pdf")
        self.assertNotEqual(renamed_conflict, "/TestFile.pdf")
        self.assertIn(renamed_conflict, container)

        # Renaming a non-existing file should raise KeyError
        with self.assertRaises(KeyError):
            container.rename_file("/NonExistingFile.pdf", "/AnotherName.pdf")

        new_name = renamed_conflict

        # Check metadata
        self.assertEqual("application/pdf", container.get_content_type("/TestFile.pdf"))
        self.assertEqual("b18229b24a4ee92c6c2b6bc6a8018563b17472f1150d35d5a5945afeb447ed44",
                         container.get_sha256("/TestFile.pdf").hex())
        self.assertIn("/TestFile.pdf", container)

        # Check contents
        file_content = io.BytesIO()
        container.write_file("/TestFile.pdf", file_content)
        self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(), "78450a66f59d74c073bf6858db340090ea72a8b1")

        # Add same file again with different content_type to test reference counting
        with open(__file__, 'rb') as f:
            duplicate_file = container.add_file("/TestFile.pdf", f, "image/jpeg")
        self.assertIn(duplicate_file, container)

        # Delete files
        container.delete_file(new_name)
        self.assertNotIn(new_name, container)
        # File should still be accessible
        container.write_file(duplicate_file, file_content)

        container.delete_file(duplicate_file)
        self.assertNotIn(duplicate_file, container)
        # File should now not be accessible anymore
        with self.assertRaises(KeyError):
            container.write_file(duplicate_file, file_content)


class AASXWriterTest(unittest.TestCase):
    def test_writing_reading_example_aas(self) -> None:
        # Create example data and file_store
        data = example_aas.create_full_example()    # creates a complete, valid example AAS
        files = aasx.DictSupplementaryFileContainer()   # in-memory store for attached files
        with open(os.path.join(os.path.dirname(__file__), 'TestFile.pdf'), 'rb') as f:
            files.add_file("/TestFile.pdf", f, "application/pdf")   # add a real supplementary pdf file
            f.seek(0)
        # Create OPC/AASX core properties
        # create AASX metadata (core properties)
        cp = pyecma376_2.OPCCoreProperties()
        cp.created = datetime.datetime.now()
        cp.creator = "Eclipse BaSyx Python Testing Framework"

        # Write AASX file
        for write_json in (False, True):    # Loop over both XML and JSON modes
            with self.subTest(write_json=write_json):
                fd, filename = tempfile.mkstemp(suffix=".aasx")     # create temporary file
                os.close(fd)    # close file descriptor

                # Write AASX file
                # the zipfile library reports errors as UserWarnings via the warnings library. Let's check for
                # warnings
                with warnings.catch_warnings(record=True) as w:
                    with aasx.AASXWriter(filename) as writer:
                        # TODO test writing multiple AAS
                        writer.write_aas('https://acplt.org/Test_AssetAdministrationShell',
                                         data, files, write_json=write_json)
                        writer.write_core_properties(cp)

                assert isinstance(w, list)  # This should be True due to the record=True parameter
                self.assertEqual(0, len(w), f"Warnings were issued while writing the AASX file: "
                                            f"{[warning.message for warning in w]}")

                # Read AASX file
                new_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
                new_files = aasx.DictSupplementaryFileContainer()
                with aasx.AASXReader(filename) as reader:
                    reader.read_into(new_data, new_files)
                    new_cp = reader.get_core_properties()

                # Check AAS objects
                checker = _helper.AASDataChecker(raise_immediately=True)
                example_aas.check_full_example(checker, new_data)

                # Check core properties
                assert isinstance(cp.created, datetime.datetime)  # to make mypy happy
                self.assertIsInstance(new_cp.created, datetime.datetime)
                assert isinstance(new_cp.created, datetime.datetime)  # to make mypy happy
                self.assertAlmostEqual(new_cp.created, cp.created, delta=datetime.timedelta(milliseconds=20))
                self.assertEqual(new_cp.creator, "Eclipse BaSyx Python Testing Framework")
                self.assertIsNone(new_cp.lastModifiedBy)

                # Check files
                self.assertEqual(new_files.get_content_type("/TestFile.pdf"), "application/pdf")
                file_content = io.BytesIO()
                new_files.write_file("/TestFile.pdf", file_content)
                self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(),
                                 "78450a66f59d74c073bf6858db340090ea72a8b1")

                os.unlink(filename)


class AASXReaderTest(unittest.TestCase):
    def _create_test_aasx(self) -> str:
        data = example_aas.create_full_example()
        files = aasx.DictSupplementaryFileContainer()

        with open(os.path.join(os.path.dirname(__file__), 'TestFile.pdf'), 'rb') as f:
            files.add_file("/TestFile.pdf", f, "application/pdf")
            f.seek(0)

        # Core properties
        cp = pyecma376_2.OPCCoreProperties()
        cp.created = datetime.datetime.now()
        cp.creator = "Eclipse BaSyx Python Testing Framework"

        fd, filename = tempfile.mkstemp(suffix=".aasx")
        os.close(fd)

        with aasx.AASXWriter(filename) as writer:
            writer.write_aas(
                'https://acplt.org/Test_AssetAdministrationShell',
                data, files, write_json=False
            )
            writer.write_core_properties(cp)

        return filename

    def test_init_file_handling(self) -> None:
        # Missing file assertion test
        with self.assertRaises(FileNotFoundError):
            aasx.AASXReader("does_not_exist.aasx")

        # Invalid file assertion test
        fd, invalid_path = tempfile.mkstemp()
        os.write(fd, b"not a file")
        os.close(fd)

        try:
            with self.assertRaises(ValueError):
                aasx.AASXReader(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_reading_core_properties(self) -> None:
        filename = self._create_test_aasx()

        try:
            with aasx.AASXReader(filename) as reader:
                cp = reader.get_core_properties()

            self.assertIsInstance(cp.created, datetime.datetime)
            self.assertEqual(cp.creator, "Eclipse BaSyx Python Testing Framework")
            self.assertIsNone(cp.lastModifiedBy)
        finally:
            os.unlink(filename)

    def test_read_into(self) -> None:
        filename = self._create_test_aasx()

        try:
            objects: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
            files = aasx.DictSupplementaryFileContainer()

            with warnings.catch_warnings(record=True) as w:
                with aasx.AASXReader(filename) as reader:
                    ids = reader.read_into(objects, files)

            assert isinstance(w, list)
            self.assertEqual(0, len(w))     # Ensure no warnings were raised

            self.assertGreater(len(ids), 0)     # Ensure at least one AAS was read
            self.assertGreater(len(objects), 0)     # Ensure objects were populated
            self.assertGreater(len(files), 0)
            self.assertEqual(
                files.get_content_type("/TestFile.pdf"),
                "application/pdf"
            )
        finally:
            os.unlink(filename)

    def test_supplementary_file_integrity(self) -> None:
        filename = self._create_test_aasx()

        try:
            objects: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
            files = aasx.DictSupplementaryFileContainer()

            with aasx.AASXReader(filename) as reader:
                reader.read_into(objects, files)

            buf = io.BytesIO()
            files.write_file("/TestFile.pdf", buf)

            self.assertEqual(
                hashlib.sha1(buf.getvalue()).hexdigest(),
                "78450a66f59d74c073bf6858db340090ea72a8b1"
            )
        finally:
            os.unlink(filename)


class AASXWriterReferencedSubmodelsTest(unittest.TestCase):

    def test_only_referenced_submodels(self):
        """
        Test that verifies that all Submodels (referenced and unreferenced) are written to the AASX package when using
        the convenience function write_all_aas_objects().
        When calling the higher-level function write_aas(), however, only
        referenced Submodels in the ObjectStore should be included.
        """
        # Create referenced and unreferenced Submodels
        referenced_submodel = model.Submodel(id_="ref_submodel")
        unreferenced_submodel = model.Submodel(id_="unref_submodel")

        aas = model.AssetAdministrationShell(
            id_="Test_AAS",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id="http://acplt.org/Test_Asset"
            ),
            submodel={model.ModelReference.from_referable(referenced_submodel)}
        )

        # ObjectStore containing all objects
        object_store = model.DictObjectStore([aas, referenced_submodel, unreferenced_submodel])

        # Empty SupplementaryFileContainer (no files needed)
        file_store = aasx.DictSupplementaryFileContainer()

        # --- Step 1: Check write_aas() behavior ---
        for write_json in (False, True):
            with self.subTest(method="write_aas", write_json=write_json):
                fd, filename = tempfile.mkstemp(suffix=".aasx")
                os.close(fd)

                with warnings.catch_warnings(record=True) as w:
                    with aasx.AASXWriter(filename) as writer:
                        # write_aas only takes the AAS id and ObjectStore
                        writer.write_aas(
                            aas_ids=[aas.id],
                            object_store=object_store,
                            file_store=file_store,
                            write_json=write_json
                        )

                # Read back
                new_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
                new_files = aasx.DictSupplementaryFileContainer()
                with aasx.AASXReader(filename) as reader:
                    reader.read_into(new_data, new_files)

                # Assertions
                self.assertIn(referenced_submodel.id, new_data)     # referenced Submodel is included
                self.assertNotIn(unreferenced_submodel.id, new_data)  # unreferenced Submodel is excluded

                os.unlink(filename)

        # --- Step 2: Check write_all_aas_objects ---
        for write_json in (False, True):
            with self.subTest(method="write_all_aas_objects", write_json=write_json):
                fd, filename = tempfile.mkstemp(suffix=".aasx")
                os.close(fd)

                with warnings.catch_warnings(record=True) as w:
                    with aasx.AASXWriter(filename) as writer:
                        writer.write_all_aas_objects(
                            part_name="/aasx/my_aas_part.xml",
                            objects=object_store,
                            file_store=file_store,
                            write_json=write_json
                        )

                # Read back
                new_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
                new_files = aasx.DictSupplementaryFileContainer()
                with aasx.AASXReader(filename) as reader:
                    reader.read_into(new_data, new_files)

                # Assertions
                self.assertIn(referenced_submodel.id, new_data)
                self.assertIn(unreferenced_submodel.id, new_data)  # all objects are written
                os.unlink(filename)
