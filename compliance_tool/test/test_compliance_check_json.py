# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import os
import unittest
from unittest import mock
import logging

from aas_compliance_tool import compliance_check_json as compliance_tool
from aas_compliance_tool.state_manager import ComplianceToolStateManager, Status

from basyx.aas.examples.data._helper import CheckResult


class ComplianceToolJsonTest(unittest.TestCase):


    def test_check_deserialization_no_file(self) -> None:
        manager = ComplianceToolStateManager()

        compliance_tool.check_deserialization("", manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertIn("No such file or directory", manager.format_step(0, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    def test_check_deserialization_fail_on_error(self, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        def mock_error(*args, **kwargs):
            logging.getLogger('basyx.aas.adapter.json.json_deserialization').error("Test error!")

        mock_read_json_file.side_effect = mock_error
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Test error!", manager.format_step(1, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    def test_check_deserialization_fail_on_warning(self, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        def mock_warning(*args, **kwargs):
            logging.getLogger('basyx.aas.adapter.json.json_deserialization').warning("Test warning!")

        mock_read_json_file.side_effect = mock_warning
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Test warning!", manager.format_step(1, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    def test_check_deserialization_success(self, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        def mock_debugging(*args, **kwargs):
            logging.getLogger('basyx.aas.adapter.json.json_deserialization').debug("Test info!")

        mock_read_json_file.side_effect = mock_debugging
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_example_success(self, mock_data_checker: mock.MagicMock, mock_read_json_file: mock.MagicMock, mock_open: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        compliance_tool.check_aas_example("", manager)

        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_example_fail_on_read(self, mock_data_checker: mock.MagicMock, mock_read_json_file: mock.MagicMock,
                                   mock_open: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        def mock_error(*args, **kwargs):
            logging.getLogger('basyx.aas.adapter.json.json_deserialization').error("Error on reading aas json file!")

        mock_read_json_file.side_effect = mock_error
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Error on reading aas json file!", manager.format_step(1, verbose_level=1) )
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_example_fail_on_check(self, mock_data_checker: mock.MagicMock, mock_read_json_file: mock.MagicMock,
                                     mock_open: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()
        mock_data_checker.return_value.checks = [CheckResult("Expected Behavior", False, dict())]
        mock_data_checker.return_value.failed_checks = iter(mock_data_checker.return_value.checks)

        compliance_tool.check_aas_example("", manager)

        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn("Expected Behavior", manager.format_step(2, verbose_level=1))

    def test_check_json_files_equivalence(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_deserializable_aas.json')
        file_path_2 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_json_files_equivalence(file_path_1, file_path_2, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

        manager.steps = []
        compliance_tool.check_json_files_equivalence(file_path_2, file_path_1, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.FAILED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.json')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example.json')
        compliance_tool.check_json_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.json')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.json')
        compliance_tool.check_json_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertEqual('FAILED:       Check if data in files are equal\n - ERROR: Attribute id_short of '
                         'AssetAdministrationShell[https://example.org/Test_AssetAdministrationShell] must be == '
                         'TestAssetAdministrationShell123 (value=\'TestAssetAdministrationShell\')',
                         manager.format_step(4, verbose_level=1))

        manager.steps = []
        compliance_tool.check_json_files_equivalence(file_path_4, file_path_3, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertEqual('FAILED:       Check if data in files are equal\n - ERROR: Attribute id_short of '
                         'AssetAdministrationShell[https://example.org/Test_AssetAdministrationShell] must be == '
                         'TestAssetAdministrationShell (value=\'TestAssetAdministrationShell123\')',
                         manager.format_step(4, verbose_level=1))
