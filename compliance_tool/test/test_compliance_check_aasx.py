# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import unittest
from unittest import mock

from ._test_helper import create_example_aas_core_properties, create_read_into_mock
from aas_compliance_tool import compliance_check_aasx as compliance_tool
from aas_compliance_tool.state_manager import ComplianceToolStateManager, Status

from basyx.aas.examples.data._helper import CheckResult


class ComplianceToolAASXTest(unittest.TestCase):

    def test_check_deserialization_no_file(self) -> None:
        manager = ComplianceToolStateManager()

        compliance_tool.check_deserialization("", manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertIn("No such file or directory", manager.format_step(0, verbose_level=1))

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    def test_check_deserialization_open_raises(self, mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.side_effect = ValueError("Test error!")
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    def test_check_deserialization_read_raises(self, mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.return_value.read_into.side_effect = ValueError("Test error!")
        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    def test_check_deserialization_success(self, mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        compliance_tool.check_deserialization("", manager)

        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_open(self, mock_data_checker: mock.MagicMock,
                                            mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.side_effect = ValueError("Test error!")
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_read(self, mock_data_checker: mock.MagicMock,
                                            mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.return_value.read_into.side_effect = ValueError("Test error!")
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_data_check(self, mock_data_checker: mock.MagicMock,
                                                  mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        failed = [CheckResult("Expected Behavior", False, dict())]
        mock_data_checker.return_value.checks = failed
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter(failed))
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn("Expected Behavior", manager.format_step(2, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_core_properties(self, mock_data_checker: mock.MagicMock,
                                                       mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file='TestFile')
        wrong_cp = create_example_aas_core_properties()
        wrong_cp.creator = "Wrong Creator"
        mock_aasx_reader.return_value.get_core_properties.return_value = wrong_cp
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.FAILED, manager.steps[3].status)
        self.assertIn("Wrong Creator", manager.format_step(3, verbose_level=1))
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_file_missing(self, mock_data_checker: mock.MagicMock,
                                                    mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file=None)
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn("/TestFile.pdf", manager.format_step(4, verbose_level=1))

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_fail_on_file_check(self, mock_data_checker: mock.MagicMock,
                                                  mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file='TestFileWrong')
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn("/TestFile.pdf", manager.format_step(4, verbose_level=1))

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aas_example_success(self, mock_data_checker: mock.MagicMock,
                                       mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file='TestFile')
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        compliance_tool.check_aas_example("", manager)

        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_file1_fail_on_open(self, mock_data_checker: mock.MagicMock,
                                                             mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.side_effect = [ValueError("Test error!"), mock_aasx_reader.return_value]
        mock_data_checker.return_value.checks = []
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertIn("Test error!", manager.format_step(0, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[6].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_file2_fail_on_open(self, mock_data_checker: mock.MagicMock,
                                                             mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.side_effect = [mock_aasx_reader.return_value, ValueError("Test error!")]
        mock_data_checker.return_value.checks = []
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn("Test error!", manager.format_step(2, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[6].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_fail_on_data_check(self, mock_data_checker: mock.MagicMock,
                                                             mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        failed = [CheckResult("Expected Behavior", False, dict())]
        mock_data_checker.return_value.checks = failed
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter(failed))
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn("Expected Behavior", manager.format_step(4, verbose_level=1))
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[5].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[6].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_fail_on_core_properties(self, mock_data_checker: mock.MagicMock,
                                                                  mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file='TestFile')
        mock_data_checker.return_value.checks = []
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))

        wrong_cp = create_example_aas_core_properties()
        wrong_cp.creator = "Wrong Creator"
        mock_aasx_reader.return_value.get_core_properties.side_effect = \
            [create_example_aas_core_properties(), wrong_cp]

        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)
        self.assertEqual(Status.FAILED, manager.steps[5].status)
        self.assertIn("Wrong Creator", manager.format_step(5, verbose_level=1))
        self.assertEqual(Status.SUCCESS, manager.steps[6].status)

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_fail_on_file_missing(self, mock_data_checker: mock.MagicMock,
                                                               mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()

        call_count = [0]

        def setup_file_stores(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_read_into_mock(file='TestFile')(*args, **kwargs)
            else:
                return create_read_into_mock(file=None)(*args, **kwargs)

        mock_aasx_reader.return_value.read_into.side_effect = setup_file_stores
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)
        self.assertEqual(Status.SUCCESS, manager.steps[5].status)
        self.assertEqual(Status.FAILED, manager.steps[6].status)
        self.assertIn("second file must contain supplementary file /TestFile.pdf",
                      manager.format_step(6, verbose_level=1))

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_fail_on_file_check(self, mock_data_checker: mock.MagicMock,
                                                             mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()

        call_count = [0]

        def setup_file_stores(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_read_into_mock(file='TestFile')(*args, **kwargs)
            else:
                return create_read_into_mock(file='TestFileWrong')(*args, **kwargs)

        mock_aasx_reader.return_value.read_into.side_effect = setup_file_stores
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)
        self.assertEqual(Status.SUCCESS, manager.steps[5].status)
        self.assertEqual(Status.FAILED, manager.steps[6].status)
        self.assertIn("second file must contain supplementary file /TestFile.pdf with sha256",
                      manager.format_step(6, verbose_level=1))

    @mock.patch("basyx.aas.adapter.aasx.AASXReader", autospec=True)
    @mock.patch("aas_compliance_tool.compliance_check_aasx.AASDataChecker", autospec=True)
    def test_check_aasx_files_equivalence_success(self, mock_data_checker: mock.MagicMock,
                                                  mock_aasx_reader: mock.MagicMock) -> None:
        manager = ComplianceToolStateManager()

        mock_aasx_reader.return_value.read_into.side_effect = create_read_into_mock(file='TestFile')
        mock_aasx_reader.return_value.get_core_properties.return_value = create_example_aas_core_properties()
        mock_data_checker.return_value.checks = []
        type(mock_data_checker.return_value).failed_checks = mock.PropertyMock(side_effect=lambda: iter([]))
        compliance_tool.check_aasx_files_equivalence("", "", manager)

        self.assertEqual(7, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)
        self.assertEqual(Status.SUCCESS, manager.steps[5].status)
        self.assertEqual(Status.SUCCESS, manager.steps[6].status)
