# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Module which offers functions to use in a confirmation tool related to AASX files

All functions reports any issues using the given
:class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager` by adding new steps and associated
:class:`LogRecords <logging.LogRecord>`
"""
import datetime
import logging
from typing import Optional, Tuple, cast

import pyecma376_2
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.adapter.json import json_deserialization
from basyx.aas.adapter.xml import xml_deserialization
from basyx.aas.examples.data import create_example_aas_binding, example_aas
from basyx.aas.examples.data._helper import AASDataChecker, DataChecker

from aas_compliance_tool.state_manager import ComplianceToolStateManager, Status


def check_deserialization(file_path: str, state_manager: ComplianceToolStateManager,
                          file_info: Optional[str] = None) \
        -> Tuple[model.DictIdentifiableStore, aasx.DictSupplementaryFileContainer, pyecma376_2.OPCCoreProperties]:
    """
    Read a AASX file and reports any issues using the given
    :class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Add the steps: `Open {} file' and 'Read {} file`

    :param file_path: Given file which should be deserialized
    :param state_manager: Manager to log the steps
    :param file_info: Additional information about the file for name of the steps
    :return: The read object store
    """
    logger_names = [
        'compliance_check',
        aasx.__name__,
        xml_deserialization.__name__,
        json_deserialization.__name__,
    ]
    for name in logger_names:
        logger = logging.getLogger(name)
        logger.addHandler(state_manager)
        logger.propagate = False
        logger.setLevel(logging.INFO)

    if file_info:
        state_manager.add_step('Open {} file'.format(file_info))
    else:
        state_manager.add_step('Open file')
    try:
        # open given file
        reader = aasx.AASXReader(file_path)
        state_manager.set_step_status_from_log()
    except (FileNotFoundError, ValueError) as error:
        logger.error(error)
        state_manager.set_step_status_from_log()
        state_manager.add_step('Read file')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return model.DictIdentifiableStore(), aasx.DictSupplementaryFileContainer(), pyecma376_2.OPCCoreProperties()

    try:
        # read given file
        state_manager.add_step('Read file')
        identifiable_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        files = aasx.DictSupplementaryFileContainer()
        reader.read_into(identifiable_store, files)
        new_cp = reader.get_core_properties()
        state_manager.set_step_status(Status.SUCCESS)
    except (ValueError, KeyError) as error:
        logger.error(error)
        state_manager.set_step_status(Status.FAILED)
        return model.DictIdentifiableStore(), aasx.DictSupplementaryFileContainer(), pyecma376_2.OPCCoreProperties()
    finally:
        reader.close()

    return identifiable_store, files, new_cp


def check_aas_example(file_path: str, state_manager: ComplianceToolStateManager, **kwargs) -> None:
    """
    Checks if a file contains all elements of the aas example and reports any issues using the given
    :class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager`

    Calls the :meth:`~basyx.aas.compliance_tool.compliance_check_aasx.check_deserialization` and add the steps:
    `Check if data is equal to example data`

    :param file_path: Given file which should be checked
    :param state_manager: :class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    :param kwargs: Additional arguments to pass to :class:`~basyx.aas.examples.data._helper.AASDataChecker`
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

    identifiable_store, files, cp_new = check_deserialization(file_path, state_manager)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if data is equal to example data')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if supplementary files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False, **kwargs)

    state_manager.add_step('Check if data is equal to example data')
    example_data = create_example_aas_binding()
    checker.check_identifiable_store(identifiable_store, example_data)
    state_manager.add_log_records_from_data_checker(checker)

    if state_manager.status in (Status.FAILED, Status.NOT_EXECUTED):
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if supplementary files are equal')
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
    if checker2.check(isinstance(cp_new.created, datetime.datetime), "core property created must be of type datetime",
                      created=type(cp_new.created)):
        duration = cast(datetime.datetime, cp_new.created) - cp.created
        checker2.check(duration.microseconds < 20, "created must be {}".format(cp.created), created=cp_new.created)

    checker2.check(cp_new.creator == cp.creator, "creator must be {}".format(cp.creator), creator=cp_new.creator)
    checker2.check(cp_new.description == cp.description, "description must be {}".format(cp.description),
                   description=cp_new.description)
    checker2.check(cp_new.lastModifiedBy == cp.lastModifiedBy, "lastModifiedBy must be {}".format(cp.lastModifiedBy),
                   lastModifiedBy=cp_new.lastModifiedBy)

    if checker2.check(isinstance(cp_new.modified, datetime.datetime), "modified must be of type datetime",
                      modified=type(cp_new.modified)):
        duration = cast(datetime.datetime, cp_new.modified) - cp.modified
        checker2.check(duration.microseconds < 20, "modified must be {}".format(cp.modified), modified=cp_new.modified)

    checker2.check(cp_new.revision == cp.revision, "revision must be {}".format(cp.revision), revision=cp_new.revision)
    checker2.check(cp_new.version == cp.version, "version must be {}".format(cp.version), version=cp_new.version)
    checker2.check(cp_new.title == cp.title, "title must be {}".format(cp.title), title=cp_new.title)

    state_manager.add_log_records_from_data_checker(checker2)

    # Check if file in file object is the same
    state_manager.add_step('Check if supplementary files are equal')
    file_checker = DataChecker(raise_immediately=False)

    list_of_id_shorts = ["ExampleSubmodelCollection", "ExampleFile"]
    identifiable = example_data.get_item("https://example.org/Test_Submodel")
    for id_short in list_of_id_shorts:
        identifiable = identifiable.get_referable(id_short)
    file_name = identifiable.value
    if file_checker.check(file_name in files, f"Supplementary File {file_name} must exist"):
        test_file_checksum = 'b18229b24a4ee92c6c2b6bc6a8018563b17472f1150d35d5a5945afeb447ed44'
        file_checker.check(
            files.get_sha256(file_name).hex() == test_file_checksum,
            f"Supplementary File {file_name} checksum must be '{test_file_checksum}'.",
            value=files.get_sha256(file_name)
        )

    state_manager.add_log_records_from_data_checker(file_checker)


