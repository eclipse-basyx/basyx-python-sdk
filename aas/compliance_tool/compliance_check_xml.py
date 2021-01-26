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
Module which offers functions to use in a confirmation tool related to xml files

:meth:`~aas.compliance_tool.compliance_check_xml.check_schema`: Checks if a xml file is conform to official JSON schema
as defined in the 'Details of the Asset Administration Shell' specification of Plattform Industrie 4.0

:meth:`~aas.compliance_tool.compliance_check_xml.check_deserialization`: Checks if a xml file can be deserialized

:meth:`~aas.compliance_tool.compliance_check_xml.check_aas_example`: Checks if a xml file consist the data of the
example data defined in aas.examples.data.example_aas.py

:meth:`~aas.compliance_tool.compliance_check_xml.check_xml_files_equivalence`: Checks if two xml files have the same
data regardless of their order

All functions reports any issues using the given :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`
by adding new steps and associated LogRecords
"""

from lxml import etree  # type: ignore
import logging
from typing import Optional

from .. import model
from ..adapter.xml import xml_deserialization, XML_SCHEMA_FILE
from ..examples.data import example_aas, create_example
from ..examples.data._helper import AASDataChecker
from .state_manager import ComplianceToolStateManager, Status


def check_schema(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks a given file against the official xml schema and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Add the steps: `Open file`, `Read file`, `Check if it is conform to the xml syntax` and `Validate file against
    official xml schema`

    :param file_path: Path to the file which should be checked
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    state_manager.add_step('Open file')
    try:
        # open given file
        file_to_be_checked = open(file_path, 'rb')
    except IOError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.add_step('Read file and check if it is conform to the xml syntax')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Validate file against official xml schema')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return
    try:
        with file_to_be_checked:
            state_manager.set_step_status(Status.SUCCESS)
            # read given file and check if it is conform to the xml syntax
            state_manager.add_step('Read file and check if it is conform to the xml syntax')
            parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
            etree.parse(file_to_be_checked, parser)
            state_manager.set_step_status(Status.SUCCESS)
    except etree.XMLSyntaxError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.add_step('Validate file against official xml schema')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    # load aas xml schema
    aas_xml_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)
    parser = etree.XMLParser(schema=aas_xml_schema)

    state_manager.add_step('Validate file against official xml schema')
    # validate given file against schema
    try:
        with open(file_path, 'rb') as file_to_be_checked:
            etree.parse(file_to_be_checked, parser=parser)
    except etree.ParseError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        return

    state_manager.set_step_status(Status.SUCCESS)
    return


def check_deserialization(file_path: str, state_manager: ComplianceToolStateManager,
                          file_info: Optional[str] = None) -> model.DictObjectStore:
    """
    Deserializes a XML AAS file and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Add the steps: `Open {} file` and `Read {} file` and `Check if it is conform to the xml schema`

    :param file_path: Given file which should be deserialized
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    :param file_info: Additional information about the file for name of the steps
    :return: The deserialized object store
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    # create handler to get logger info
    logger_deserialization = logging.getLogger(xml_deserialization.__name__)
    logger_deserialization.addHandler(state_manager)
    logger_deserialization.propagate = False
    logger_deserialization.setLevel(logging.INFO)

    if file_info:
        state_manager.add_step('Open {} file'.format(file_info))
    else:
        state_manager.add_step('Open file')
    try:
        # open given file
        file_to_be_checked = open(file_path, 'rb')
    except IOError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        if file_info:
            state_manager.add_step('Read file {} and check if it is deserializable'.format(file_info))
        else:
            state_manager.add_step('Read file and check if it is deserializable')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return model.DictObjectStore()

    with file_to_be_checked:
        state_manager.set_step_status(Status.SUCCESS)
        # read given file and check if it is conform to the official xml schema
        if file_info:
            state_manager.add_step('Read file {} and check if it is deserializable'.format(file_info))
        else:
            state_manager.add_step('Read file and check if it is deserializable')
        obj_store = xml_deserialization.read_aas_xml_file(file_to_be_checked, failsafe=True)

    state_manager.set_step_status_from_log()

    return obj_store


def check_aas_example(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if a file contains all elements of the aas example and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Calls the :meth:`~aas.compliance_tool.compliance_check_xml.check_deserialization` and add the steps: `Check if data
    is equal to example data`

    :param file_path: Given file which should be checked
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    """
    # create handler to get logger info
    logger_example = logging.getLogger(example_aas.__name__)
    logger_example.addHandler(state_manager)
    logger_example.propagate = False
    logger_example.setLevel(logging.INFO)

    obj_store = check_deserialization(file_path, state_manager)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if data is equal to example data')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False)

    state_manager.add_step('Check if data is equal to example data')
    checker.check_object_store(obj_store, create_example())

    state_manager.add_log_records_from_data_checker(checker)


def check_xml_files_equivalence(file_path_1: str, file_path_2: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if two xml files contain the same elements in any order and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Calls the :meth:`~aas.compliance_tool.compliance_check_xml.check_deserialization` for each file and add the steps:
    `Check if data in files are equal`

    :param file_path_1: Given first file which should be checked
    :param file_path_2: Given second file which should be checked
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    obj_store_1 = check_deserialization(file_path_1, state_manager, 'first')

    obj_store_2 = check_deserialization(file_path_2, state_manager, 'second')

    if state_manager.status is Status.FAILED:
        state_manager.add_step('Check if data in files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False)
    try:
        state_manager.add_step('Check if data in files are equal')
        checker.check_object_store(obj_store_1, obj_store_2)
    except (KeyError, AssertionError) as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        return

    state_manager.add_log_records_from_data_checker(checker)
