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
import os
import subprocess
import sys
import unittest
import io

import pyecma376_2

import aas.compliance_tool
import tempfile

from aas import model
from aas.adapter import aasx
from aas.adapter.json import read_aas_json_file, JSON_SCHEMA_FILE
from aas.adapter.xml import read_aas_xml_file, XML_SCHEMA_FILE
from aas.examples.data import create_example, create_example_aas_binding
from aas.examples.data._helper import AASDataChecker


class ComplianceToolTest(unittest.TestCase):
    def test_parse_args(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        # test schema check
        output: subprocess.CompletedProcess = subprocess.run([sys.executable, file_path, "s"],
                                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test deserialisation check
        output = subprocess.run([sys.executable, file_path, "d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json"), "--aasx"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test example check
        output = subprocess.run([sys.executable, file_path, "e"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--aasx"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test file check
        output = subprocess.run([sys.executable, file_path, "f"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"), "--aasx"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: f or files requires two file path', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test verbose
        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertNotIn('ERROR', str(output.stderr))
        self.assertNotIn('INFO', str(output.stdout))

        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-v", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertNotIn('ERROR', str(output.stderr))
        self.assertIn('INFO', str(output.stdout))

        # test quite
        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertEqual("b''", str(output.stdout))

        # test logfile
        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-l"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: argument -l/--logfile: expected one argument', str(output.stderr))

        # todo: add test for correct logfile

    def test_json_create_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')

        file, filename = tempfile.mkstemp(suffix=".json")
        os.close(file)
        output: subprocess.CompletedProcess = subprocess.run([sys.executable, file_path, "c", filename, "--json"],
                                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        with open(filename, "r", encoding='utf-8-sig') as f:
            json_object_store = read_aas_json_file(f, failsafe=False)
            data = create_example()
            checker = AASDataChecker(raise_immediately=True)
            checker.check_object_store(json_object_store, data)
        os.unlink(filename)

    def test_json_deserialization(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file and check if it is deserializable', str(output.stdout))

    def test_json_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file and check if it is deserializable', str(output.stdout))
        self.assertIn('SUCCESS:      Check if data is equal to example data', str(output.stdout))

    def test_json_file(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open first file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Open second file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Check if data in files are equal', str(output.stdout))

    def test_xml_create_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')

        file, filename = tempfile.mkstemp(suffix=".xml")
        os.close(file)
        output: subprocess.CompletedProcess = subprocess.run([sys.executable, file_path, "c", filename, "--xml"],
                                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        with open(filename, "rb") as f:
            xml_object_store = read_aas_xml_file(f, failsafe=False)
            data = create_example()
            checker = AASDataChecker(raise_immediately=True)
            checker.check_object_store(xml_object_store, data)
        os.unlink(filename)

    def test_xml_deseralization(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file and check if it is deserializable', str(output.stdout))

    def test_xml_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file and check if it is deserializable', str(output.stdout))
        self.assertIn('SUCCESS:      Check if data is equal to example data', str(output.stdout))

    def test_xml_file(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.xml"),
             os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open first file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Open second file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Check if data in files are equal', str(output.stdout))

    def test_aasx_create_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')

        file, filename = tempfile.mkstemp(suffix=".aasx")
        os.close(file)
        output: subprocess.CompletedProcess = subprocess.run([sys.executable, file_path, "c", filename, "--xml",
                                                              "--aasx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        # Read AASX file
        new_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        new_files = aasx.DictSupplementaryFileContainer()
        with aasx.AASXReader(filename) as reader:
            reader.read_into(new_data, new_files)
            new_cp = reader.get_core_properties()

        # Check AAS objects
        assert (isinstance(new_cp.created, datetime.datetime))
        self.assertIsInstance(new_cp.created, datetime.datetime)
        self.assertAlmostEqual(new_cp.created, datetime.datetime(2020, 1, 1, 0, 0, 0),
                               delta=datetime.timedelta(milliseconds=20))
        self.assertEqual(new_cp.creator, "PyI40AAS Testing Framework")
        self.assertEqual(new_cp.description, "Test_Description")
        self.assertEqual(new_cp.lastModifiedBy, "PyI40AAS Testing Framework Compliance Tool")
        assert (isinstance(new_cp.modified, datetime.datetime))
        self.assertAlmostEqual(new_cp.modified, datetime.datetime(2020, 1, 1, 0, 0, 1),
                               delta=datetime.timedelta(milliseconds=20))
        self.assertEqual(new_cp.revision, "1.0")
        self.assertEqual(new_cp.version, "2.0.1")
        self.assertEqual(new_cp.title, "Test Title")

        # Check files
        self.assertEqual(new_files.get_content_type("/TestFile.pdf"), "application/pdf")
        file_content = io.BytesIO()
        new_files.write_file("/TestFile.pdf", file_content)
        self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(),
                         "78450a66f59d74c073bf6858db340090ea72a8b1")

        os.unlink(filename)

    def test_aasx_deseralization_xml(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example_xml.aasx"), "--xml",
             "--aasx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))

    def test_aasx_example_xml(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example_xml.aasx"), "--xml",
             "--aasx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        # self.assertIn('SUCCESS:      Check if data is equal to example data', str(output.stdout))

    def test_aasx_deseralization_json(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example_json.aasx"), "--json",
             "--aasx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))

    def test_aasx_example_json(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example_json.aasx"), "--json",
             "--aasx"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        # self.assertIn('SUCCESS:      Check if data is equal to example data', str(output.stdout))

    def test_aasx_file(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example_xml.aasx"),
             os.path.join(test_file_path, "test_demo_full_example_xml.aasx"), "--xml", "--aasx"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open first file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Open second file', str(output.stdout))
        self.assertIn('SUCCESS:      Read file', str(output.stdout))
        self.assertIn('SUCCESS:      Check if data in files are equal', str(output.stdout))

    def test_logfile(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        file, filename = tempfile.mkstemp(suffix=".json")
        file2, filename2 = tempfile.mkstemp(suffix=".log")
        os.close(file)
        os.close(file2)
        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "c", filename, "--json", "-v", "-v", "-l", filename2],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        with open(filename2, "r", encoding='utf-8-sig') as f:
            data = f.read()
            self.assertIn('SUCCESS:      Create example data', data)
            self.assertIn('SUCCESS:      Open file', data)
            self.assertIn('SUCCESS:      Write data to file', data)
        os.unlink(filename)
        os.unlink(filename2)
