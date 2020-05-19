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
import os
import subprocess
import sys
import unittest
import aas.compliance_tool
import tempfile

from aas.adapter.json import read_aas_json_file
from aas.adapter.xml import read_aas_xml_file
from aas.examples.data import create_example
from aas.examples.data._helper import AASDataChecker

JSON_SCHEMA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'adapter', 'json', 'aasJSONSchema.json')
XML_SCHEMA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'adapter', 'xml', 'AAS.xsd')


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

        output = subprocess.run(
            [sys.executable, file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: s or schema requires a schema path.', str(output.stderr))

        # test deserialisation check
        output = subprocess.run([sys.executable, file_path, "d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, output.returncode)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output = subprocess.run(
            [sys.executable, file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json")],
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
        self.assertNotIn('ERROR', str(output.stdout))
        self.assertNotIn('INFO', str(output.stdout))

        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-v", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertNotIn('ERROR', str(output.stdout))
        self.assertIn('INFO', str(output.stdout))

        # test quite
        output = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-q"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    @unittest.skipUnless(os.path.exists(JSON_SCHEMA_FILE), "JSON Schema not found for validation")
    def test_json_schema(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-s", JSON_SCHEMA_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

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

    def test_json_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

    def test_json_file(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)

    @unittest.skipUnless(os.path.exists(XML_SCHEMA_FILE), "XML Schema not found for validation")
    def test_xml_schema(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "s", os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml",
             "-s", XML_SCHEMA_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

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

    def test_xml_example(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "e", os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

    def test_xml_file(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'cli.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        output: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, file_path, "f", os.path.join(test_file_path, "test_demo_full_example.xml"),
             os.path.join(test_file_path, "test_demo_full_example.xml"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)

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
