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
Tests for the example concept description

Functions to test if an object is the same to the example concept description from example_concept_description.py
"""

from aas import model
from aas.model.concept import IEC61360DataType, IEC61360LevelType
from aas.util import identification
from aas.examples.data._helper import AASDataChecker
from aas.examples.data import example_concept_description


def assert_example_iec61360_concept_description(checker: AASDataChecker,
                                                concept_description: model.concept.IEC61360ConceptDescription) -> None:
    expected_concept_description = example_concept_description.create_iec61360_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def assert_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore, failsafe: bool = True) -> None:
    # separate different kind of objects
    assets = []
    submodels = []
    concept_descriptions = []
    shells = []
    for obj in obj_store:
        if isinstance(obj, model.Asset):
            assets.append(obj)
        elif isinstance(obj, model.AssetAdministrationShell):
            shells.append(obj)
        elif isinstance(obj, model.Submodel):
            submodels.append(obj)
        elif isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)
        else:
            if failsafe:
                raise KeyError()

    for asset in assets:
        if failsafe:
            raise KeyError()

    for shell in shells:
        if failsafe:
            raise KeyError()

    for submodel in submodels:
        if failsafe:
            raise KeyError()

    for cd in concept_descriptions:
        if cd.identification.id == 'http://acplt.org/DataSpecifciations/Example/Identification':
            assert_example_iec61360_concept_description(checker, cd)  # type: ignore
        else:
            if failsafe:
                raise KeyError()
