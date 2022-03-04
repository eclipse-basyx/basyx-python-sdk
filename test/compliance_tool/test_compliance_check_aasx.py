# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
import os
import unittest

from basyx.aas.compliance_tool import compliance_check_aasx as compliance_tool
from basyx.aas.compliance_tool.state_manager import ComplianceToolStateManager, Status


class ComplianceToolAASXTest(unittest.TestCase):
    def test_check_deserialization(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.aasx')
        compliance_tool.check_deserialization(file_path_1, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertIn("is not a valid ECMA376-2 (OPC) file", manager.format_step(0, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)

        # Todo add more tests for checking wrong aasx files

        manager.steps = []
        file_path_5 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_deserialization(file_path_5, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

    def test_check_aas_example(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_2 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_aas_example(file_path_2, manager)
        self.assertEqual(4, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example2.aasx')
        compliance_tool.check_aas_example(file_path_3, manager)
        self.assertEqual(4, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.aasx')
        compliance_tool.check_aas_example(file_path_4, manager)
        self.assertEqual(4, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell[Identifier(IRI=https://acplt.org/'
                      'Test_AssetAdministrationShell)] must be == TestAssetAdministrationShell',
                      manager.format_step(2, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[3].status)

    def test_check_aasx_files_equivalence(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_2 = os.path.join(script_dir, 'files/test_empty.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_1, file_path_2, manager)
        self.assertEqual(6, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)

        manager.steps = []
        compliance_tool.check_aasx_files_equivalence(file_path_2, file_path_1, manager)
        self.assertEqual(6, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(6, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)
        self.assertEqual(Status.SUCCESS, manager.steps[5].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.aasx')
        compliance_tool.check_aasx_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(6, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell'
                      '[Identifier(IRI=https://acplt.org/Test_AssetAdministrationShell)] must be ==',
                      manager.format_step(4, verbose_level=1))
        self.assertEqual(Status.FAILED, manager.steps[4].status)

        manager.steps = []
        compliance_tool.check_aasx_files_equivalence(file_path_4, file_path_3, manager)
        self.assertEqual(6, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn('Attribute id_short of AssetAdministrationShell'
                      '[Identifier(IRI=https://acplt.org/Test_AssetAdministrationShell)] must be ==',
                      manager.format_step(4, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)

    def test_check_schema(self):
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_2 = os.path.join(script_dir, 'files/test_demo_full_example.aasx')
        compliance_tool.check_schema(file_path_2, manager)
        self.assertEqual(10, len(manager.steps))
        for i in range(10):
            self.assertEqual(Status.SUCCESS, manager.steps[i].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example2.aasx')
        compliance_tool.check_schema(file_path_3, manager)
        self.assertEqual(4, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.aasx')
        compliance_tool.check_schema(file_path_4, manager)
        self.assertEqual(10, len(manager.steps))
        for i in range(10):
            self.assertEqual(Status.SUCCESS, manager.steps[i].status)
