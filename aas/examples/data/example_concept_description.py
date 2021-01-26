# Copyright 2020 PyI40AAS Contributors
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
Module for creation of an example :class:`~aas.model.concept.ConceptDescription`
"""
import logging

from ... import model
from ._helper import AASDataChecker
from ...model.concept import *

logger = logging.getLogger(__name__)


def create_iec61360_concept_description() -> IEC61360ConceptDescription:
    """
    Creates a :class:`~aas.model.concept.ConceptDescription` after the IEC61360 standard

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
                                               value='http://acplt.org/ReferenceElements/ConceptDescriptionX',
                                               id_type=model.KeyType.IRI),))},
        id_short="TestSpec_01",
        category=None,
        description=None,
        parent=None,
        administration=model.AdministrativeInformation(version='0.9', revision='0'),
        unit="SpaceUnit",
        unit_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                           value='http://acplt.org/Units/SpaceUnit',
                                           id_type=model.KeyType.IRI),)),
        source_of_definition="http://acplt.org/DataSpec/ExampleDef",
        symbol="SU",
        value_format=model.datatypes.String,
        value_list={
            model.ValueReferencePair(
                value_type=model.datatypes.String,
                value='exampleValue',
                value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                    value='http://acplt.org/ValueId/ExampleValueId',
                                                    id_type=model.KeyType.IRI),)),),
            model.ValueReferencePair(
                value_type=model.datatypes.String,
                value='exampleValue2',
                value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
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


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    expected_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    expected_data.add(create_iec61360_concept_description())
    checker.check_object_store(obj_store, expected_data)
