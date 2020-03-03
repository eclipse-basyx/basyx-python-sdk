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
import re
import unittest

import aas.compliance_tool.json as compliance_tool
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status

dirname = os.path.dirname
JSON_SCHEMA_FILE = os.path.join(dirname(dirname(dirname(__file__))), 'test\\adapter\\json\\aasJSONSchemaV2.0.json')


class ComplianceToolJsonTest(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(JSON_SCHEMA_FILE), "JSON Schema not found for validation")
    def test_check_schema(self):
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.json')
        compliance_tool.check_schema(file_path_1, manager)
        self.assertEqual(len(manager.steps), 1)
        self.assertEqual(manager.steps[0][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(0)
        self.assertIsNotNone(re.search(r"No such file or directory", error_list[0].getMessage()))

        manager.steps = []
        file_path_2 = os.path.join(script_dir, 'files/test_not_serializable.json')
        compliance_tool.check_schema(file_path_2, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(1)
        self.assertEqual(error_list[0].getMessage(), "Expecting ',' delimiter: line 5 column 2 (char 69)")

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_missing_submodels.json')
        compliance_tool.check_schema(file_path_3, manager)
        self.assertEqual(len(manager.steps), 3)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(2)
        self.assertIsNotNone(re.search(r"'submodels' is a required property", error_list[0].getMessage()))

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_schema(file_path_4, manager)
        self.assertEqual(len(manager.steps), 3)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)

    def test_check_deserialization(self):
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.json')
        compliance_tool.check_deserialization(file_path_1, manager)
        self.assertEqual(len(manager.steps), 1)
        self.assertEqual(manager.steps[0][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(0)
        self.assertIsNotNone(re.search(r"No such file or directory", error_list[0].getMessage()))

        manager.steps = []
        file_path_2 = os.path.join(script_dir, 'files/test_not_serializable_aas.json')
        compliance_tool.check_deserialization(file_path_2, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(1)
        self.assertIsNotNone(re.search(r'Found JSON object with modelType="Test", which is not a known AAS class',
                                       error_list[0].getMessage()))

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_serializable_aas_warning.json')
        compliance_tool.check_deserialization(file_path_3, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(1)
        self.assertIsNotNone(re.search(r"Ignoring 'revision' attribute of AdministrativeInformation object due to "
                                       r"missing 'version'", error_list[0].getMessage()))

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_deserialization(file_path_4, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_deserialization(file_path_4, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)

    def test_check_aas_example(self):
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_2 = os.path.join(script_dir, 'files/test_demo_full_example.json')
        compliance_tool.check_aas_example(file_path_2, manager)
        self.assertEqual(len(manager.steps), 3)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)

        manager.steps = []
        file_path_1 = os.path.join(script_dir, 'files/test_not_serializable_aas.json')
        compliance_tool.check_aas_example(file_path_1, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(1)
        self.assertIsNotNone(re.search(r'Found JSON object with modelType="Test", which is not a known AAS class',
                                       error_list[0].getMessage()))

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.json')
        compliance_tool.check_aas_example(file_path_3, manager)
        self.assertEqual(len(manager.steps), 3)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(2)
        self.assertNotEqual(-1, error_list[0].getMessage().find('Attribute id_short of AssetAdministrationShell'
                                                                '[Identifier(IRI=https://acplt.org/'
                                                                'Test_AssetAdministrationShell)] must be == '
                                                                'TestAssetAdministrationShell123'))

    def test_check_json_files_equivalence(self):
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_serializable_aas.json')
        file_path_2 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_json_files_equivalence(file_path_1, file_path_2, manager)
        self.assertEqual(len(manager.steps), 2)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.FAILED)

        manager.steps = []
        compliance_tool.check_json_files_equivalence(file_path_2, file_path_1, manager)
        self.assertEqual(len(manager.steps), 4)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)
        self.assertEqual(manager.steps[3][1], Status.FAILED)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_aas.json')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_aas.json')
        compliance_tool.check_json_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(len(manager.steps), 5)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)
        self.assertEqual(manager.steps[3][1], Status.SUCCESS)
        self.assertEqual(manager.steps[4][1], Status.SUCCESS)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_aas.json')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_aas_wrong_attribute.json')
        compliance_tool.check_json_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(len(manager.steps), 5)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)
        self.assertEqual(manager.steps[3][1], Status.SUCCESS)
        self.assertEqual(manager.steps[4][1], Status.FAILED)

        manager.steps = []
        compliance_tool.check_json_files_equivalence(file_path_4, file_path_3, manager)
        self.assertEqual(len(manager.steps), 5)
        self.assertEqual(manager.steps[0][1], Status.SUCCESS)
        self.assertEqual(manager.steps[1][1], Status.SUCCESS)
        self.assertEqual(manager.steps[2][1], Status.SUCCESS)
        self.assertEqual(manager.steps[3][1], Status.SUCCESS)
        self.assertEqual(manager.steps[4][1], Status.FAILED)
        error_list = manager.get_error_logs_from_step(4)
        self.assertIsNotNone(re.search(r'Attribute description of AssetAdministrationShell\[Identifier'
                                       r'\(IRI=https://acplt.org/Test_AssetAdministrationShell\)\] must be ==',
                                       error_list[0].getMessage()))
