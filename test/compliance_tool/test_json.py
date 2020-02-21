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
import io
import os
import re
import unittest

import aas.compliance_tool.json as compliance_tool
from aas.compliance_tool.helper import MessageLogger, MessageCategory

dirname = os.path.dirname
JSON_SCHEMA_FILE = os.path.join(dirname(dirname(dirname(__file__))), 'test\\adapter\\json\\aasJSONSchemaV2.0.json')


class ComplianceToolJsonTest(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(JSON_SCHEMA_FILE), "JSON Schema not found for validation")
    def test_check_schema(self):
        logger = MessageLogger()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.json')
        compliance_tool.check_schema(file_path_1, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Unable to open json file: {}'.format(file_path_1))

        file_path_2 = os.path.join(script_dir, 'files/test_not_serializable.json')
        compliance_tool.check_schema(file_path_2, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Unable to deserialize json file: {}'.format(file_path_2))

        file_path_3 = os.path.join(script_dir, 'files/test_missing_submodels.json')
        compliance_tool.check_schema(file_path_3, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Validation of file {} was not successfull'.format(file_path_3))
        self.assertIsNotNone(re.search(r"'submodels' is a required property", message.msg_category))

        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_schema(file_path_4, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.msg, 'Schema check of file {} was successful'.format(file_path_4))
        self.assertEqual(message.category, MessageCategory.SUCCESS)

    def test_check_deserialization(self):
        logger = MessageLogger()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.json')
        compliance_tool.check_deserialization(file_path_1, True, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Unable to open json file: {}'.format(file_path_1))

        file_path_2 = os.path.join(script_dir, 'files/test_not_serializable_aas.json')
        compliance_tool.check_deserialization(file_path_2, False, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Unable to deserialize json file: {}'.format(file_path_2))
        self.assertIsNotNone(re.search(r'Found JSON object with modelType="Test", which is not a known AAS class',
                                       message.msg_category))

        compliance_tool.check_deserialization(file_path_2, True, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.ERROR)
        self.assertEqual(message.msg, 'Unable to deserialize json file: {}'.format(file_path_2))
        self.assertIsNotNone(re.search(r'Found JSON object with modelType="Test", which is not a known AAS class',
                                       message.msg_category))

        file_path_3 = os.path.join(script_dir, 'files/test_serializable_aas_warning.json')
        compliance_tool.check_deserialization(file_path_3, True, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.category, MessageCategory.SUCCESS)
        self.assertEqual(message.msg, 'Deserialization check of file {} was successful'.format(file_path_3))
        self.assertIsNotNone(re.search(r"Ignoring 'revision' attribute of AdministrativeInformation object due to "
                                       r"missing 'version'", message.msg_category))

        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_deserialization(file_path_4, True, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.msg, 'Deserialization check of file {} was successful'.format(file_path_4))
        self.assertEqual(message.category, MessageCategory.SUCCESS)

        file_path_4 = os.path.join(script_dir, 'files/test_empty.json')
        compliance_tool.check_deserialization(file_path_4, False, logger)
        message = logger.get_last_message_in_list(MessageCategory.ALL)
        self.assertEqual(message.msg, 'Deserialization check of file {} was successful'.format(file_path_4))
        self.assertEqual(message.category, MessageCategory.SUCCESS)
