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

import argparse
import aas.compliance_tool.json as compliance_tool_json

from aas.adapter.json import json_serialization
from aas.examples.data import example_aas
from aas.util.message_logger import MessageLogger, MessageCategory, LoggingMessage

parser = argparse.ArgumentParser(
    prog='compliance_tool',
    description='Compliance tool for creating and checking json and xml files in compliance with "Details of the '
                'Asset Administration Shell" specification of Plattform Industrie 4.0.',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('function', type=str, choices=['create', 'c', 'schema', 's', 'deserialization', 'd', 'example', 'e',
                                                   'files', 'f'],
                    help='c or create: creates a file with the example data with the given file path\n'
                         's or schema: checks a given file if it is compliance with the official json schema\n'
                         'd or deserialization: checks if a given file is deserializable\n'
                         'e or example: checks if a given file contains the example aas elements\n'
                         'f or files: checks if two given files contains the same aas elements in any order')
parser.add_argument('file_1', help="path to file 1")
parser.add_argument('file_2', nargs='?', default=None, help="path to file 2")
parser.add_argument('-f', '--failsafe', help="try to check as much as possible", action='store_true')
parser.add_argument('-v', '--verbose', help="display all information occurred while checking", action='store_true')
parser.add_argument('--format', type=str, choices=['xml', 'json'],
                    help='xml: checking or creating xml file(s)\n'
                         'json: checking or creating json file(s)\n'
                         'not set: tool tries to figure out in which format the file(s) is(are)')

args = parser.parse_args()
verbose = False
if args.verbose:
    verbose = True

failsafe = False
if args.failsafe:
    failsafe = True

format = args.format
if args.format is None:
    format = 'json'  # Todo try to find out in which format the file is

logger = MessageLogger()
if args.function == 'create' or args.function == 'c':
    data = example_aas.create_full_example()
    try:
        file = open(args.file_1, 'w', encoding='utf-8-sig')
    except FileNotFoundError as error:
        logger.add_msg(LoggingMessage('Unable to open file: {}'.format(args.file_1), str(error),
                                      MessageCategory.ERROR))
        exit()
    if format == 'json':
        json_serialization.write_aas_json_file(file=file, data=data)
    else:
        parser.error("xml is not implemented yet.")
    logger.add_msg(LoggingMessage('Creation of example file {} was successful'.format(args.file_1), '',
                                  MessageCategory.SUCCESS))
else:
    if args.function == 'schema' or args.function == 's':
        if format == 'json':
            compliance_tool_json.check_schema(args.file_1, logger)
        else:
            parser.error("xml is not implemented yet.")
    elif args.function == 'deserialization' or args.function == 'd':
        if format == 'json':
            compliance_tool_json.check_deserialization(args.file_1, failsafe, logger)
        else:
            parser.error("xml is not implemented yet.")
    elif args.function == 'example' or args.function == 'e':
        if format == 'json':
            compliance_tool_json.check_aas_example(args.file_1, failsafe, logger)
        else:
            parser.error("xml is not implemented yet.")
    elif args.function == 'files' or args.function == 'f':
        if args.file_2:
            if format == 'json':
                compliance_tool_json.check_json_files_conform(args.file_1, args.file_2, failsafe, logger)
            else:
                parser.error("xml is not implemented yet.")
        else:
            parser.error("f or files requires two file path.")

messages = logger.get_messages_in_list(MessageCategory.ALL)

for x in messages:
    print(x.__str__(verbose))
