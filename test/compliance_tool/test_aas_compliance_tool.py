# Copyright 2019 PyI40AAS Contributors
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
import unittest
import aas.compliance_tool
import tempfile

from aas.adapter.json import json_deserialization
from aas.examples.data import example_concept_description, create_example
from aas.examples.data._helper import AASDataChecker


class ComplianceToolTest(unittest.TestCase):
    def test_parse_args(self) -> None:
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'aas_compliance_tool.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        # test schema check
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "s"],
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test deserialisation check
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "d"], 
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test example check
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "e"],
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test file check
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "f"],
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: the following arguments are required: file_1', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: f or files requires two file path', str(output.stderr))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: one of the arguments --json --xml is required', str(output.stderr))

        # test verbose
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertNotIn('ERROR', str(output.stdout))
        self.assertNotIn('INFO', str(output.stdout))

        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-v", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertNotIn('ERROR', str(output.stdout))
        self.assertIn('INFO', str(output.stdout))

        # test quite
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json",
             "-q"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertEqual("b''", str(output.stdout))

        # test logfile
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json", "-l"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(output.returncode != 0)
        self.assertIn('error: argument -l/--logfile: expected one argument', str(output.stderr))

    def test_json(self):
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'aas_compliance_tool.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        # test schema check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test create example check
        file, filename = tempfile.mkstemp(suffix=".json")
        os.close(file)
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "c", filename, "--json"],
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        with open(filename, "r", encoding='utf-8-sig') as f:
            json_object_store = json_deserialization.read_json_aas_file(f, failsafe=False)
            data = create_example()
            checker = AASDataChecker(raise_immediately=True)
            checker.check_object_store(json_object_store, data)
        os.unlink(filename)

        # test deserialisation check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test example check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test file check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json"), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)

    @unittest.expectedFailure
    def test_xml(self):
        file_path = os.path.join(os.path.dirname(aas.compliance_tool.__file__), 'aas_compliance_tool.py')
        test_file_path = os.path.join(os.path.dirname(__file__), 'files')

        # test schema check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "s", os.path.join(test_file_path, "test_demo_full_example.json"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test create example check
        file, filename = tempfile.mkstemp(suffix=".json")
        os.close(file)
        output: subprocess.CalledProcessError = subprocess.run(["python3", file_path, "c", filename, "--xml"],
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Create example data', str(output.stdout))
        self.assertIn('SUCCESS:      Open file', str(output.stdout))
        self.assertIn('SUCCESS:      Write data to file', str(output.stdout))

        with open(filename, "r", encoding='utf-8-sig') as f:
            json_object_store = json_deserialization.read_json_aas_file(f, failsafe=False)
            data = create_example()
            checker = AASDataChecker(raise_immediately=True)
            checker.check_object_store(json_object_store, data)
        os.unlink(filename)

        # test deserialisation check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "d", os.path.join(test_file_path, "test_demo_full_example.json"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test example check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "e", os.path.join(test_file_path, "test_demo_full_example.json"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
        self.assertIn('SUCCESS:      Open file', str(output.stdout))

        # test file check
        output: subprocess.CalledProcessError = subprocess.run(
            ["python3", file_path, "f", os.path.join(test_file_path, "test_demo_full_example.json"),
             os.path.join(test_file_path, "test_demo_full_example.json"), "--xml"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, output.returncode)