def check_aasx_files_equivalence(file_path_1: str, file_path_2: str, state_manager: ComplianceToolStateManager,
                                 **kwargs) -> None:
    """
    Checks if two aasx files contain the same elements in any order and reports any issues using the given
    :class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager`

    calls the :meth:`~basyx.aas.compliance_tool.compliance_check_aasx.check_deserialization` for each file and add the
    steps: `Check if data in files are equal`

    :param file_path_1: Given first file which should be checked
    :param file_path_2: Given second file which should be checked
    :param state_manager: :class:`~basyx.aas.compliance_tool.state_manager.ComplianceToolStateManager` to log the steps
    :param kwargs: Additional arguments to pass to :class:`~basyx.aas.examples.data._helper.AASDataChecker`
    """
    logger = logging.getLogger('compliance_check')
    logger.addHandler(state_manager)
    logger.propagate = False
    logger.setLevel(logging.INFO)

    identifiable_store_1, files_1, cp_1 = check_deserialization(file_path_1, state_manager, 'first')

    identifiable_store_2, files_2, cp_2 = check_deserialization(file_path_2, state_manager, 'second')

    if state_manager.status >= Status.FAILED:
        state_manager.add_step('Check if data in files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if supplementary files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    checker = AASDataChecker(raise_immediately=False, **kwargs)
    try:
        state_manager.add_step('Check if data in files are equal')
        checker.check_identifiable_store(identifiable_store_1, identifiable_store_2)
    except (KeyError, AssertionError) as error:
        state_manager.set_step_status(Status.FAILED)
        logger.error(error)
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if supplementary files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_log_records_from_data_checker(checker)

    if state_manager.status >= Status.FAILED:
        state_manager.add_step('Check if core properties are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        state_manager.add_step('Check if supplementary files are equal')
        state_manager.set_step_status(Status.NOT_EXECUTED)
        return

    state_manager.add_step('Check if core properties are equal')
    checker2 = DataChecker(raise_immediately=False)
    checker2.check(isinstance(cp_1.created, datetime.datetime),
                   "core property created of first file must be of type datetime",
                   created=type(cp_1.created))
    checker2.check(isinstance(cp_2.created, datetime.datetime),
                   "core property created of second file must be of type datetime",
                   created=type(cp_2.created))

    if any(True for _ in checker2.failed_checks):
        state_manager.add_log_records_from_data_checker(checker2)
        return

    duration = cast(datetime.datetime, cp_1.created) - cast(datetime.datetime, cp_2.created)
    checker2.check(duration.microseconds < 20, "created must be {}".format(cp_1.created), value=cp_2.created)
    checker2.check(cp_1.creator == cp_2.creator, "creator must be {}".format(cp_1.creator), value=cp_2.creator)
    checker2.check(cp_1.lastModifiedBy == cp_2.lastModifiedBy, "lastModifiedBy must be {}".format(cp_1.lastModifiedBy),
                   value=cp_2.lastModifiedBy)
    checker2.check(cp_1.revision == cp_2.revision, "revision must be {}".format(cp_2.revision), revision=cp_1.revision)
    checker2.check(cp_1.version == cp_2.version, "version must be {}".format(cp_2.version), version=cp_1.version)
    checker2.check(cp_1.title == cp_2.title, "title must be {}".format(cp_2.title), title=cp_1.title)
    state_manager.add_log_records_from_data_checker(checker2)

    state_manager.add_step('Check if supplementary files are equal')

    file_checker = DataChecker(raise_immediately=False)
    for file_name in files_1:
        both_contain = file_checker.check(file_name in files_2,
                                          "second file must contain supplementary file {}".format(file_name))
        if both_contain:
            expected_type = files_1.get_content_type(file_name)
            file_checker.check(expected_type == files_2.get_content_type(file_name),
                               f"second file must contain supplementary file {file_name}"
                               " with content-type {expected_type}",
                               content_type=files_2.get_content_type(file_name))
            expected_checksum = files_1.get_sha256(file_name)
            file_checker.check(expected_checksum == files_2.get_sha256(file_name),
                               f"second file must contain supplementary file {file_name}"
                               f" with sha256 {expected_checksum.hex()}",
                               checksum=files_2.get_sha256(file_name).hex())

    for file_name in files_2:
        file_checker.check(file_name in files_1,
                           "first file must contain supplementary file {}".format(file_name))

    state_manager.add_log_records_from_data_checker(file_checker)
