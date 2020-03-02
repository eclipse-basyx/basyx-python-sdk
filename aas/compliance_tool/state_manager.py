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


class ComplianceToolStateManager(logging.Handler):
    """
    A state manager to store steps while performing a compliance test. The manager provides functionalities to:
    1. add a new step
    2. set the step status
    3. add logs to a step by hand
    4. add logs to a step from a data checker
    5. be used as a logging.Handler which adds logs to the actual step
    """
    def __init__(self):
        """
        steps: List of steps. Each step consist of a step name, a step status and LogRecords belong to to this step.
               The step name have to be unique in the list.
        """
        super().__init__()
        self.steps: List[List[str, Status, List[logging.LogRecord]]] = []

    @property
    def status(self):
        status: Status = Status.SUCCESS
        for step in self.steps:
            if status < step[1]:
                status = step[1]
        return status

    def add_step(self, name: str):
        self.steps.append([name, Status.NOT_EXECUTED, []])

    def add_log_record(self, record: logging.LogRecord):
        self.steps[-1][2].append(record)

    def set_step_status(self, status: Status):
        self.steps[-1][1] = status

    def add_log_records_from_data_checker(self, data_checker: DataChecker):
        x = any(True for _ in data_checker.failed_checks)
        self.steps[-1][1] = Status.SUCCESS if not any(True for _ in data_checker.failed_checks) else Status.FAILED
        for check in data_checker.checks:
            self.steps[-1][2].append(logging.LogRecord(name=logging.getLogger().name,
                                                       level=logging.INFO if check.result else logging.ERROR,
                                                       pathname='',
                                                       lineno=0,
                                                       msg=repr(check),
                                                       args=(),
                                                       exc_info=None))

    def get_error_logs_from_step(self, index: int) -> List[logging.LogRecord]:
        return [x for x in self.steps[index][2] if x.levelno == logging.ERROR or x.levelno == logging.WARNING]

    def get_step_string(self, index: int, verbose_level: int = False) -> str:
        if self.steps[index][1] == Status.SUCCESS:
            string = 'SUCCESS: '
        elif self.steps[index][1] == Status.FAILED:
            string = 'FAILED: '
        elif self.steps[index][1] == Status.NOT_EXECUTED:
            string = 'NOT EXECUTED: '
        else:
            raise NotImplementedError
        string += self.steps[index][0]
        if verbose_level == 1:
            for log in self.steps[index][2]:
                if log.levelno < logging.WARNING:
                    continue
                string += '\n\t- {}: {}'.format(log.levelname, log.getMessage())
        if verbose_level == 2:
            for log in self.steps[index][2]:
                string += '\n\t- {}: {}'.format(log.levelname, log.getMessage())
        return string

    def emit(self, record: logging.LogRecord):
        self.steps[-1][2].append(record)
