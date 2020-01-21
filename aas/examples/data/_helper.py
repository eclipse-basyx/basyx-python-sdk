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
Helper classes for checking example data structures for completeness and correctness and reporting the check results.
"""

import pprint
from typing import List, NamedTuple, Iterator, Dict, Any


class CheckResult(NamedTuple):
    expectation: str
    result: bool
    data: Dict[str, Any]

    def __repr__(self):
        return "{}: {} ({})".format("OK  " if self.result else "FAIL",
                                    self.expectation,
                                    ", ".join("{}={}".format(k, pprint.pformat(v, depth=2, width=2 ** 14, compact=True))
                                              for k, v in self.data.items()))


class DataChecker:
    """
    A helper class to perform multiple checks/assertions of given data and report the result.

    Typical usage:

        data = {'a': 1, 'b': 2}
        dc = DataChecker()
        dc.check(len(data) > 0, "data is not empty")
        if dc.check('a' in data, "a is in data", keys=list(data.keys())):
            dc.check(data['a'] == data['b'], "a == b", a=data['a'], b=data['b'])
            dc.check(data['a'] > 0, "a is positive", a=data['a'])

        for result in dc.failed_checks:
            print(result)
    """
    def __init__(self, raise_immediately: bool = False):
        """
        :param raise_immediately: If True, a failed check will raise an AssertionError instead of gathering the
                                  CheckResults for later analysis
        """
        self.checks: List[CheckResult] = []
        self.raise_immediately = raise_immediately

    def check(self, expression: bool, expectation: str, **kwargs: Dict[str, Any]) -> bool:
        """
        Checks if `expression` is True and adds stores the check result for later analysis.

        :param expression: The boolean to be checked for
        :param expectation: A string describing, what the data was expected to look like (for later listing of
                            successful and failed checks)
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        if not expression and self.raise_immediately:
            raise AssertionError("Check failed: {}".format(expectation), kwargs)
        self.checks.append(CheckResult(expectation, expression, kwargs))
        return expression

    def extend(self, other: "DataChecker") -> None:
        """
        Extend the list of check results with another DataChecker's check results
        """
        self.checks.extend(other.checks)

    @property
    def failed_checks(self) -> Iterator[CheckResult]:
        return (result for result in self.checks if not result.result)

    @property
    def successful_checks(self) -> Iterator[CheckResult]:
        return (result for result in self.checks if result.result)

    def raise_failed(self) -> None:
        """
        Raise AssertionError if any check failed
        """
        failed = list(self.failed_checks)
        if len(failed) > 0:
            raise AssertionError("{} of {} checks failed".format(len(failed), len(self.checks)),
                                 [f.expectation for f in failed])
