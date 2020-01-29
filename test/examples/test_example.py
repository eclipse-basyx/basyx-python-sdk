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
Tests for the example aas

Functions to test if an object is the same to the example aas from example_aas.py
"""
import unittest
from aas.examples.data.example_aas import *
from aas.examples.data._helper import AASDataChecker


class ExampleAASTest(unittest.TestCase):
    def test_example_asset_identification_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = create_example_asset_identification_submodel()
        check_example_asset_identification_submodel(checker, submodel)

    def test_example_bill_of_material_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = create_example_bill_of_material_submodel()
        check_example_bill_of_material_submodel(checker, submodel)

    def test_example_asset(self):
        checker = AASDataChecker(raise_immediately=True)
        asset = create_example_asset()
        check_example_asset(checker, asset)

    def test_example_concept_description(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_description = create_example_concept_description()
        check_example_concept_description(checker, concept_description)

    def test_example_asset_administration_shell(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_dictionary = create_example_concept_dictionary()
        shell = create_example_asset_administration_shell(concept_dictionary)
        check_example_asset_administration_shell(checker, shell)

    def test_example_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = create_example_submodel()
        check_example_submodel(checker, submodel)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store = create_full_example()
        check_full_example(checker, obj_store)
