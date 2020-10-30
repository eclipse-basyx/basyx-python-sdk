# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import datetime
import hashlib
import io
import os
import tempfile
import unittest
import warnings

import pyecma376_2
from aas import model
from aas.adapter import aasx
from aas.examples.data import example_aas, _helper, example_aas_mandatory_attributes


class TestAASXUtils(unittest.TestCase):
    def test_name_friendlyfier(self) -> None:
        friendlyfier = aasx.NameFriendlyfier()
        name1 = friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS-a", model.IdentifierType.IRI))
        self.assertEqual("http___example_com_AAS_a", name1)
        name2 = friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS+a", model.IdentifierType.IRI))
        self.assertEqual("http___example_com_AAS_a_1", name2)

    def test_supplementary_file_container(self) -> None:
        container = aasx.DictSupplementaryFileContainer()
        with open(os.path.join(os.path.dirname(__file__), 'TestFile.pdf'), 'rb') as f:
            new_name = container.add_file("/TestFile.pdf", f, "application/pdf")
            # Name should not be modified, since there is no conflict
            self.assertEqual("/TestFile.pdf", new_name)
            f.seek(0)
            container.add_file("/TestFile.pdf", f, "application/pdf")
        # Name should not be modified, since there is still no conflict
        self.assertEqual("/TestFile.pdf", new_name)

        with open(__file__, 'rb') as f:
            new_name = container.add_file("/TestFile.pdf", f, "application/pdf")
        # Now, we have a conflict
        self.assertNotEqual("/TestFile.pdf", new_name)
        self.assertIn(new_name, container)

        # Check metadata
        self.assertEqual("application/pdf", container.get_content_type("/TestFile.pdf"))
        self.assertEqual("b18229b24a4ee92c6c2b6bc6a8018563b17472f1150d35d5a5945afeb447ed44",
                         container.get_sha256("/TestFile.pdf").hex())
        self.assertIn("/TestFile.pdf", container)

        # Check contents
        file_content = io.BytesIO()
        container.write_file("/TestFile.pdf", file_content)
        self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(), "78450a66f59d74c073bf6858db340090ea72a8b1")


class AASXWriterTest(unittest.TestCase):
    def test_writing_reading_example_aas(self) -> None:
        # Create example data and file_store
        data = example_aas.create_full_example()
        files = aasx.DictSupplementaryFileContainer()
        with open(os.path.join(os.path.dirname(__file__), 'TestFile.pdf'), 'rb') as f:
            files.add_file("/TestFile.pdf", f, "application/pdf")
            f.seek(0)

        # Create OPC/AASX core properties
        cp = pyecma376_2.OPCCoreProperties()
        cp.created = datetime.datetime.now()
        cp.creator = "PyI40AAS Testing Framework"

        # Write AASX file
        for write_json in (False, True):
            for submodel_split_parts in (False, True):
                with self.subTest(write_json=write_json, submodel_split_parts=submodel_split_parts):
                    fd, filename = tempfile.mkstemp(suffix=".aasx")
                    os.close(fd)

                    # Write AASX file
                    # the zipfile library reports errors as UserWarnings via the warnings library. Let's check for
                    # warnings
                    with warnings.catch_warnings(record=True) as w:
                        with aasx.AASXWriter(filename) as writer:
                            writer.write_aas(model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell',
                                                              id_type=model.IdentifierType.IRI),
                                             data, files, write_json=write_json,
                                             submodel_split_parts=submodel_split_parts)
                            writer.write_core_properties(cp)

                    assert isinstance(w, list)  # This should be True due to the record=True parameter
                    self.assertEqual(0, len(w), f"Warnings were issued while writhing the AASX file: "
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
                    assert(isinstance(cp.created, datetime.datetime))  # to make mypy happy
                    self.assertIsInstance(new_cp.created, datetime.datetime)
                    assert(isinstance(new_cp.created, datetime.datetime))  # to make mypy happy
                    self.assertAlmostEqual(new_cp.created, cp.created, delta=datetime.timedelta(milliseconds=20))
                    self.assertEqual(new_cp.creator, "PyI40AAS Testing Framework")
                    self.assertIsNone(new_cp.lastModifiedBy)

                    # Check files
                    self.assertEqual(new_files.get_content_type("/TestFile.pdf"), "application/pdf")
                    file_content = io.BytesIO()
                    new_files.write_file("/TestFile.pdf", file_content)
                    self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(),
                                     "78450a66f59d74c073bf6858db340090ea72a8b1")

                    os.unlink(filename)

    def test_writing_reading_objects_single_part(self) -> None:
        # Create example data and file_store
        data = example_aas_mandatory_attributes.create_full_example()
        files = aasx.DictSupplementaryFileContainer()

        # Write AASX file
        for write_json in (False, True):
            with self.subTest(write_json=write_json):
                fd, filename = tempfile.mkstemp(suffix=".aasx")
                os.close(fd)
                with aasx.AASXWriter(filename) as writer:
                    writer.write_aas_objects('/aasx/aasx.{}'.format('json' if write_json else 'xml'),
                                             [obj.identification for obj in data],
                                             data, files, write_json)

                # Read AASX file
                new_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
                new_files = aasx.DictSupplementaryFileContainer()
                with aasx.AASXReader(filename) as reader:
                    reader.read_into(new_data, new_files)

                # Check AAS objects
                checker = _helper.AASDataChecker(raise_immediately=True)
                example_aas_mandatory_attributes.check_full_example(checker, new_data)

                os.unlink(filename)
