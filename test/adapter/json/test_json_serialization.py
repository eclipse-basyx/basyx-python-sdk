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
import json

from aas import model
from aas.adapter.json import AASToJsonEncoder, StrippedAASToJsonEncoder, write_aas_json_file, JSON_SCHEMA_FILE
from jsonschema import validate  # type: ignore
from typing import Set, Union

from aas.examples.data import example_aas_missing_attributes, example_submodel_template, \
    example_aas_mandatory_attributes, example_aas, create_example, example_concept_description


class JsonSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property("test_id_short", model.datatypes.String, category="PARAMETER",
                                     description={"en-us": "Germany", "de": "Deutschland"})
        json_data = json.dumps(test_object, cls=AASToJsonEncoder)

    def test_random_object_serialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(model.AssetInformation(global_asset_id=asset_reference),
                                                  aas_identifier, submodel={submodel_reference})

        # serialize object to json
        json_data = json.dumps({
                'assetAdministrationShells': [test_aas],
                'submodels': [submodel],
                'assets': [],
                'conceptDescriptions': [],
            }, cls=AASToJsonEncoder)
        json_data_new = json.loads(json_data)


class JsonSerializationSchemaTest(unittest.TestCase):
    def test_random_object_serialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        # The JSONSchema expects every object with HasSemnatics (like Submodels) to have a `semanticId` Reference, which
        # must be a Reference. (This seems to be a bug in the JSONSchema.)
        submodel = model.Submodel(submodel_identifier, semantic_id=model.Reference((),))
        test_aas = model.AssetAdministrationShell(model.AssetInformation(global_asset_id=asset_reference),
                                                  aas_identifier, submodel={submodel_reference})

        # serialize object to json
        json_data = json.dumps({
                'assetAdministrationShells': [test_aas],
                'submodels': [submodel],
                'assets': [],
                'conceptDescriptions': [],
            }, cls=AASToJsonEncoder)
        json_data_new = json.loads(json_data)

        # load schema
        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_schema = json.load(json_file)

        # validate serialization against schema
        validate(instance=json_data_new, schema=aas_schema)

    def test_aas_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_concept_description_serialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_concept_description.create_iec61360_concept_description())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_example_serialization(self) -> None:
        data = create_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, 'r') as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)


class JsonSerializationStrippedObjectsTest(unittest.TestCase):
    def _checkNormalAndStripped(self, attributes: Union[Set[str], str], obj: object) -> None:
        if isinstance(attributes, str):
            attributes = {attributes}

        # attributes should be present when using the normal encoder,
        # but must not be present when using the stripped encoder
        for cls, assert_fn in ((AASToJsonEncoder, self.assertIn), (StrippedAASToJsonEncoder, self.assertNotIn)):
            data = json.loads(json.dumps(obj, cls=cls))
            for attr in attributes:
                assert_fn(attr, data)

    def test_stripped_qualifiable(self) -> None:
        qualifier = model.Qualifier("test_qualifier", str)
        operation = model.Operation("test_operation", qualifier={qualifier})
        submodel = model.Submodel(
            model.Identifier("http://acplt.org/test_submodel", model.IdentifierType.IRI),
            submodel_element=[operation],
            qualifier={qualifier}
        )

        self._checkNormalAndStripped({"submodelElements", "qualifiers"}, submodel)
        self._checkNormalAndStripped("qualifiers", operation)

    def test_stripped_annotated_relationship_element(self) -> None:
        mlp = model.MultiLanguageProperty("test_multi_language_property", category="PARAMETER")
        ref = model.AASReference(
            (model.Key(model.KeyElements.SUBMODEL, "http://acplt.org/test_ref", model.KeyType.IRI),),
            model.Submodel
        )
        are = model.AnnotatedRelationshipElement(
            "test_annotated_relationship_element",
            ref,
            ref,
            annotation=[mlp]
        )

        self._checkNormalAndStripped("annotation", are)

    def test_stripped_entity(self) -> None:
        mlp = model.MultiLanguageProperty("test_multi_language_property", category="PARAMETER")
        entity = model.Entity("test_entity", model.EntityType.CO_MANAGED_ENTITY, statement=[mlp])

        self._checkNormalAndStripped("statements", entity)

    def test_stripped_submodel_element_collection(self) -> None:
        mlp = model.MultiLanguageProperty("test_multi_language_property", category="PARAMETER")
        sec = model.SubmodelElementCollectionOrdered("test_submodel_element_collection", value=[mlp])

        self._checkNormalAndStripped("value", sec)

    def test_stripped_asset_administration_shell(self) -> None:
        asset_ref = model.AASReference(
            (model.Key(model.KeyElements.ASSET, "http://acplt.org/test_ref", model.KeyType.IRI),),
            model.Asset
        )
        submodel_ref = model.AASReference(
            (model.Key(model.KeyElements.SUBMODEL, "http://acplt.org/test_ref", model.KeyType.IRI),),
            model.Submodel
        )
        aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id=asset_ref),
            model.Identifier("http://acplt.org/test_aas", model.IdentifierType.IRI),
            submodel={submodel_ref},
            view=[model.View("test_view")]
        )

        self._checkNormalAndStripped({"submodels", "views"}, aas)
