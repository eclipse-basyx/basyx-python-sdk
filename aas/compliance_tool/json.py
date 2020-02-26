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

check_json_files_conform: Checks if two json files have the same data regardless of their order
"""
import io
import json
import logging
import os

import jsonschema  # type: ignore

from aas import model
from aas.adapter.json import json_deserialization
from aas.examples.data import example_aas
from aas.examples.data._helper import AASDataChecker
from aas.compliance_tool.helper import MessageLogger, LoggingMessage, MessageCategory

dirname = os.path.dirname
JSON_SCHEMA_FILE = os.path.join(dirname(dirname(dirname(__file__))), 'test\\adapter\\json\\aasJSONSchemaV2.0.json')


class LogFilter(logging.Filter):
    def __init__(self, level):
        self.__level = level

    def filter(self, log_record):
        return log_record.levelno <= self.__level


def check_schema(file_path: str, logger: MessageLogger) -> None:
    try:
        # open given file
        file_to_be_checked = open(file_path, 'r', encoding='utf-8-sig')
        # read given file and check if it is conform to the json syntax
        json_to_be_checked = json.load(file_to_be_checked)
    except FileNotFoundError as error:
        logger.add_msg(LoggingMessage('Unable to open json file: {}'.format(file_path), str(error),
                                      MessageCategory.ERROR))
        return
    except json.decoder.JSONDecodeError as error:
        logger.add_msg(LoggingMessage('Unable to deserialize json file: {}'.format(file_path), str(error),
                                      MessageCategory.ERROR))
        file_to_be_checked.close()
        return
    file_to_be_checked.close()

    # load json schema
    json_file = open(JSON_SCHEMA_FILE, 'r', encoding='utf-8-sig')
    aas_json_schema = json.load(json_file)
    json_file.close()

    # validate given file against schema
    try:
        jsonschema.validate(instance=json_to_be_checked, schema=aas_json_schema)
    except jsonschema.exceptions.ValidationError as error:
        logger.add_msg(LoggingMessage('Validation of file {} was not successfull'.format(file_path), str(error),
                                      MessageCategory.ERROR))
        return

    logger.add_msg(LoggingMessage('Schema check of file {} was successful'.format(file_path),
                                  '', MessageCategory.SUCCESS))
    return


def check_deserialization(file_path: str, failsafe: bool, logger: MessageLogger) -> model.DictObjectStore:
    # configure logger of json_deserialization.py to avoid consol output
    tmp_file = io.StringIO()
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, stream=tmp_file)

    # create handler to get logger info
    logger_deserialization = logging.getLogger(json_deserialization.__name__)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_error = io.StringIO()
    handler_error = logging.StreamHandler(file_error)
    handler_error.setLevel(logging.ERROR)
    handler_error.setFormatter(formatter)
    file_warning = io.StringIO()
    handler_warning = logging.StreamHandler(file_warning)
    handler_warning.setLevel(logging.WARNING)
    handler_warning.addFilter(LogFilter(logging.WARNING))
    handler_warning.setFormatter(formatter)
    file_info = io.StringIO()
    handler_info = logging.StreamHandler(file_info)
    handler_info.setLevel(logging.INFO)
    handler_info.addFilter(LogFilter(logging.INFO))
    handler_info.setFormatter(formatter)
    logger_deserialization.addHandler(handler_error)
    logger_deserialization.addHandler(handler_warning)
    logger_deserialization.addHandler(handler_info)

    try:
        # open given file
        file_to_be_checked = open(file_path, 'r', encoding='utf-8-sig')
        # read given file and check if it is conform to the json schema
        obj_store = json_deserialization.read_json_aas_file(file_to_be_checked, failsafe)
    except FileNotFoundError as error:
        logger.add_msg(LoggingMessage('Unable to open json file: {}'.format(file_path), str(error),
                                      MessageCategory.ERROR))
        return model.DictObjectStore()
    except (KeyError, TypeError) as error:
        logger.add_msg(LoggingMessage('Unable to deserialize json file: {}'.format(file_path), str(error),
                                      MessageCategory.ERROR))
        file_to_be_checked.close()
        return model.DictObjectStore()
    file_to_be_checked.close()

    # add logger information to output
    if failsafe:
        if file_error.getvalue() != "":
            logger.add_msg(LoggingMessage('Unable to deserialize json file: {}'.format(file_path),
                                          str(file_error.getvalue())+str(file_warning.getvalue()),
                                          MessageCategory.ERROR))
            return model.DictObjectStore()
        else:
            logger.add_msg(LoggingMessage('Deserialization check of file {} was successful'.format(file_path),
                                          str(file_warning.getvalue())+str(file_info.getvalue()),
                                          MessageCategory.SUCCESS))
    else:
        if file_warning.getvalue() != "":
            logger.add_msg(LoggingMessage('Unable to deserialize json file: {}'.format(file_path),
                                          str(file_warning.getvalue()), MessageCategory.ERROR))
            return model.DictObjectStore()
        else:
            logger.add_msg(LoggingMessage('Deserialization check of file {} was successful'.format(file_path),
                                          str(file_info.getvalue()), MessageCategory.SUCCESS))
    return obj_store


def check_aas_example(file_path: str, failsafe: bool, logger: MessageLogger) -> None:
    # configure logger of json_deserialization.py to avoid consol output
    tmp_file = io.StringIO()
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, stream=tmp_file)

    logger_example = logging.getLogger(example_aas.__name__)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_warning = io.StringIO()
    handler_warning = logging.StreamHandler(file_warning)
    handler_warning.setLevel(logging.WARNING)
    handler_warning.addFilter(LogFilter(logging.WARNING))
    handler_warning.setFormatter(formatter)
    file_info = io.StringIO()
    handler_info = logging.StreamHandler(file_info)
    handler_info.setLevel(logging.INFO)
    handler_info.addFilter(LogFilter(logging.INFO))
    handler_info.setFormatter(formatter)
    logger_example.addHandler(handler_warning)
    logger_example.addHandler(handler_info)

    obj_store = check_deserialization(file_path, False, logger)

    if logger.error:
        logger.add_msg(LoggingMessage('Could not check against example data cause of error in deserialization of '
                                      'file {}'.format(file_path), '', MessageCategory.ERROR))
        return

    checker = AASDataChecker(raise_immediately=(not failsafe))
    try:
        example_aas.check_full_example(checker, obj_store, failsafe)
    except (KeyError, AssertionError) as error:
        logger.add_msg(LoggingMessage('Data in file {} is not equal to example data'.format(file_path),
                                      str(error), MessageCategory.ERROR))
        return

    if len(list(checker.failed_checks)) > 0 or file_warning.getvalue() != "":
        msg = ''
        for x in checker.failed_checks:
            msg += '{}\n'.format(x)
        logger.add_msg(LoggingMessage('Data in file {} is not equal to example data'.format(file_path),
                                      msg, MessageCategory.ERROR))
    else:
        msg = ''
        for x in checker.successful_checks:
            msg += '{}\n'.format(x)
        logger.add_msg(LoggingMessage('Data in file {} is equal to example data'.format(file_path),
                                      msg, MessageCategory.SUCCESS))


def check_json_files_conform(file_path_1: str, file_path_2: str, failsafe: bool, logger: MessageLogger) -> None:
    # configure logger of json_deserialization.py to avoid consol output
    tmp_file = io.StringIO()
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, stream=tmp_file)

    obj_store_1 = check_deserialization(file_path_1, False, logger)

    if logger.error:
        logger.add_msg(LoggingMessage('Could not check files cause of error in deserialization of '
                                      'file {}'.format(file_path_1), '', MessageCategory.ERROR))
        return

    obj_store_2 = check_deserialization(file_path_2, False, logger)

    if logger.error:
        logger.add_msg(LoggingMessage('Could not check files cause of error in deserialization of '
                                      'file {}'.format(file_path_2), '', MessageCategory.ERROR))
        return

    checker = AASDataChecker(raise_immediately=(not failsafe))
    try:
        checker.check_object_store(obj_store_1, obj_store_2)
    except (KeyError, AssertionError) as error:
        logger.add_msg(LoggingMessage('Data in file {} is not equal to data in file {}'.format(file_path_1,
                                                                                               file_path_2),
                                      str(error), MessageCategory.ERROR))
        return

    if len(list(checker.failed_checks)) > 0:
        msg = ''
        for x in checker.failed_checks:
            msg += '{}\n'.format(x)
        logger.add_msg(LoggingMessage('Data in file {} is not equal to data in file {}'.format(file_path_1,
                                                                                               file_path_2),
                                      msg, MessageCategory.ERROR))
    else:
        msg = ''
        for x in checker.successful_checks:
            msg += '{}\n'.format(x)
        logger.add_msg(LoggingMessage('Data in file {} is equal to data in file {}'.format(file_path_1, file_path_2),
                                      msg, MessageCategory.SUCCESS))
