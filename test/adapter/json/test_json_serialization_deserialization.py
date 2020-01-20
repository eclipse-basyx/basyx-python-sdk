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

import io
import json
import os

from aas import model
from aas.adapter.json import json_serialization, json_deserialization

from aas.helpers import example_aas, example_submodel_template, \
    example_aas_mandatory_attributes, example_aas_missing_attributes
from test._helper.testCase_for_example_aas import ExampleHelper
from test._helper.testCase_for_example_aas_mandatory_attributes import ExampleHelper as ExampleHelperMandatory
from test._helper.testCase_for_example_aas_missing_attributes import ExampleHelper as ExampleHelperMissing

JSON_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'aasJSONSchemaV2.0.json')


class JsonSerializationDeserializationTest(ExampleHelper):
    def test_random_object_serialization_deserialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, True, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel_={submodel_reference})

        # serialize object to json
        json_data = json.dumps({
                'assetAdministrationShells': [test_aas],
                'submodels': [submodel],
                'assets': [],
                'conceptDescriptions': [],
            }, cls=json_serialization.AASToJsonEncoder)
        json_data_new = json.loads(json_data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        json_object_store = json_deserialization.read_json_aas_file(io.StringIO(json_data), failsafe=False)

    def test_full_example_serialization_deserialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)
        self.assert_full_example(json_object_store)

    def test_submodel_template_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)

    def test_full_empty_example_serialization_deserialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)

    def test_missing_serialization_deserialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)


class JsonSerializationDeserializationTest2(ExampleHelperMandatory):
    def test_example_mandatory_attributes_serialization_deserialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)
        self.assert_full_example(json_object_store)


class JsonSerializationDeserializationTest3(ExampleHelperMissing):
    def test_example_missing_attributes_serialization_deserialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        json_serialization.write_aas_json_file(file=file, data=data)
        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json_deserialization
        # module
        file.seek(0)
        json_object_store = json_deserialization.read_json_aas_file(file, failsafe=False)
        self.assert_full_example(json_object_store)
