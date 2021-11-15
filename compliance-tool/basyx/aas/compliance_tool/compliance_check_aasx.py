# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
Module which offers functions to use in a confirmation tool related to AASX files

:meth:`~aas.compliance_tool.compliance_check_aasx.check_deserialization`: Checks if a AASX file can be deserialized

:meth:`~aas.compliance_tool.compliance_check_aasx.check_aas_example`: Checks if a AASX file consist the data of the
example data defined in aas.examples.data.example_aas.py

:meth:`~aas.compliance_tool.compliance_check_aasx.check_aasx_files_equivalence`: Checks if two AASX files have the same
data regardless of their order

All functions reports any issues using the given :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`
by adding new steps and associated LogRecords
"""
import datetime
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
    Read a AASX file and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Add the steps: `Open {} file' and 'Read {} file`

    :param file_path: Given file which should be deserialized
    :param state_manager: Manager to log the steps
    :param file_info: Additional information about the file for name of the steps
    :return: The read object store
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
        logger.error(error)
        state_manager.set_step_status(Status.FAILED)
        return model.DictObjectStore(), aasx.DictSupplementaryFileContainer(), pyecma376_2.OPCCoreProperties()
    finally:
        reader.close()

    return obj_store, files, new_cp


def check_aas_example(file_path: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if a file contains all elements of the aas example and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Calls the :meth:`~aas.compliance_tool.compliance_check_aasx.check_deserialization` and add the steps:
    `Check if data is equal to example data`

    :param file_path: Given file which should be checked
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

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
    example_data = create_example_aas_binding()
    checker.check_object_store(obj_store, example_data)
    state_manager.add_log_records_from_data_checker(checker)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_step('Check if core properties are equal')
    # Create OPC/AASX core properties
    cp = pyecma376_2.OPCCoreProperties()
    cp.created = datetime.datetime(2020, 1, 1, 0, 0, 0)
    cp.creator = "Eclipse BaSyx Python Testing Framework"
    cp.description = "Test_Description"
    cp.lastModifiedBy = "Eclipse BaSyx Python Testing Framework Compliance Tool"
    cp.modified = datetime.datetime(2020, 1, 1, 0, 0, 1)
    cp.revision = "1.0"
    cp.version = "2.0.1"
    cp.title = "Test Title"

    checker2 = DataChecker(raise_immediately=False)
    try:
        assert(isinstance(cp_new.created, datetime.datetime))
        checker2.check(isinstance(cp_new.created, datetime.datetime), "core property created must be of type datetime",
                       created=type(cp_new.created))
        duration = cp_new.created - cp.created
        checker2.check(duration.microseconds < 20, "created must be {}".format(cp.created), created=cp_new.created)
    except AssertionError:
        checker2.check(isinstance(cp_new.created, datetime.datetime), "core property created must be of type datetime",
                       created=type(cp_new.created))

    checker2.check(cp_new.creator == cp.creator, "creator must be {}".format(cp.creator), creator=cp_new.creator)
    checker2.check(cp_new.description == cp.description, "description must be {}".format(cp.description),
                   description=cp_new.description)
    checker2.check(cp_new.lastModifiedBy == cp.lastModifiedBy, "lastModifiedBy must be {}".format(cp.lastModifiedBy),
                   lastModifiedBy=cp_new.lastModifiedBy)
    try:
        assert(isinstance(cp_new.modified, datetime.datetime))
        checker2.check(isinstance(cp_new.modified, datetime.datetime), "modified bust be of type datetime",
                       modified=type(cp_new.modified))
        duration = cp_new.modified - cp.modified
        checker2.check(duration.microseconds < 20, "modified must be {}".format(cp.modified), modified=cp_new.modified)
    except AssertionError:
        checker2.check(isinstance(cp_new.modified, datetime.datetime), "modified bust be of type datetime",
                       modified=type(cp_new.modified))
    checker2.check(cp_new.revision == cp.revision, "revision must be {}".format(cp.revision), revision=cp_new.revision)
    checker2.check(cp_new.version == cp.version, "version must be {}".format(cp.version), version=cp_new.version)
    checker2.check(cp_new.title == cp.title, "title must be {}".format(cp.title), title=cp_new.title)

    # Check if file in file object is the same
    list_of_id_shorts = ["ExampleSubmodelCollectionUnordered", "ExampleFile"]
    obj = example_data.get_identifiable(model.Identifier("https://acplt.org/Test_Submodel", model.IdentifierType.IRI))
    for id_short in list_of_id_shorts:
        obj = obj.get_referable(id_short)
    obj2 = obj_store.get_identifiable(model.Identifier("https://acplt.org/Test_Submodel", model.IdentifierType.IRI))
    for id_short in list_of_id_shorts:
        obj2 = obj2.get_referable(id_short)
    try:
        sha_file = files.get_sha256(obj.value)
    except KeyError as error:
        state_manager.add_log_records_from_data_checker(checker2)
        logger.error(error)
        state_manager.set_step_status(Status.FAILED)
        return

    checker2.check(sha_file == files.get_sha256(obj2.value), "File of {} must be {}.".format(obj.value, obj2.value),
                   value=obj2.value)
    state_manager.add_log_records_from_data_checker(checker2)
    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.set_step_status(Status.FAILED)
    else:
        state_manager.set_step_status(Status.SUCCESS)


def check_aasx_files_equivalence(file_path_1: str, file_path_2: str, state_manager: ComplianceToolStateManager) -> None:
    """
    Checks if two aasx files contain the same elements in any order and reports any issues using the given
    :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager`

    calls the :meth:`~aas.compliance_tool.compliance_check_aasx.check_deserialization` for each file and add the steps:
    `Check if data in files are equal`

    :param file_path_1: Given first file which should be checked
    :param file_path_2: Given second file which should be checked
    :param state_manager: :class:`~aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
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
