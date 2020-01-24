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
from typing import List, NamedTuple, Iterator, Dict, Any, Type

from aas import model


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

    def check(self, expression: bool, expectation: str, **kwargs) -> bool:
        """
        Checks if `expression` is True and adds / stores the check result for later analysis.

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

    def check_object_equal(self, object_: object, expected_value: object, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is the same as expected_value and adds / stores the
        check result for later analysis.

        :param object_: The object which shall be checked
        :param expected_value: The expected object
        :return: The value of expression to be used in control statements
        """
        kwargs['object_'] = repr(object_)
        return self.check(object_ == expected_value,
                          "Object {} must be == '{}'".format(repr(object_), repr(expected_value)),
                          **kwargs)

    def check_attribute_equal(self, object_: object, attribute_name: str, expected_value: object, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is the same as expected_value and adds / stores the
        check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param expected_value: The expected value of the attribute
        :return: The value of expression to be used in control statements
        """
        kwargs['value'] = getattr(object_, attribute_name)
        return self.check(getattr(object_, attribute_name) == expected_value,
                          "Attribute '{}' of {} must be == '{}'".format(attribute_name, repr(object_), expected_value),
                          **kwargs)

    def check_attribute_equal_deep(self, object_: object, attribute_name: str, expected_value: object,
                                   attribute: object, attribute_path: str, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is the same as expected_value and adds / stores the
        check result for later analysis.

        For use: check_attribute_equal_deep(submodel, id, "http://...",
                                            submodel.identification.id, "identification.id")

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param expected_value: The expected value of the attribute
        :param attribute: The attribute object
        :param attribute_path: The path inside the object to the attribute
        :return: The value of expression to be used in control statements
        """
        kwargs['value'] = getattr(attribute, attribute_name)
        return self.check(getattr(attribute, attribute_name) == expected_value,
                          "Attribute '{}' of {} must be == {}".format(attribute_path, repr(object_), expected_value),
                          **kwargs)

    def check_element_in(self, object_: model.Referable, parent: object, **kwargs) -> bool:
        """
        Checks if object_ exist in parent and adds / stores the check result for later analysis.

        :param object_: The object which shall be in parent
        :param parent: The parent in which object_ shall be exist
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        Existence check: <path to object> must exist in <object class> (<path to object>)
        """
        return self.check(object_.parent == parent,
                          "{} must exist in {}s".format(repr(object_), repr(parent)),
                          **kwargs)

    def check_contained_element_length(self, object_: object, attribute_name: str, class_name: Type,
                                       length: int, **kwargs) -> bool:
        """
        Checks if the object_ has <lenght> elements of class <class_name> in attribute <attribute_name> and
        adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param class_name: The class name to decide which objects in the attribute shall be count
        :param length: The expected length of the attribute
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        count = 0
        for element in getattr(object_, attribute_name):
            if isinstance(element, class_name):
                count = count + 1
        kwargs['count'] = count
        return self.check(count == length,
                          "{} must contain {} {}s".format(repr(object_), length, class_name.__name__),
                          **kwargs)

    def check_is_instance(self, object_: object, class_name: Type, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is None and adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param class_name: The class name which the object_ shall be
        :return: The value of expression to be used in control statements
        """
        kwargs['class'] = object_.__class__.__name__
        return self.check(isinstance(object_, class_name),
                          "Object {} must be of class {}".format(repr(object_), class_name.__name__),
                          **kwargs)

    def check_attribute_is_none(self, object_: object, attribute_name: str, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is None and adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :return: The value of expression to be used in control statements
        """
        kwargs['value'] = getattr(object_, attribute_name)
        return self.check(getattr(object_, attribute_name) is None,
                          "Attribute '{}' of {} must be 'None'".format(attribute_name, repr(object_)),
                          **kwargs)

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
