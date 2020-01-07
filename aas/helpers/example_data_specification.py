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
Module for creation of an example data specification.

Use create_data_specification_IEC61360
"""

from aas.util import data_specification_templates as dst
from aas import model


def create_data_specification_iec61360():
    """
    Creates a (nonsensical) DataSpecification after the IEC61360 standard
    :return: Example DataSpecification
    """
    identification = model.Identifier(id_='http://acplt.org/DataSpecifciations/Example/Identification',
                                      id_type=model.IdentifierType.IRI)
    data_specification = dst.DataSpecificationIEC61360(administration=model.AdministrativeInformation(version='0.9',
                                                                                                      revision='0'),
                                                       identification=identification,
                                                       id_short="TestSpec_01",
                                                       preferred_name="TestSpecification",
                                                       short_name="TestSpec",
                                                       data_type=dst.DataTypeIEC61360.REAL_MEASURE,
                                                       definition="This is a DataSpecification for testing purposes",
                                                       code="123/45_ABC///idk",
                                                       unit="SpaceUnit",
                                                       source_of_definition="http://acplt.org/DataSpec/ExampleDef",
                                                       symbol="SU",
                                                       value_format="string",
                                                       value="TEST")
    return data_specification
