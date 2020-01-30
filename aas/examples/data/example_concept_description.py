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
Module for creation of an example concept description
"""

from aas import model
from aas.examples.data._helper import AASDataChecker
from aas.model.concept import *


def create_iec61360_concept_description() -> IEC61360ConceptDescription:
    """
    Creates a ConceptDescription after the IEC61360 standard

    :return: Example concept description
    """
    identification = model.Identifier(id_='http://acplt.org/DataSpecifciations/Example/Identification',
                                      id_type=model.IdentifierType.IRI)
    return IEC61360ConceptDescription(
        identification=identification,
        preferred_name={'de': 'Test Specification', 'en-us': "TestSpecification"},
        data_type=IEC61360DataType.REAL_MEASURE,
        definition={'de': 'Dies ist eine Data Specification für Testzwecke',
                    'en-us': "This is a DataSpecification for testing purposes"},
        short_name={'de': 'Test Spec', 'en-us': "TestSpec"},
        is_case_of={model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/ReferenceElements/ConceptDescriptionX',
                                               id_type=model.KeyType.IRI),))},
        id_short="TestSpec_01",
        category=None,
        description=None,
        parent=None,
        administration=model.AdministrativeInformation(version='0.9', revision='0'),
        unit="SpaceUnit",
        unit_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                           local=False,
                                           value='http://acplt.org/Units/SpaceUnit',
                                           id_type=model.KeyType.IRI),)),
        source_of_definition="http://acplt.org/DataSpec/ExampleDef",
        symbol="SU",
        value_format="string",
        value_list={
            model.ValueReferencePair(
                value_type='string',
                value='exampleValue',
                value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                    local=False,
                                                    value='http://acplt.org/ValueId/ExampleValueId',
                                                    id_type=model.KeyType.IRI),)),),
            model.ValueReferencePair(
                value_type='string',
                value='exampleValue2',
                value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                    local=False,
                                                    value='http://acplt.org/ValueId/ExampleValueId2',
                                                    id_type=model.KeyType.IRI),)),)},
        value="TEST",
        value_id=None,
        level_types={IEC61360LevelType.MIN, IEC61360LevelType.MAX})


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_iec61360_concept_description(checker: AASDataChecker,
                                               concept_description: model.concept.IEC61360ConceptDescription) -> None:
    expected_concept_description = create_iec61360_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore, failsafe: bool = True) -> None:
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
            check_example_iec61360_concept_description(checker, cd)  # type: ignore
        else:
            if failsafe:
                raise KeyError()
