# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import decimal
import json
import math
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import ValueOnlyJsonEncoder
from basyx.aas.examples.data import example_aas, example_aas_mandatory_attributes

EXAMPLE_SUBMODEL_ID = "http://example.org/Test_Submodel"


class TestValueOnlyJsonEncoder(unittest.TestCase):
    def setUp(self):
        self.submodel = example_aas.create_example_submodel()

    # ------------------------------------------------------------------ Submodel

    def test_submodel_ok(self):
        submodel = example_aas.create_example_asset_identification_submodel()

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"}, parsed_output)

    def test_submodel_omits_operation_and_capability_ok(self):
        out_str = json.dumps(self.submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleRelationshipElement",
            "ExampleAnnotatedRelationshipElement",
            "ExampleBasicEventElement",
            "ExampleSubmodelCollection",
        ], parsed_output.keys())

    def test_submodel_omits_elements_without_value_ok(self):
        submodel = model.Submodel("https://example.org/Submodel", submodel_element=[
            model.Property("FilledProperty", model.datatypes.String, "exampleValue"),
            model.Property("EmptyProperty", model.datatypes.String),
            model.MultiLanguageProperty("EmptyMultiLanguageProperty"),
            model.Range("EmptyRange", model.datatypes.Int),
            model.File("EmptyFile", "application/pdf"),
            model.ReferenceElement("EmptyReferenceElement"),
            model.RelationshipElement("EmptyRelationshipElement"),
        ])

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"FilledProperty": "exampleValue"}, parsed_output)

    def test_submodel_omits_containers_of_omitted_elements_ok(self):
        submodel = model.Submodel("https://example.org/Submodel", submodel_element=[
            model.Property("FilledProperty", model.datatypes.String, "exampleValue"),
            model.SubmodelElementCollection("CollectionOfOperations", [model.Operation("Operation")]),
            model.SubmodelElementList("ListOfOperations", model.Operation, [model.Operation(None)]),
        ])

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"FilledProperty": "exampleValue"}, parsed_output)

    def test_empty_submodel_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_empty_submodel()

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({}, parsed_output)

    # ------------------------------------------------------------------ SubmodelElementCollection / -List

    def test_submodel_element_collection_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleBlob",
            "ExampleFile",
            "ExampleFileURI",
            "ExampleMultiLanguageProperty",
            "ExampleRange",
            "ExampleReferenceElement",
            "ExampleSubmodelList",
        ], parsed_output.keys())
        self.assertEqual({"min": 0, "max": 100}, parsed_output["ExampleRange"])
        self.assertEqual(["exampleValue", "exampleValue"], parsed_output["ExampleSubmodelList"])

    def test_submodel_element_list_ok(self):
        sml = self.submodel.get_referable("ExampleSubmodelCollection.ExampleSubmodelList")

        out_str = json.dumps(sml, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["exampleValue", "exampleValue"], parsed_output)

    def test_submodel_element_list_keeps_index_of_element_without_value_ok(self):
        sml = model.SubmodelElementList("List", model.Property, [
            model.Property(None, model.datatypes.String, "first"),
            model.Property(None, model.datatypes.String),
            model.Property(None, model.datatypes.String, "third"),
        ], value_type_list_element=model.datatypes.String)

        out_str = json.dumps(sml, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["first", None, "third"], parsed_output)

    def test_empty_submodel_element_list_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList2")

        out_str = json.dumps(sml, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual([], parsed_output)

    # ------------------------------------------------------------------ Property data type to value mapping

    def test_property_ok(self):
        submodel = example_aas.create_example_asset_identification_submodel()
        prop = submodel.get_referable("ManufacturerName")

        out_str = json.dumps(prop, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual("ACPLT", parsed_output)

    def test_property_without_value_ok(self):
        prop = model.Property("EmptyProperty", model.datatypes.String)

        out_str = json.dumps(prop, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsNone(parsed_output)

    def test_property_boolean_types_ok(self):
        smc = model.SubmodelElementCollection("Booleans", [
            model.Property("True", model.datatypes.Boolean, True),
            model.Property("False", model.datatypes.Boolean, False),
        ])

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"True": True, "False": False}, parsed_output)

    def test_property_number_types_ok(self):
        smc = model.SubmodelElementCollection("Numbers", [
            model.Property("Int", model.datatypes.Int, -1),
            model.Property("Long", model.datatypes.Long, 9223372036854775807),
            model.Property("UnsignedLong", model.datatypes.UnsignedLong, 18446744073709551615),
            model.Property("Zero", model.datatypes.NonNegativeInteger, 0),
            # xs:integer is unbounded, this value cannot be represented as a float
            model.Property("HugeInteger", model.datatypes.Integer, 10**400),
            model.Property("Decimal", model.datatypes.Decimal, decimal.Decimal("-1.23")),
            model.Property("Double", model.datatypes.Double, 234.567e8),
            model.Property("Float", model.datatypes.Float, 1.5),
        ])

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "Int": -1,
            "Long": 9223372036854775807,
            "UnsignedLong": 18446744073709551615,
            "Zero": 0,
            "HugeInteger": 10**400,
            "Decimal": -1.23,
            "Double": 234.567e8,
            "Float": 1.5,
        }, parsed_output)

    def test_property_non_finite_double_ok(self):
        # JSON has no representation for NaN, INF and -INF, so the XSD representation is used instead
        smc = model.SubmodelElementCollection("NonFinite", [
            model.Property("NaN", model.datatypes.Double, math.nan),
            model.Property("Inf", model.datatypes.Double, math.inf),
            model.Property("NegativeInf", model.datatypes.Double, -math.inf),
        ])

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"NaN": "NaN", "Inf": "INF", "NegativeInf": "-INF"}, parsed_output)

    def test_property_string_types_ok(self):
        smc = model.SubmodelElementCollection("Strings", [
            model.Property("String", model.datatypes.String, "Hello world"),
            model.Property("EmptyString", model.datatypes.String, ""),
            model.Property("Date", model.datatypes.Date, model.datatypes.Date(2000, 1, 1)),
            model.Property("Time", model.datatypes.Time, model.datatypes.Time(14, 23)),
            model.Property("DateTime", model.datatypes.DateTime, model.datatypes.DateTime(2000, 1, 1, 14, 23)),
            model.Property("GYear", model.datatypes.GYear, model.datatypes.GYear(2000)),
            model.Property("Duration", model.datatypes.Duration, model.datatypes.Duration(days=30)),
            model.Property("HexBinary", model.datatypes.HexBinary, model.datatypes.HexBinary(b"kumowashere")),
            model.Property("Base64Binary", model.datatypes.Base64Binary,
                           model.datatypes.Base64Binary(b"Hello, World!")),
            model.Property("AnyURI", model.datatypes.AnyURI, model.datatypes.AnyURI("urn:example:company:1.0.0")),
        ])

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "String": "Hello world",
            "EmptyString": "",
            "Date": "2000-01-01",
            "Time": "14:23:00",
            "DateTime": "2000-01-01T14:23:00",
            "GYear": "2000",
            "Duration": "P30D",
            "HexBinary": "6b756d6f77617368657265",
            "Base64Binary": "SGVsbG8sIFdvcmxkIQ==",
            "AnyURI": "urn:example:company:1.0.0",
        }, parsed_output)

    # ------------------------------------------------------------------ other SubmodelElements

    def test_multi_language_property_ok(self):
        mlp = self.submodel.get_referable("ExampleSubmodelCollection.ExampleMultiLanguageProperty")

        out_str = json.dumps(mlp, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            {"de": "Beispielwert für ein MultiLanguageProperty-Element"},
            {"en-US": "Example value of a MultiLanguageProperty element"},
        ], parsed_output)

    def test_multi_language_property_without_value_ok(self):
        mlp = model.MultiLanguageProperty("EmptyMultiLanguageProperty")

        out_str = json.dumps(mlp, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual([], parsed_output)

    def test_range_ok(self):
        range_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleRange")

        out_str = json.dumps(range_element, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"min": 0, "max": 100}, parsed_output)

    def test_blob_ok(self):
        blob = self.submodel.get_referable("ExampleSubmodelCollection.ExampleBlob")

        out_str = json.dumps(blob, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        # the value is base64 encoded b"\x01\x02\x03\x04\x05"
        self.assertEqual({"contentType": "application/pdf", "value": "AQIDBAU="}, parsed_output)

    def test_file_ok(self):
        file = self.submodel.get_referable("ExampleSubmodelCollection.ExampleFile")

        out_str = json.dumps(file, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/pdf", "value": "/TestFile.pdf"}, parsed_output)

    def test_reference_element_ok(self):
        reference_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleReferenceElement")

        out_str = json.dumps(reference_element, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "type": "ModelReference",
            "keys": [
                {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                {"type": "Property", "value": "ExampleProperty"},
            ],
        }, parsed_output)

    def test_relationship_element_ok(self):
        relationship_element = self.submodel.get_referable("ExampleRelationshipElement")

        out_str = json.dumps(relationship_element, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "first": {
                "type": "ModelReference",
                "keys": [
                    {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                    {"type": "Property", "value": "ExampleProperty"},
                ],
            },
            "second": {
                "type": "ModelReference",
                "keys": [
                    {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                    {"type": "Property", "value": "ExampleProperty2"},
                ],
            },
        }, parsed_output)

    def test_annotated_relationship_element_ok(self):
        are = self.submodel.get_referable("ExampleAnnotatedRelationshipElement")

        out_str = json.dumps(are, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "first": {
                "type": "ModelReference",
                "keys": [
                    {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                    {"type": "Property", "value": "ExampleProperty"},
                ],
            },
            "second": {
                "type": "ModelReference",
                "keys": [
                    {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                    {"type": "Property", "value": "ExampleProperty2"},
                ],
            },
            "annotations": {
                "ExampleAnnotatedProperty": "exampleValue",
                "ExampleAnnotatedRange": {"min": 1, "max": 5},
            },
        }, parsed_output)

    def test_annotated_relationship_element_without_annotation_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        are = submodel.get_referable("ExampleAnnotatedRelationshipElement")

        out_str = json.dumps(are, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual(["first", "second"], parsed_output.keys())

    def test_entity_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity")

        out_str = json.dumps(entity, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "statements": {
                "ExampleProperty": "exampleValue",
                "ExampleProperty2": "exampleValue2",
            },
            "entityType": "SelfManagedEntity",
            "globalAssetId": "http://example.org/TestAsset/",
            "specificAssetIds": [{
                "name": "TestKey",
                "value": "TestValue",
                "externalSubjectId": {
                    "type": "ExternalReference",
                    "keys": [{"type": "GlobalReference", "value": "http://example.org/SpecificAssetId/"}],
                },
            }],
        }, parsed_output)

    def test_entity_without_statements_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity2")

        out_str = json.dumps(entity, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertNotIn("statements", parsed_output)

    def test_submodel_keeps_co_managed_entity_with_statements_ok(self):
        submodel = model.Submodel("https://example.org/Submodel", submodel_element=[
            model.Entity("CoManagedEntity", model.EntityType.CO_MANAGED_ENTITY, statement=[
                model.Property("Statement", model.datatypes.String, "exampleValue"),
            ]),
        ])

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "CoManagedEntity": {
                "statements": {"Statement": "exampleValue"},
                "entityType": "CoManagedEntity",
            },
        }, parsed_output)

    def test_basic_event_element_ok(self):
        basic_event_element = self.submodel.get_referable("ExampleBasicEventElement")

        out_str = json.dumps(basic_event_element, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "observed": {
                "type": "ModelReference",
                "keys": [
                    {"type": "Submodel", "value": EXAMPLE_SUBMODEL_ID},
                    {"type": "Property", "value": "ExampleProperty"},
                ],
            },
        }, parsed_output)

    def test_operation_fail(self):
        operation = self.submodel.get_referable("ExampleOperation")

        with self.assertRaises(TypeError):
            json.dumps(operation, cls=ValueOnlyJsonEncoder)

    def test_capability_fail(self):
        capability = self.submodel.get_referable("ExampleCapability")

        with self.assertRaises(TypeError):
            json.dumps(capability, cls=ValueOnlyJsonEncoder)

class TestValueOnlyJsonEncoderCore(unittest.TestCase):

    def setUp(self):
        self.submodel = example_aas.create_example_submodel()

    def test_deep_is_default_ok(self):
        deep_output = json.loads(json.dumps(self.submodel, cls=ValueOnlyJsonEncoder, deep=True))

        out_str = json.dumps(self.submodel, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_submodel_core_empties_submodel_element_collection_ok(self):
        out_str = json.dumps(self.submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({}, parsed_output["ExampleSubmodelCollection"])

    def test_submodel_element_collection_core_empties_submodel_element_list_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual([], parsed_output["ExampleSubmodelList"])
        self.assertEqual({"min": 0, "max": 100}, parsed_output["ExampleRange"])

    def test_submodel_core_keeps_leaf_values_ok(self):
        submodel = example_aas.create_example_asset_identification_submodel()

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"}, parsed_output)

    def test_submodel_element_list_core_empties_submodel_element_collections_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList")

        out_str = json.dumps(sml, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual([{}, {}], parsed_output)

    def test_submodel_core_empties_submodel_element_list_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual([], parsed_output["ExampleSubmodelList"])

    def test_submodel_core_omits_entity_statements_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        deep_output = json.loads(json.dumps(submodel, cls=ValueOnlyJsonEncoder))
        expected = deep_output["ExampleEntity"]
        expected.pop("statements")

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(expected, parsed_output["ExampleEntity"])

    def test_entity_core_keeps_statements_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity")

        out_str = json.dumps(entity, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({"ExampleProperty": "exampleValue", "ExampleProperty2": "exampleValue2"},
                         parsed_output["statements"])

    def test_entity_core_empties_statement_submodel_element_collection_ok(self):
        collection = model.SubmodelElementCollection(
            "ExampleCollection",
            value=[model.Property("ExampleProperty", model.datatypes.String, value="exampleValue")],
        )
        entity = model.Entity("ExampleEntity", model.EntityType.CO_MANAGED_ENTITY, statement=[collection])

        out_str = json.dumps(entity, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({"ExampleCollection": {}}, parsed_output["statements"])

    def test_submodel_core_omits_annotated_relationship_element_annotations_ok(self):
        deep_output = json.loads(json.dumps(self.submodel, cls=ValueOnlyJsonEncoder))
        expected = deep_output["ExampleAnnotatedRelationshipElement"]
        expected.pop("annotations")

        out_str = json.dumps(self.submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(expected, parsed_output["ExampleAnnotatedRelationshipElement"])

    def test_annotated_relationship_element_core_keeps_annotations_ok(self):
        are = self.submodel.get_referable("ExampleAnnotatedRelationshipElement")
        deep_output = json.loads(json.dumps(are, cls=ValueOnlyJsonEncoder))

        out_str = json.dumps(are, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_leaf_element_core_ok(self):
        range_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleRange")

        out_str = json.dumps(range_element, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({"min": 0, "max": 100}, parsed_output)

    def test_submodel_core_keeps_containers_of_omitted_elements_ok(self):
        submodel = model.Submodel("https://example.org/Submodel", submodel_element=[
            model.Property("FilledProperty", model.datatypes.String, "exampleValue"),
            model.SubmodelElementCollection("CollectionOfOperations", [model.Operation("Operation")]),
            model.SubmodelElementList("ListOfOperations", model.Operation, [model.Operation(None)]),
        ])

        out_str = json.dumps(submodel, cls=ValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({
            "FilledProperty": "exampleValue",
            "CollectionOfOperations": {},
            "ListOfOperations": [],
        }, parsed_output)


class WithoutBlobValueValueOnlyJsonEncoder(ValueOnlyJsonEncoder):
    with_blob_value = False


class TestValueOnlyJsonEncoderBlobValue(unittest.TestCase):
    def setUp(self):
        self.submodel = example_aas.create_example_submodel()
        self.blob = self.submodel.get_referable("ExampleSubmodelCollection.ExampleBlob")

    def test_with_blob_value_is_default_ok(self):
        out_str = json.dumps(self.blob, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertTrue(ValueOnlyJsonEncoder.with_blob_value)
        # the value is base64 encoded b"\x01\x02\x03\x04\x05"
        self.assertEqual({"contentType": "application/pdf", "value": "AQIDBAU="}, parsed_output)

    def test_without_blob_value_omits_value_ok(self):
        out_str = json.dumps(self.blob, cls=WithoutBlobValueValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/pdf"}, parsed_output)

    def test_without_blob_value_keeps_nested_blob_ok(self):
        out_str = json.dumps(self.submodel, cls=WithoutBlobValueValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/pdf"}, parsed_output["ExampleSubmodelCollection"]["ExampleBlob"])

    def test_without_blob_value_core_omits_blob_value_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=WithoutBlobValueValueOnlyJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/pdf"}, parsed_output["ExampleBlob"])

    def test_with_blob_value_empty_value_ok(self):
        blob = model.Blob("EmptyBlob", "application/octet-stream", value=b"")

        out_str = json.dumps(blob, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/octet-stream", "value": ""}, parsed_output)

    def test_with_blob_value_without_value_ok(self):
        blob = model.Blob("BlobWithoutValue", "application/octet-stream")

        out_str = json.dumps(blob, cls=ValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual({"contentType": "application/octet-stream"}, parsed_output)
