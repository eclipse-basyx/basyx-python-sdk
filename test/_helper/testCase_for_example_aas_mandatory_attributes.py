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
Tests for the example aas mandatory attributes

Functions to test if an object is the same to the example aas mandatory attributes from
example_aas_mandatory_attributes.py
"""
from typing import Optional

from aas import model
from aas.util import identification
from aas.examples.data._helper import AASDataChecker
from aas.examples.data import example_aas_mandatory_attributes


def assert_example_asset(checker: AASDataChecker, asset: model.Asset) -> None:
    expected_asset = example_aas_mandatory_attributes.create_example_asset()
    checker.check_asset_equal(asset, expected_asset)


def assert_example_concept_description(checker: AASDataChecker, concept_description: model.ConceptDescription) -> None:
    expected_concept_description = example_aas_mandatory_attributes.create_example_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def assert_example_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) -> None:
    example_cd = example_aas_mandatory_attributes.create_example_concept_dictionary()
    expected_shell = example_aas_mandatory_attributes.create_example_asset_administration_shell(example_cd)
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def assert_example_empty_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) \
        -> None:
    expected_shell = example_aas_mandatory_attributes.create_example_empty_asset_administration_shell()
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def assert_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = example_aas_mandatory_attributes.create_example_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def assert_example_empty_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = example_aas_mandatory_attributes.create_example_empty_submodel()
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
        if asset.identification.id == 'https://acplt.org/Test_Asset_Mandatory':
            assert_example_asset(checker, asset)
        else:
            if failsafe:
                raise KeyError()

    for shell in shells:
        if shell.identification.id == 'https://acplt.org/Test_AssetAdministrationShell_Mandatory':
            assert_example_asset_administration_shell(checker, shell)
        elif shell.identification.id == 'https://acplt.org/Test_AssetAdministrationShell2_Mandatory':
            assert_example_empty_asset_administration_shell(checker, shell)
        else:
            if failsafe:
                raise KeyError()

    for submodel in submodels:
        if submodel.identification.id == 'https://acplt.org/Test_Submodel_Mandatory':
            assert_example_submodel(checker, submodel)
        elif submodel.identification.id == 'https://acplt.org/Test_Submodel2_Mandatory':
            assert_example_empty_submodel(checker, submodel)
        else:
            if failsafe:
                raise KeyError()

    for cd in concept_descriptions:
        if cd.identification.id == 'https://acplt.org/Test_ConceptDescription_Mandatory':
            assert_example_concept_description(checker, cd)
        else:
            if failsafe:
                raise KeyError()