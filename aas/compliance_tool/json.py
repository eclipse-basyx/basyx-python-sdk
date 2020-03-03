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
Module which offers functions to use in a confirmation tool related to json files

check_schema: Checks if a json file is conform to official JSON schema as defined in the 'Details of the Asset
              Administration Shell' specification of Plattform Industrie 4.0.

check_deserialization: Checks if a json file can be deserialized

check_aas_example: Checks if a json file consist the data of the example data defined in
                   aas.examples.data.example_aas.py

check_json_files_equivalence: Checks if two json files have the same data regardless of their order
"""
import json
import logging
import os
from typing import Optional

import jsonschema  # type: ignore

from aas import model
from aas.adapter.json import json_deserialization
from aas.examples.data import example_aas, create_example
from aas.examples.data._helper import AASDataChecker
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status

dirname = os.path.dirname
JSON_SCHEMA_FILE = os.path.join(dirname(__file__), '..', '..', 'test', 'adapter', 'json', 'aasJSONSchemaV2.0.json')
# TODO change path if schema is added to the project
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_schema(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    logger.addHandler(state_manager)
    try:
        # open given file
        state_manager.add_step('Open file')
        file_to_be_checked = open(file_path, 'r', encoding='utf-8-sig')
        state_manager.set_step_status(Status.SUCCESS)
        # read given file and check if it is conform to the json syntax
        state_manager.add_step('Read file and check if it is conform to the json syntax')
        json_to_be_checked = json.load(file_to_be_checked)
        state_manager.set_step_status(Status.SUCCESS)
    except FileNotFoundError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        return
    except json.decoder.JSONDecodeError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        file_to_be_checked.close()
        return
    file_to_be_checked.close()

    # load json schema
    json_file = open(JSON_SCHEMA_FILE, 'r', encoding='utf-8-sig')
    aas_json_schema = json.load(json_file)
    json_file.close()

    state_manager.add_step('Validate file against official json schema')
    # validate given file against schema
    try:
        jsonschema.validate(instance=json_to_be_checked, schema=aas_json_schema)
    except jsonschema.exceptions.ValidationError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        return

    state_manager.set_step_status(Status.SUCCESS)
    return


def check_deserialization(file_path: str, state_manager: ComplianceToolStateManager,
                          file_info: Optional[str] = None) -> model.DictObjectStore:
    logger.addHandler(state_manager)

    # create handler to get logger info
    logger_deserialization = logging.getLogger(json_deserialization.__name__)
    logger_deserialization.addHandler(state_manager)

    try:
        # open given file
        if file_info:
            state_manager.add_step('Open {} file'.format(file_info))
        else:
            state_manager.add_step('Open file')
        file_to_be_checked = open(file_path, 'r', encoding='utf-8-sig')
        state_manager.set_step_status(Status.SUCCESS)

        # read given file and check if it is conform to the official json schema
        if file_info:
            state_manager.add_step('Read {} file and check if it is conform to the json schema'.format(file_info))
        else:
            state_manager.add_step('Read file and check if it is conform to the json schema')
        obj_store = json_deserialization.read_json_aas_file(file_to_be_checked, True)
        state_manager.set_step_status(Status.SUCCESS)
    except FileNotFoundError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        return model.DictObjectStore()
    file_to_be_checked.close()
    if len(state_manager.steps[-1].log_list) > 0:
        state_manager.set_step_status(Status.FAILED)

    return obj_store


def check_aas_example(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    logger.addHandler(state_manager)

    # create handler to get logger info
    logger_example = logging.getLogger(example_aas.__name__)
    logger_example.addHandler(state_manager)

    obj_store = check_deserialization(file_path, state_manager)

    if state_manager.status == Status.FAILED:
        return

    checker = AASDataChecker(raise_immediately=False)

    state_manager.add_step('Check if data is equal to example data')
    checker.check_object_store(obj_store, create_example())

    state_manager.add_log_records_from_data_checker(checker)


def check_json_files_equivalence(file_path_1: str, file_path_2: str, state_manager: ComplianceToolStateManager) -> None:
    logger.addHandler(state_manager)

    obj_store_1 = check_deserialization(file_path_1, state_manager, 'first')

    if state_manager.status == Status.FAILED:
        return

    obj_store_2 = check_deserialization(file_path_2, state_manager, 'second')

    if state_manager.status == Status.FAILED:
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
