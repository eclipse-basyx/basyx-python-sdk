# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import unittest
from unittest import mock

from aas_compliance_tool import compliance_check_json as compliance_tool
from aas_compliance_tool.state_manager import ComplianceToolStateManager, Status
from basyx.aas.examples.data._helper import CheckResult

from ._test_helper import create_mock_effect


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

        mock_read_json_file.side_effect = create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'error')
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Test error!", manager.format_step(1, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    def test_check_deserialization_fail_on_warning(self, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        mock_read_json_file.side_effect = create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'warning')
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Test warning!", manager.format_step(1, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    def test_check_deserialization_success(self, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        mock_read_json_file.side_effect = create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'debug')
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_example_success(self, mock_data_checker: mock.MagicMock, mock_read_json_file: mock.MagicMock,
                                   mock_open: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
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

        mock_read_json_file.side_effect = create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'error',
                                                             error_msg="Error on reading aas json file!")
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Error on reading aas json file!", manager.format_step(1, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_example_fail_on_check(self, mock_data_checker: mock.MagicMock, mock_read_json_file: mock.MagicMock,
                                         mock_open: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()
        failed = [CheckResult("Expected Behavior", False, dict())]
        mock_data_checker.return_value.checks = failed
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter(failed))

        compliance_tool.check_aas_example("", manager)

        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn("Expected Behavior", manager.format_step(2, verbose_level=1))

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_json_files_equivalence_file1_fail_on_deserialization(self, mock_data_checker, mock_read_json_file,
                                                                        mock_open) -> None:
        manager = ComplianceToolStateManager()

        call_count = [0]

        def mock_first_fails(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'error')(*args, **kwargs)

        mock_read_json_file.side_effect = mock_first_fails
        compliance_tool.check_json_files_equivalence("", "", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("Test error!", manager.format_step(1, verbose_level=1))
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_json_files_equivalence_file2_fail_on_deserialization(self, mock_data_checker, mock_read_json_file,
                                                                        mock_open) -> None:
        manager = ComplianceToolStateManager()

        call_count = [0]

        def mock_second_fails(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                create_mock_effect('basyx.aas.adapter.json.json_deserialization', 'error')(*args, **kwargs)

        mock_read_json_file.side_effect = mock_second_fails
        compliance_tool.check_json_files_equivalence("", "", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.FAILED, manager.steps[3].status)
        self.assertIn("Test error!", manager.format_step(3, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_json_files_equivalence_success(self, mock_data_checker, mock_read_json_file, mock_open) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        compliance_tool.check_json_files_equivalence("", "", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)

    @mock.patch("builtins.open")
    @mock.patch("basyx.aas.adapter.json.json_deserialization.read_aas_json_file", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_json.AASDataChecker", autospec=True)
    def test_check_json_files_equivalence_fail_on_check(self, mock_data_checker: mock.MagicMock, mock_read_json_file,
                                                        mock_open) -> None:
        manager = ComplianceToolStateManager()

        failed = [CheckResult("Expected Behavior", False, dict())]
        mock_data_checker.return_value.checks = failed
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter(failed))
        compliance_tool.check_json_files_equivalence("", "", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn("Expected Behavior", manager.format_step(4, verbose_level=1))
