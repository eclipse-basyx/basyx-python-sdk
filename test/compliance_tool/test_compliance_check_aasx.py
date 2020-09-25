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
import unittest

import aas.compliance_tool.compliance_check_aasx as compliance_tool
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status


class ComplianceToolAASXTest(unittest.TestCase):
    def test_check_deserialization(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.aasx')
        compliance_tool.check_deserialization(file_path_1, manager)
        self.assertEqual(1, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertIn("is not a valid ECMA376-2 (OPC) file", manager.format_step(0, verbose_level=1))

        # Todo add more tests for checking wrong aasx files

        manager.steps = []
        file_path_5 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_deserialization(file_path_5, manager)
        self.assertEqual(1, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)


    def test_check_aas_example(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_2 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_aas_example(file_path_2, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        # Todo update AASX library for saving also sm and cds which are not linked to an aas
        self.assertEqual(Status.FAILED, manager.steps[1].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.aasx')
        compliance_tool.check_aas_example(file_path_3, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell[Identifier(IRI=https://acplt.org/'
                      'Test_AssetAdministrationShell)] must be == TestAssetAdministrationShell',
                      manager.format_step(1, verbose_level=1))

    def test_check_aasx_files_equivalence(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_2 = os.path.join(script_dir, 'files/test_empty.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_1, file_path_2, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)

        manager.steps = []
        compliance_tool.check_aasx_files_equivalence(file_path_2, file_path_1, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell'
                      '[Identifier(IRI=https://acplt.org/Test_AssetAdministrationShell)] must be ==',
                      manager.format_step(2, verbose_level=1))

        manager.steps = []
        compliance_tool.check_aasx_files_equivalence(file_path_4, file_path_3, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell'
                      '[Identifier(IRI=https://acplt.org/Test_AssetAdministrationShell)] must be ==',
                      manager.format_step(2, verbose_level=1))
