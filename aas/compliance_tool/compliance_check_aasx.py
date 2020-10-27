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
Module which offers functions to use in a confirmation tool related to AASX files

check_deserialization: Checks if a AASX file can be deserialized

check_aas_example: Checks if a AASX file consist the data of the example data defined in
                   aas.examples.data.example_aas.py

check_aasx_files_equivalence: Checks if two AASX files have the same data regardless of their order

All functions reports any issues using the given StateManager by adding new steps and associated LogRecords
"""
import datetime
import json
import logging
from typing import Optional, Tuple

import pyecma376_2

from .. import model
from ..adapter import aasx
from ..examples.data import example_aas, create_example_aas_binding
from ..examples.data._helper import AASDataChecker, DataChecker
from .state_manager import ComplianceToolStateManager, Status


def check_deserialization(file_path: str, state_manager: ComplianceToolStateManager,
                          file_info: Optional[str] = None) \
        -> Tuple[model.DictObjectStore, aasx.DictSupplementaryFileContainer, pyecma376_2.OPCCoreProperties]:
    """
    Read a AASX file and reports any issues using the given StateManager

    add the steps: 'Open {} file' and 'Read {} file'

    :param file_path: given file which should be deserialized
    :param state_manager: manager to log the steps
    :param file_info: additional information about the file for name of the steps
    :return: returns the read object store
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    # create handler to get logger info
    logger_deserialization = logging.getLogger(aasx.__name__)
    logger_deserialization.addHandler(state_manager)
    logger_deserialization.propagate = False
    logger_deserialization.setLevel(logging.INFO)

    if file_info:
        state_manager.add_step('Open {} file'.format(file_info))
    else:
        state_manager.add_step('Open file')
    try:
        # open given file
        reader = aasx.AASXReader(file_path)
        state_manager.set_step_status_from_log()
    except ValueError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.set_step_status_from_log()
        state_manager.add_step('Read file')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return model.DictObjectStore(), aasx.DictSupplementaryFileContainer(), pyecma376_2.OPCCoreProperties()

    try:
        # read given file
        state_manager.add_step('Read file')
        obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        files = aasx.DictSupplementaryFileContainer()
        reader.read_into(obj_store, files)
        new_cp = reader.get_core_properties()
        state_manager.set_step_status(Status.SUCCESS)
    except ValueError as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.set_step_status_from_log()
        return model.DictObjectStore(), aasx.DictSupplementaryFileContainer(), pyecma376_2.OPCCoreProperties()
    finally:
        reader.close()

    return obj_store, files, new_cp


def check_aas_example(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if a file contains all elements of the aas example and reports any issues using the given StateManager

    calls the check_deserialization and add the steps: 'Check if data is equal to example data'

    :param file_path: given file which should be checked
    :param state_manager: manager to log the steps
    """
    # create handler to get logger info
    logger_example = logging.getLogger(example_aas.__name__)
    logger_example.addHandler(state_manager)
    logger_example.propagate = False
    logger_example.setLevel(logging.INFO)

    obj_store, files, cp_new = check_deserialization(file_path, state_manager)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if data is equal to example data')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False)

    state_manager.add_step('Check if data is equal to example data')
    checker.check_object_store(obj_store, create_example_aas_binding())
    state_manager.add_log_records_from_data_checker(checker)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_step('Check if core properties are equal')
    # Create OPC/AASX core properties
    cp = pyecma376_2.OPCCoreProperties()
    cp.created = datetime.datetime(2020, 1, 1, 0, 0, 0)
    cp.creator = "PyI40AAS Testing Framework"

    checker2 = DataChecker(raise_immediately=False)
    assert (isinstance(cp_new.created, datetime.datetime))
    duration = cp_new.created - cp.created
    checker2.check(duration.microseconds < 20, "created must be {}".format(cp.created))
    checker2.check(cp_new.creator == "PyI40AAS Testing Framework", "creator must be 'PyI40AAS Testing Framework'")
    checker2.check(cp_new.lastModifiedBy is cp.lastModifiedBy, "lastModifiedBy must be {}".format(cp.lastModifiedBy))
    state_manager.add_log_records_from_data_checker(checker2)
    state_manager.set_step_status(Status.SUCCESS)


def check_aasx_files_equivalence(file_path_1: str, file_path_2: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if two aasx files contain the same elements in any order and reports any issues using the given StateManager

    calls the check_deserialization for ech file and add the steps: 'Check if data in files are equal'

    :param file_path_1: given first file which should be checked
    :param file_path_2: given second file which should be checked
    :param state_manager: manager to log the steps
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    obj_store_1, files_1, cp_1 = check_deserialization(file_path_1, state_manager, 'first')

    obj_store_2, files_2, cp_2 = check_deserialization(file_path_2, state_manager, 'second')

    if state_manager.status is Status.FAILED:
        state_manager.add_step('Check if data in files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False)
    try:
        state_manager.add_step('Check if data in files are equal')
        checker.check_object_store(obj_store_1, obj_store_2)
    except (KeyError, AssertionError) as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_log_records_from_data_checker(checker)

    if state_manager.status is Status.FAILED:
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_step('Check if core properties are equal')
    checker2 = DataChecker(raise_immediately=False)
    assert (isinstance(cp_1.created, datetime.datetime))
    assert (isinstance(cp_2.created, datetime.datetime))
    duration = cp_1.created - cp_2.created
    checker2.check(duration.microseconds < 20, "created must be {}".format(cp_1.created), value=cp_2.created)
    checker2.check(cp_1.creator == cp_2.creator, "creator must be {}".format(cp_1.creator), value=cp_2.creator)
    checker2.check(cp_1.lastModifiedBy == cp_2.lastModifiedBy, "lastModifiedBy must be {}".format(cp_1.lastModifiedBy),
                   value=cp_2.lastModifiedBy)
    state_manager.add_log_records_from_data_checker(checker2)
