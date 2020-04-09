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

"""
Command line script which is a compliance tool for creating and checking json and xml files in compliance with
"Details of the Asset Administration Shell" specification of Plattform Industrie 4.0. It uses the create_example() from
examples.data.__init__.py
"""
import argparse

import logging

from aas.compliance_tool import compliance_check_json as compliance_tool_json
from aas.adapter.json import write_aas_json_file
from aas.examples.data import create_example
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status


def main():
    parser = argparse.ArgumentParser(
        prog='compliance_tool',
        description='Compliance tool for creating and checking json and xml files in compliance with "Details of the '
                    'Asset Administration Shell" specification of Plattform Industrie 4.0.',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('action', choices=['create', 'c', 'schema', 's', 'deserialization', 'd', 'example', 'e',
                                           'files', 'f'],
                        help='c or create: creates a file with the example data with the given file path\n'
                             's or schema: checks a given file if it is compliance with the official json schema\n'
                             'd or deserialization: checks if a given file is deserializable\n'
                             'e or example: checks if a given file contains the example aas elements\n'
                             'f or files: checks if two given files contains the same aas elements in any order')
    parser.add_argument('file_1', help="path to file 1")
    parser.add_argument('file_2', nargs='?', default=None, help="path to file 2")
    parser.add_argument('-v', '--verbose', help="display all information occurred while checking: 1: Error information,"
                                                " 2: Additional Success information", action='count', default=0)
    parser.add_argument('-q', '--quite', help="no information output if successful", action='store_true')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--json', help="checking or creating json file(s)", action='store_true')
    group.add_argument('--xml', help="checking or creating xml file(s)", action='store_true')
    parser.add_argument('-l', '--logfile', help="creates the log additional in the given file", default=None)

    args = parser.parse_args()

    # Todo try to find out in which format the file is if not --json or --xml

    manager = ComplianceToolStateManager()
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.addHandler(manager)

    if args.action == 'create' or args.action == 'c':
        manager.add_step('Create example data')
        data = create_example()
        manager.set_step_status(Status.SUCCESS)
        try:
            manager.add_step('Open file')
            with open(args.file_1, 'w', encoding='utf-8-sig') as file:
                manager.set_step_status(Status.SUCCESS)

                manager.add_step('Write data to file')
                if args.json:
                    write_aas_json_file(file=file, data=data)
                    manager.set_step_status(Status.SUCCESS)
                elif args.xml:
                    # Todo: if xml serialization is done add code here
                    raise NotImplementedError
        except IOError as error:
            logger.error(error)
            manager.set_step_status(Status.FAILED)
    elif args.action == 'schema' or args.action == 's':
        if args.json:
            compliance_tool_json.check_schema(args.file_1, manager)
        elif args.xml:
            # Todo: if xml serialization is done add code here
            raise NotImplementedError
    elif args.action == 'deserialization' or args.action == 'd':
        if args.json:
            compliance_tool_json.check_deserialization(args.file_1, manager)
        elif args.xml:
            # Todo: if xml serialization is done add code here
            raise NotImplementedError
    elif args.action == 'example' or args.action == 'e':
        if args.json:
            compliance_tool_json.check_aas_example(args.file_1, manager)
        elif args.xml:
            # Todo: if xml serialization is done add code here
            raise NotImplementedError
    elif args.action == 'files' or args.action == 'f':
        if args.file_2:
            if args.json:
                compliance_tool_json.check_json_files_equivalence(args.file_1, args.file_2, manager)
            elif args.xml:
                # Todo: if xml serialization is done add code here
                raise NotImplementedError
        else:
            parser.error("f or files requires two file path.")
            exit()

    if manager.status is Status.SUCCESS and args.quite:
        exit()

    print(manager.format_state_manager(args.verbose))

    if args.logfile:
        try:
            with open(args.logfile, 'w', encoding='utf-8-sig') as file:
                file.write(manager.format_state_manager(args.verbose))
        except IOError as error:
            print('Could not open logfile: \n{}'.format(error))


if __name__ == "__main__":
    main()
