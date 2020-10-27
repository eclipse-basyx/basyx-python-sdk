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

"""
Command line script which is a compliance tool for creating and checking json and xml files in compliance with
"Details of the Asset Administration Shell" specification of Plattform Industrie 4.0. It uses the create_example() from
examples.data.__init__.py
"""
import argparse
import datetime

import logging

import pyecma376_2

from aas import model
from aas.adapter import aasx
from aas.adapter.xml import write_aas_xml_file
from aas.compliance_tool import compliance_check_json as compliance_tool_json
from aas.compliance_tool import compliance_check_xml as compliance_tool_xml
from aas.compliance_tool import compliance_check_aasx as compliance_tool_aasx
from aas.adapter.json import write_aas_json_file
from aas.examples.data import create_example, create_example_aas_binding, TEST_PDF_FILE
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status


def main():
    parser = argparse.ArgumentParser(
        prog='compliance_tool',
        description='Compliance tool for creating and checking json and xml files in compliance with "Details of the '
                    'Asset Administration Shell" specification of Plattform Industrie 4.0. \n\n'
                    'This tool has five features: \n'
                    '1. create a xml or json file or an AASX file using xml or json files with example aas elements\n'
                    '2. check a given xml or json file if it is compliant with the official json or xml aas schema\n'
                    '3. check if a given xml, json or aasx file is deserializable\n'
                    '4. check if the data in a given xml, json or aasx file is the same as the example data\n'
                    '5. check if two given xml, json or aasx files contain the same aas elements in any order\n\n'
                    'As a first argument, the feature must be specified (create, schema, deserialization, example, '
                    'files) or in short (c, s, d, e or f).\n'
                    'Depending the chosen feature, different additional arguments must be specified:\n'
                    'create or c:          path to the file which shall be created (file_1)\n'
                    'schema or s:          file to be checked (file_1)\n'
                    'deserialization or d: file to be checked (file_1)\n'
                    'example or e:         file to be checked (file_1)\n'
                    'file_compare or f:    files to compare (file_1, file_2)\n,'
                    'In any case, it must be specified whether the (given or created) files are json (--json) or '
                    'xml (--xml).\n'
                    'All features except "schema" support reading/writing AASX packages instead of plain XML or JSON '
                    'files via the --aasx option.\n\n'
                    'Additionally, the tool offers some extra features for more convenient usage:\n'
                    'a. Different levels of verbosity:\n'
                    '   Default output is just the status for each step performed. With -v or --verbose, additional '
                    'information in case of status = FAILED will be provided. With one more -v or --verbose, additional'
                    ' information even in case of status = SUCCESS or WARNINGS will be provided.\n'
                    'b. Suppressing output on success:\n'
                    '   With -q or --quite no output will be generated if the status = SUCCESS.\n'
                    'c. Save log additionally in a logfile:\n'
                    '   With -l or --logfile, a path to the file where the logfiles shall be created can be specified.',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('action', choices=['create', 'c', 'schema', 's', 'deserialization', 'd', 'example', 'e',
                                           'files', 'f'],
                        help='c or create: creates a file with example data\n'
                             's or schema: checks a given file if it is compliance with the official schema\n'
                             'd or deserialization: checks if a given file is deserializable\n'
                             'e or example: checks if a given file contains the example aas elements\n'
                             'f or file_compare: checks if two given files contain the same aas elements in any order')
    parser.add_argument('file_1', help="path to file 1")
    parser.add_argument('file_2', nargs='?', default=None, help="path to file 2: is required if action f or files is "
                                                                "choosen")
    parser.add_argument('-v', '--verbose', help="Print detailed information for each check. Multiple -v options "
                                                "increase the verbosity. 1: Detailed error information, 2: Additional "
                                                "detailed success information", action='count', default=0)
    parser.add_argument('-q', '--quite', help="no information output if successful", action='store_true')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--json', help="Use AAS json format when checking or creating files", action='store_true')
    group.add_argument('--xml', help="Use AAS xml format when checking or creating files", action='store_true')
    parser.add_argument('-l', '--logfile', help="Log file to be created in addition to output to stdout", default=None)
    parser.add_argument('--aasx', help="Create or read AASX files", action='store_true')

    args = parser.parse_args()

    # Todo try to find out in which format the file is if not --json or --xml

    manager = ComplianceToolStateManager()
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.addHandler(manager)

    if args.action == 'create' or args.action == 'c':
        manager.add_step('Create example data')
        if args.aasx:
            data = create_example_aas_binding()
        else:
            data = create_example()
        manager.set_step_status(Status.SUCCESS)
        try:
            manager.add_step('Open file')
            if args.aasx:
                with aasx.AASXWriter(args.file_1) as writer:
                    manager.set_step_status(Status.SUCCESS)
                    manager.add_step('Write data to file')

                    files = aasx.DictSupplementaryFileContainer()
                    with open(TEST_PDF_FILE, 'rb') as f:
                        files.add_file("/TestFile.pdf", f, "application/pdf")

                    # Create OPC/AASX core properties
                    cp = pyecma376_2.OPCCoreProperties()
                    cp.created = datetime.datetime.fromtimestamp(1577829600)
                    cp.creator = "PyI40AAS Testing Framework"

                    for identifiable in data:
                        if isinstance(identifiable, model.AssetAdministrationShell):
                            writer.write_aas(identifiable.identification, data, files, write_json=args.json)
                    writer.write_core_properties(cp)
                manager.set_step_status(Status.SUCCESS)
            elif args.json:
                with open(args.file_1, 'w', encoding='utf-8-sig') as file:
                    manager.set_step_status(Status.SUCCESS)
                    manager.add_step('Write data to file')
                    write_aas_json_file(file=file, data=data, indent=4)
                    manager.set_step_status(Status.SUCCESS)
            elif args.xml:
                with open(args.file_1, 'wb') as file:
                    manager.set_step_status(Status.SUCCESS)
                    manager.add_step('Write data to file')
                    write_aas_xml_file(file=file, data=data, pretty_print=True)
                    manager.set_step_status(Status.SUCCESS)
        except IOError as error:
            logger.error(error)
            manager.set_step_status(Status.FAILED)
    elif args.action == 'schema' or args.action == 's':
        if args.json:
            compliance_tool_json.check_schema(args.file_1, manager)
        if args.xml:
            compliance_tool_xml.check_schema(args.file_1, manager)
    elif args.action == 'deserialization' or args.action == 'd':
        if args.aasx:
            compliance_tool_aasx.check_deserialization(args.file_1, manager)
        elif args.json:
            compliance_tool_json.check_deserialization(args.file_1, manager)
        elif args.xml:
            compliance_tool_xml.check_deserialization(args.file_1, manager)
    elif args.action == 'example' or args.action == 'e':
        if args.aasx:
            compliance_tool_aasx.check_aas_example(args.file_1, manager)
        elif args.json:
            compliance_tool_json.check_aas_example(args.file_1, manager)
        elif args.xml:
            compliance_tool_xml.check_aas_example(args.file_1, manager)
    elif args.action == 'files' or args.action == 'f':
        if args.file_2:
            if args.aasx:
                compliance_tool_aasx.check_aasx_files_equivalence(args.file_1, args.file_2, manager)
            elif args.json:
                compliance_tool_json.check_json_files_equivalence(args.file_1, args.file_2, manager)
            elif args.xml:
                compliance_tool_xml.check_xml_files_equivalence(args.file_1, args.file_2, manager)
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
