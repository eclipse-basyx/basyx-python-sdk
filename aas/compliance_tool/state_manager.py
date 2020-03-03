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
This module defines a State Manager to store LogRecords for single steps in a compliance check of the compliance tool
"""
import logging
import enum
from typing import List
from aas.examples.data._helper import DataChecker


@enum.unique
class Status(enum.IntEnum):
    SUCCESS = 0
    FAILED = 1
    NOT_EXECUTED = 2


class Step:
    """
    A step is a object which is used in the ComplianceToolStateManager for a new step in a check.

    :ivar name: Name of the step
    :ivar status: status of the step from type Status
    :ivar log_list: list of LogRecords which belong to this step
    """
    def __init__(self, name: str, status: Status, log_list: List[logging.LogRecord]):
        self.name = name
        self.status = status
        self.log_list = log_list


class ComplianceToolStateManager(logging.Handler):
    """
    A state manager to store steps while performing a compliance test. The manager provides functionalities to:
    1. add a new step
    2. set the step status
    3. add logs to a step by hand
    4. add logs to a step from a data checker
    5. be used as a logging.Handler which adds logs to the actual step

    :ivar steps: List of Step
    """
    def __init__(self):
        """
        steps: List of steps. Each step consist of a step name, a step status and LogRecords belong to to this step.
               The step name have to be unique in the list.
        """
        super().__init__()
        self.steps: List[Step] = []

    @property
    def status(self) -> Status:
        """
        Determine the status of all steps in following way:
        1. If there is at least one step with status = NOT_EXECUTED than NOT_EXECUTED will be returned
        2. If there is at least one step with status = FAILED than FAILED will be returned
        3. Else status SUCCESS will be returned

        :return: status of the manager
        """
        status: Status = Status.SUCCESS
        for step in self.steps:
            if status < step.status:
                status = step.status
        return status

    def add_step(self, name: str) -> None:
        """
        Adding a new step to the manager with a given name, status = NOT_EXECUTED and an empty list of records

        :param name: Name of the step
        """
        self.steps.append(Step(name, Status.NOT_EXECUTED, []))

    def add_log_record(self, record: logging.LogRecord) -> None:
        """
        Adds a LogRecord to the log list of the acutal step

        :param record: LogRecord which should be added to the actual step
        """
        self.steps[-1].log_list.append(record)

    def set_step_status(self, status: Status) -> None:
        """
        Sets the status of the actual step

        :param status: status which should be set
        """
        self.steps[-1].status = status

    def add_log_records_from_data_checker(self, data_checker: DataChecker) -> None:
        """
        Sets the status of the actual step and convert the checks to LogRecords and adds these to the actual step

        step: FAILED if the DataChecker consist at least one failed check otherwise SUCCESS

        :param data_checker: DataChecker which checks should be added to the actual step
        """
        self.steps[-1].status = Status.SUCCESS if not any(True for _ in data_checker.failed_checks) else Status.FAILED
        for check in data_checker.checks:
            self.steps[-1].log_list.append(logging.LogRecord(name=logging.getLogger(__name__).name,
                                                             level=logging.INFO if check.result else logging.ERROR,
                                                             pathname='',
                                                             lineno=0,
                                                             msg=repr(check),
                                                             args=(),
                                                             exc_info=None))

    def get_error_logs_from_step(self, index: int) -> List[logging.LogRecord]:
        """
        Returns a list of LogRecords of a step where the log level is logging.ERROR or logging.WARNING

        :param index: step index in the step list of the manager
        :return: List of LogRecords with log levell logging.ERROR or logging.WARNING
        """
        return [x for x in self.steps[index].log_list if x.levelno == logging.ERROR or x.levelno == logging.WARNING]

    def get_step_string(self, index: int, verbose_level: int = 0) -> str:
        """
        Creates a string for the step containing the status, the step name and the LogRecords if wanted

        :param index:  step index in the step list of the manager
        :param verbose_level: Decision which kind of LogRecords should be in the string
                              0: No LogRecords
                              1: Only LogRecords with log level >= logging.WARNING
                              2: All LogRecords
        :return: formatted string of the step
        """
        if self.steps[index].status == Status.SUCCESS:
            string = 'SUCCESS: '
        elif self.steps[index].status == Status.FAILED:
            string = 'FAILED: '
        elif self.steps[index].status == Status.NOT_EXECUTED:
            string = 'NOT EXECUTED: '
        else:
            raise NotImplementedError
        string += self.steps[index].name
        if verbose_level == 1:
            for log in self.steps[index].log_list:
                if log.levelno < logging.WARNING:
                    continue
                string += '\n\t- {}: {}'.format(log.levelname, log.getMessage())
        if verbose_level == 2:
            for log in self.steps[index].log_list:
                if log.levelno == logging.INFO:
                    string += '\n\t- {}:  {}'.format(log.levelname, log.getMessage())
                else:
                    string += '\n\t- {}: {}'.format(log.levelname, log.getMessage())
        return string

    def emit(self, record: logging.LogRecord):
        """
        logging.Handler function for adding LogRecords from a logger to the actual step

        :param record: LogRecord which should be added
        """
        self.steps[-1].log_list.append(record)
