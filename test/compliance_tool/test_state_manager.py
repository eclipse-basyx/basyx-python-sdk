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
import logging
import unittest

from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status
from aas.examples.data._helper import DataChecker


class ComplianceToolStateManagerTest(unittest.TestCase):
    def test_state(self) -> None:
        manager = ComplianceToolStateManager()
        manager.add_step('test')
        self.assertEqual(Status.NOT_EXECUTED, manager.status)
        manager.set_step_status(Status.SUCCESS)
        self.assertEqual(Status.SUCCESS, manager.status)
        manager.set_step_status(Status.FAILED)
        self.assertEqual(Status.FAILED, manager.status)

    def test_logs(self) -> None:
        manager = ComplianceToolStateManager()
        manager.add_step('test')
        manager.add_log_record(logging.LogRecord('x', logging.INFO, '', 0, 'test_msg', (), None))
        self.assertEqual(0, len(manager.get_error_logs_from_step(0)))
        manager.add_log_record(logging.LogRecord('x', logging.ERROR, '', 0, 'test_msg_2', (), None))
        self.assertEqual(1, len(manager.get_error_logs_from_step(0)))

        manager.add_step('test 2')
        checker = DataChecker(raise_immediately=False)
        checker.check(2 == 2, 'Assertion test')

        manager.add_log_records_from_data_checker(checker)
        self.assertEqual(0, len(manager.get_error_logs_from_step(1)))
        self.assertEqual('SUCCESS:      test 2', manager.format_step(1, 1))
        self.assertEqual('SUCCESS:      test 2', manager.format_step(1, 1))
        self.assertIn('INFO:  Assertion test ()', manager.format_step(1, 2))

        checker.check(2 == 1, 'Assertion test 2')
        manager.add_log_records_from_data_checker(checker)
        self.assertEqual(1, len(manager.get_error_logs_from_step(1)))
        self.assertEqual('FAILED:       test 2', manager.format_step(1))
        self.assertIn('ERROR: Assertion test 2 ()', manager.format_step(1, 1))
        self.assertIn('INFO:  Assertion test ()', manager.format_step(1, 2))
