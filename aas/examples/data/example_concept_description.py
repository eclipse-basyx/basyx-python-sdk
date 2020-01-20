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
from aas.model.concept import *


def create_iec61360_concept_description() -> IEC61360ConceptDescription:
    """
    Creates a ConceptDescription after the IEC61360 standard

    :return: Example concept description
    """
    identification = model.Identifier(id_='http://acplt.org/DataSpecifciations/Example/Identification',
                                      id_type=model.IdentifierType.IRI)
    return IEC61360ConceptDescription(administration=model.AdministrativeInformation(version='0.9',
                                                                                     revision='0'),
                                      identification=identification,
                                      id_short="TestSpec_01",
                                      preferred_name="TestSpecification",
                                      short_name="TestSpec",
                                      data_type=IEC61360DataType.REAL_MEASURE,
                                      definition="This is a DataSpecification for testing purposes",
                                      code="123/45_ABC///idk",
                                      unit="SpaceUnit",
                                      source_of_definition="http://acplt.org/DataSpec/ExampleDef",
                                      symbol="SU",
                                      value_format="string",
                                      value="TEST")
