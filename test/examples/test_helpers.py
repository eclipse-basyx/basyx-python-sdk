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
import unittest

from aas.examples.data import example_aas, example_aas_mandatory_attributes, example_aas_missing_attributes, \
    example_concept_description, example_submodel_template
from aas.examples.data._helper import DataChecker, AASDataChecker
from aas import model


class DataCheckerTest(unittest.TestCase):
    def test_check(self):
        checker = DataChecker(raise_immediately=True)
        with self.assertRaises(AssertionError):
            checker.check(2 == 3, 'Assertion test')

    def test_raise_failed(self):
        checker = DataChecker(raise_immediately=False)
        checker.check(2 == 2, 'Assertion test')
        checker.raise_failed()  # no assertion should be occur
        self.assertEqual(1, sum(1 for _ in checker.successful_checks))
        checker.check(2 == 3, 'Assertion test')
        with self.assertRaises(AssertionError):
            checker.raise_failed()


class AASDataCheckerTest(unittest.TestCase):
    def test_ordered_collection_checker(self):
        property = model.Property(
            id_short='Prop1',
            value_type=model.datatypes.String,
            value='test'
        )
        range = model.Range(
            id_short='Range1',
            value_type=model.datatypes.Int,
            min_=100,
            max_=200
        )
        collection = model.SubmodelElementCollectionOrdered(
            id_short='Collection',
            value=(property, range)
        )

        property_expected = model.Property(
            id_short='Prop1',
            value_type=model.datatypes.String,
            value='test'
        )
        range_expected = model.Range(
            id_short='Range1',
            value_type=model.datatypes.Int,
            min_=100,
            max_=200
        )
        collection_expected = model.SubmodelElementCollectionOrdered(
            id_short='Collection',
            value=(range_expected, property_expected)
        )

        checker = AASDataChecker(raise_immediately=False)
        checker.check_submodel_collection_equal(collection, collection_expected)
        self.assertEqual(2, sum(1 for _ in checker.failed_checks))
        checker_iterator = iter(checker.failed_checks)
        self.assertEqual("FAIL: Property[Collection / Prop1] must be of class Range (class='Property')",
                         repr(next(checker_iterator)))
        self.assertEqual("FAIL: Range[Collection / Range1] must be of class Property (class='Range')",
                         repr(next(checker_iterator)))

    def test_qualifiable_checker(self):
        qualifier_expected = model.Qualifier(
            type_='test',
            value_type=model.datatypes.String,
            value='test value'
        )
        property_expected = model.Property(
            id_short='Prop1',
            value_type=model.datatypes.String,
            value='test',
            qualifier={qualifier_expected}
        )

        property = model.Property(
            id_short='Prop1',
            value_type=model.datatypes.String,
            value='test'
        )

        checker = AASDataChecker(raise_immediately=False)
        checker.check_property_equal(property, property_expected)
        self.assertEqual(2, sum(1 for _ in checker.failed_checks))
        self.assertEqual(9, sum(1 for _ in checker.successful_checks))
        checker_iterator = iter(checker.failed_checks)
        self.assertEqual("FAIL: Property[Prop1] must contain 1 Constraints (count=0)",
                         repr(next(checker_iterator)))
        self.assertEqual("FAIL: ConstraintQualifier(type=test) must exist ()", repr(next(checker_iterator)))
