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
import unittest

from aas.util.message_logger import MessageLogger, MessageCategory, LoggingMessage


class ComplianceToolLoggerTest(unittest.TestCase):
    def test_message_logger(self):
        logger = MessageLogger()
        logger.add_msg(LoggingMessage('test_error', 'test_error_category', MessageCategory.ERROR))
        logger.add_msg(LoggingMessage('test_warning', 'test_warning_category', MessageCategory.WARNING))
        logger.add_msg(LoggingMessage('test_success', 'test_success_category', MessageCategory.SUCCESS))
        messages = logger.get_messages_in_list(MessageCategory.ALL)
        self.assertEqual(messages[0].__str__(verbose=True), 'ERROR: test_error\nOccurred log messages:\ntest_error_'
                                                            'category\n')
        self.assertEqual(messages[1].__str__(verbose=True), 'WARNING: test_warning\nOccurred log messages:\n'
                                                            'test_warning_category\n')
        self.assertEqual(messages[2].__str__(), 'SUCCESS: test_success\n')
        self.assertEqual(messages[2].__str__(verbose=True), 'SUCCESS: test_success\nOccurred log messages:\n'
                                                            'test_success_category\n')
        message_list = logger.get_messages_in_ordered_lists()
        self.assertEqual(message_list[0][0].__str__(verbose=True), 'ERROR: test_error\nOccurred log messages:\ntest_'
                                                                   'error_category\n')
        self.assertEqual(message_list[1][0].__str__(verbose=True), 'WARNING: test_warning\nOccurred log messages:\n'
                                                                   'test_warning_category\n')
        self.assertEqual(message_list[2][0].__str__(), 'SUCCESS: test_success\n')
        self.assertEqual(message_list[2][0].__str__(verbose=True), 'SUCCESS: test_success\nOccurred log messages:\n'
                                                                   'test_success_category\n')
        logger.add_msg(LoggingMessage('test_failure', '', MessageCategory.ALL))
        with self.assertRaises(ValueError):
            logger.get_messages_in_ordered_lists()

        logger_2 = MessageLogger()
        logger_2.add_msg(LoggingMessage('test_error', 'test_error_category', MessageCategory.ERROR))
        self.assertIsNone(logger_2.get_last_message_in_list(MessageCategory.SUCCESS))
