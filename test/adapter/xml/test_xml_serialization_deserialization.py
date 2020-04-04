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

import io
import unittest

from aas import model
from aas.adapter.xml import xml_serialization, xml_deserialization

from aas.examples.data import example_aas_missing_attributes, example_submodel_template, \
    example_aas_mandatory_attributes, example_aas, example_concept_description
from aas.examples.data._helper import AASDataChecker


def _serialize_and_deserialize(data: model.DictObjectStore) -> model.DictObjectStore:
    file = io.BytesIO()
    xml_serialization.write_aas_xml_file(file=file, data=data)

    # try deserializing the xml document into a DictObjectStore of AAS objects with help of the xml_deserialization
    # module
    file.seek(0)
    return xml_deserialization.read_xml_aas_file(file, failsafe=False)


class XMLSerializationDeserializationTest(unittest.TestCase):
    def test_example_serialization_deserialization(self) -> None:
        object_store = _serialize_and_deserialize(example_aas.create_full_example())
        checker = AASDataChecker(raise_immediately=True)
        example_aas.check_full_example(checker, object_store)

    def test_example_mandatory_attributes_serialization_deserialization(self) -> None:
        object_store = _serialize_and_deserialize(example_aas_mandatory_attributes.create_full_example())
        checker = AASDataChecker(raise_immediately=True)
        example_aas_mandatory_attributes.check_full_example(checker, object_store)

    def test_example_missing_attributes_serialization_deserialization(self) -> None:
        object_store = _serialize_and_deserialize(example_aas_missing_attributes.create_full_example())
        checker = AASDataChecker(raise_immediately=True)
        example_aas_missing_attributes.check_full_example(checker, object_store)

    def test_example_submodel_template_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        object_store = _serialize_and_deserialize(data)
        checker = AASDataChecker(raise_immediately=True)
        example_submodel_template.check_full_example(checker, object_store)

    def test_example_iec61360_concept_description_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_concept_description.create_iec61360_concept_description())
        object_store = _serialize_and_deserialize(data)
        checker = AASDataChecker(raise_immediately=True)
        example_concept_description.check_full_example(checker, object_store)
