# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import io
import json
import os
import unittest
from typing import Set, Union

from basyx.aas import model
from basyx.aas.adapter.json import (
    AASToJsonEncoder,
    StrippedAASToJsonEncoder,
    object_store_to_json,
    read_aas_json_file,
    write_aas_json_file,
)
from basyx.aas.examples.data import (
    create_example,
    example_aas,
    example_aas_mandatory_attributes,
    example_aas_missing_attributes,
    example_submodel_template,
)
from jsonschema import validate  # type: ignore

from test._helper.test_helpers import REQUIRE_SCHEMAS

JSON_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "../schemas/aasJSONSchema.json"
)


class JsonSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property(
            "test_id_short",
            model.datatypes.String,
            category="PARAMETER",
            description=model.MultiLanguageTextType(
                {"en-US": "Germany", "de": "Deutschland"}
            ),
        )
        json.dumps(test_object, cls=AASToJsonEncoder)

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="test"),
            aas_identifier,
            submodel={submodel_reference},
        )

        # serialize object to json
        json_data = json.dumps(
            {
                "assetAdministrationShells": [test_aas],
                "submodels": [submodel],
                "assets": [],
                "conceptDescriptions": [],
            },
            cls=AASToJsonEncoder,
        )
        json.loads(json_data)


    def test_entity_omits_empty_specific_asset_ids(self) -> None:
        # An Entity without specific asset ids must leave specificAssetIds out
        # entirely: the schema gives it minItems 1, so an empty array is invalid.
        # AASd-014 forbids them on a co-managed entity, so this is every such entity.
        entity = model.Entity("test_entity", model.EntityType.CO_MANAGED_ENTITY)
        data = json.loads(json.dumps(entity, cls=AASToJsonEncoder))
        self.assertNotIn("specificAssetIds", data)

    def test_entity_serializes_specific_asset_ids(self) -> None:
        # AASd-014: only a self-managed entity may carry specific asset ids
        entity = model.Entity(
            "test_entity",
            model.EntityType.SELF_MANAGED_ENTITY,
            specific_asset_id=[model.SpecificAssetId("test_name", "test_value")],
        )
        data = json.loads(json.dumps(entity, cls=AASToJsonEncoder))
        self.assertEqual(1, len(data["specificAssetIds"]))
        self.assertEqual("test_name", data["specificAssetIds"][0]["name"])


class JsonSerializationSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(JSON_SCHEMA_FILE):
            if REQUIRE_SCHEMAS:
                raise RuntimeError(
                    f"REQUIRE_SCHEMA_TESTS is set, but the JSON Schema does not exist at {JSON_SCHEMA_FILE}"
                )
            raise unittest.SkipTest(
                f"JSON Schema does not exist at {JSON_SCHEMA_FILE}, skipping test"
            )

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        # The JSONSchema expects every object with HasSemnatics (like Submodels) to have a `semanticId` Reference, which
        # must be a Reference. (This seems to be a bug in the JSONSchema.)
        submodel = model.Submodel(
            submodel_identifier,
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        model.KeyTypes.GLOBAL_REFERENCE,
                        "http://example.org/TestSemanticId",
                    ),
                )
            ),
        )
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="test"),
            aas_identifier,
            submodel={submodel_reference},
        )

        # serialize object to json
        json_data = json.dumps(
            {"assetAdministrationShells": [test_aas], "submodels": [submodel]},
            cls=AASToJsonEncoder,
        )
        json_data_new = json.loads(json_data)

        # load schema
        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_schema = json.load(json_file)

        # validate serialization against schema
        validate(instance=json_data_new, schema=aas_schema)

    def test_aas_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_concept_description_serialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_aas.create_example_concept_description())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_example_serialization(self) -> None:
        data = create_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)


