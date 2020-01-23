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
Tests for the example submodel template

Functions to test if an object is the same to the example submodel template from example_submodel_template.py
"""

from aas import model
from aas.examples.data._helper import AASDataChecker
from aas.examples.data import example_submodel_template


def assert_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = example_submodel_template.create_example_submodel_template()
    checker.check_submodel_equal(submodel, expected_submodel)


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
        if submodel.identification.id == 'https://acplt.org/Test_Submodel_Template':
            assert_example_submodel(checker, submodel)
        else:
            if failsafe:
                raise KeyError()

    for cd in concept_descriptions:
        if failsafe:
            raise KeyError()