class JsonSerializationStrippedObjectsTest(unittest.TestCase):
    def _checkNormalAndStripped(
        self, attributes: Union[Set[str], str], obj: object
    ) -> None:
        if isinstance(attributes, str):
            attributes = {attributes}

        # attributes should be present when using the normal encoder,
        # but must not be present when using the stripped encoder
        for cls, assert_fn in (
            (AASToJsonEncoder, self.assertIn),
            (StrippedAASToJsonEncoder, self.assertNotIn),
        ):
            data = json.loads(json.dumps(obj, cls=cls))
            for attr in attributes:
                assert_fn(attr, data)

    def test_stripped_qualifiable(self) -> None:
        qualifier = model.Qualifier("test_qualifier", str)
        qualifier2 = model.Qualifier("test_qualifier2", str)
        operation = model.Operation("test_operation", qualifier={qualifier})
        submodel = model.Submodel(
            "http://example.org/test_submodel",
            submodel_element=[operation],
            qualifier={qualifier2},
        )

        self._checkNormalAndStripped({"submodelElements", "qualifiers"}, submodel)
        self._checkNormalAndStripped("qualifiers", operation)

    def test_stripped_annotated_relationship_element(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "http://example.org/test_ref"),),
            model.Submodel,
        )
        are = model.AnnotatedRelationshipElement(
            "test_annotated_relationship_element", ref, ref, annotation=[mlp]
        )

        self._checkNormalAndStripped("annotations", are)

    def test_relationship_element_omits_none_first_second(self) -> None:
        re = model.RelationshipElement("test_re")
        data = json.loads(json.dumps(re, cls=AASToJsonEncoder))
        self.assertNotIn("first", data)
        self.assertNotIn("second", data)

    def test_stripped_entity(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        entity = model.Entity(
            "test_entity", model.EntityType.CO_MANAGED_ENTITY, statement=[mlp]
        )

        self._checkNormalAndStripped("statements", entity)

    def test_stripped_submodel_element_collection(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        sec = model.SubmodelElementCollection(
            "test_submodel_element_collection", value=[mlp]
        )

        self._checkNormalAndStripped("value", sec)

    def test_stripped_asset_administration_shell(self) -> None:
        submodel_ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "http://example.org/test_ref"),),
            model.Submodel,
        )
        aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/test_ref"),
            "http://example.org/test_aas",
            submodel={submodel_ref},
        )

        self._checkNormalAndStripped({"submodels"}, aas)


class WithoutBlobValueAASToJsonEncoder(AASToJsonEncoder):
    with_blob_value = False


class TestAASToJsonEncoderBlobValue(unittest.TestCase):
    def setUp(self):
        self.submodel = example_aas.create_example_submodel()
        self.blob = self.submodel.get_referable("ExampleSubmodelCollection.ExampleBlob")

    def test_with_blob_value_is_default_ok(self):
        out_str = json.dumps(self.blob, cls=AASToJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertTrue(AASToJsonEncoder.with_blob_value)
        # the value is base64 encoded b"\x01\x02\x03\x04\x05"
        self.assertEqual("AQIDBAU=", parsed_output["value"])

    def test_without_blob_value_omits_value_ok(self):
        expected = json.loads(json.dumps(self.blob, cls=AASToJsonEncoder))
        expected.pop("value")

        out_str = json.dumps(self.blob, cls=WithoutBlobValueAASToJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(expected, parsed_output)

    def test_with_blob_value_empty_value_ok(self):
        blob = model.Blob("EmptyBlob", "application/octet-stream", value=b"")

        out_str = json.dumps(blob, cls=AASToJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual("", parsed_output["value"])

    def test_with_blob_value_without_value_ok(self):
        blob = model.Blob("BlobWithoutValue", "application/octet-stream")

        out_str = json.dumps(blob, cls=AASToJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertNotIn("value", parsed_output)


def _external_reference(*values: str) -> model.ExternalReference:
    return model.ExternalReference(
        tuple(model.Key(model.KeyTypes.GLOBAL_REFERENCE, value) for value in values)
    )


def _submodel_reference(identifier: str) -> model.ModelReference:
    return model.ModelReference(
        (model.Key(model.KeyTypes.SUBMODEL, identifier),), model.Submodel
    )


class TestAASToJsonEncoderOrder(unittest.TestCase):
    """
    Collections that are unordered according to the specification must be serialized in a canonical order, so that
    equal objects always produce identical JSON strings, independent of insertion order and hash randomization.
    The elements are always inserted in reverse order of the expected output.
    """

    def test_referables_start_with_modelType_ok(self) -> None:
        referables = [
            model.AssetAdministrationShell(
                model.AssetInformation(global_asset_id="urn:asset"), "urn:aas"
            ),
            model.Submodel("urn:sm"),
            model.ConceptDescription("urn:cd"),
            model.Property("prop", model.datatypes.String),
            model.MultiLanguageProperty("mlp"),
            model.Range("range", model.datatypes.Int),
            model.Blob("blob", "application/octet-stream"),
            model.File("file", "text/plain"),
            model.ReferenceElement("ref"),
            model.SubmodelElementCollection("smc"),
            model.SubmodelElementList("sml", model.Capability),
            model.RelationshipElement("rel"),
            model.AnnotatedRelationshipElement("arel"),
            model.Operation("op"),
            model.Capability("cap"),
            model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY),
            model.BasicEventElement(
                "event",
                _submodel_reference("urn:sm"),
                model.Direction.OUTPUT,
                model.StateOfEvent.ON,
            ),
        ]

        data = [json.loads(json.dumps(r, cls=AASToJsonEncoder)) for r in referables]

        self.assertEqual(
            [(type(r).__name__, "modelType") for r in referables],
            [(type(r).__name__, next(iter(d))) for r, d in zip(referables, data)],
        )

    def test_extensions_sorted_by_name_ok(self) -> None:
        submodel = model.Submodel(
            "urn:sm",
            extension=[model.Extension(name) for name in ["e2", "e1", "e0"]],
        )

        data = json.loads(json.dumps(submodel, cls=AASToJsonEncoder))

        self.assertEqual(["e0", "e1", "e2"], [e["name"] for e in data["extensions"]])

    def test_embedded_data_specifications_sorted_by_data_specification_ok(self) -> None:
        content = model.DataSpecificationIEC61360(
            model.PreferredNameTypeIEC61360({"en": "name"})
        )
        submodel = model.Submodel(
            "urn:sm",
            embedded_data_specifications=[
                model.EmbeddedDataSpecification(_external_reference(value), content)
                for value in ["urn:ds2", "urn:ds1", "urn:ds0"]
            ],
        )

        data = json.loads(json.dumps(submodel, cls=AASToJsonEncoder))

        self.assertEqual(
            ["urn:ds0", "urn:ds1", "urn:ds2"],
            [
                spec["dataSpecification"]["keys"][0]["value"]
                for spec in data["embeddedDataSpecifications"]
            ],
        )


    def test_lang_string_sets_sorted_by_language_ok(self) -> None:
        prop = model.Property(
            "prop",
            model.datatypes.String,
            display_name=model.MultiLanguageNameType({"fr": "n", "en": "n", "de": "n"}),
            description=model.MultiLanguageTextType({"fr": "t", "en": "t", "de": "t"}),
        )

        data = json.loads(json.dumps(prop, cls=AASToJsonEncoder))

        self.assertEqual(
            ["de", "en", "fr"], [s["language"] for s in data["displayName"]]
        )
        self.assertEqual(
            ["de", "en", "fr"], [s["language"] for s in data["description"]]
        )

    def test_qualifiers_sorted_by_type_ok(self) -> None:
        submodel = model.Submodel(
            "urn:sm",
            qualifier=[
                model.Qualifier(type_, model.datatypes.String)
                for type_ in ["q2", "q1", "q0"]
            ],
        )

        data = json.loads(json.dumps(submodel, cls=AASToJsonEncoder))

        self.assertEqual(["q0", "q1", "q2"], [q["type"] for q in data["qualifiers"]])

    def test_entity_specific_asset_ids_sorted_ok(self) -> None:
        entity = model.Entity(
            "entity",
            model.EntityType.SELF_MANAGED_ENTITY,
            specific_asset_id=[
                model.SpecificAssetId(name, "v") for name in ["n2", "n1", "n0"]
            ],
        )

        data = json.loads(json.dumps(entity, cls=AASToJsonEncoder))

        self.assertEqual(
            ["n0", "n1", "n2"], [s["name"] for s in data["specificAssetIds"]]
        )

    def test_asset_administration_shell_submodels_sorted_ok(self) -> None:
        aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="urn:asset"),
            "urn:aas",
            submodel={_submodel_reference(i) for i in ["urn:sm2", "urn:sm1", "urn:sm0"]},
        )

        data = json.loads(json.dumps(aas, cls=AASToJsonEncoder))

        self.assertEqual(
            ["urn:sm0", "urn:sm1", "urn:sm2"],
            [ref["keys"][0]["value"] for ref in data["submodels"]],
        )

    def test_submodel_elements_sorted_by_id_short_ok(self) -> None:
        submodel = model.Submodel(
            "urn:sm",
            submodel_element=[
                model.Property(id_short, model.datatypes.String)
                for id_short in ["p2", "p1", "p0"]
            ],
        )

        data = json.loads(json.dumps(submodel, cls=AASToJsonEncoder))

        self.assertEqual(
            ["p0", "p1", "p2"], [e["idShort"] for e in data["submodelElements"]]
        )

    def test_submodel_element_collection_sorted_by_id_short_ok(self) -> None:
        collection = model.SubmodelElementCollection(
            "smc",
            value=[
                model.Property(id_short, model.datatypes.String)
                for id_short in ["p2", "p1", "p0"]
            ],
        )

        data = json.loads(json.dumps(collection, cls=AASToJsonEncoder))

        self.assertEqual(["p0", "p1", "p2"], [e["idShort"] for e in data["value"]])

    def test_object_store_identifiables_sorted_by_id_ok(self) -> None:
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore(
            [model.Submodel(identifier) for identifier in ["urn:sm2", "urn:sm1", "urn:sm0"]]
        )

        data = json.loads(object_store_to_json(store))

        self.assertEqual(
            ["urn:sm0", "urn:sm1", "urn:sm2"], [sm["id"] for sm in data["submodels"]]
        )