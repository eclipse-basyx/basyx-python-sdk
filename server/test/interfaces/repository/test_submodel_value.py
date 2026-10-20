# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import math

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.examples.data.example_aas import create_full_example

from ..format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from .helpers import RepositoryEndpointTestBase

TEST_SUBMODEL_ID = "https://example.org/Test_Submodel"
IDENTIFICATION_SUBMODEL_ID = "http://example.org/Submodels/Assets/TestAsset/Identification"
BILL_OF_MATERIAL_SUBMODEL_ID = "http://example.org/Submodels/Assets/TestAsset/BillOfMaterial"
TYPED_SUBMODEL_ID = "http://example.org/Typed_Submodel"


def _create_typed_submodel() -> model.Submodel:
    """
    A Submodel containing the value types and edge cases that aren't part of the example data.
    """
    return model.Submodel(
        id_=TYPED_SUBMODEL_ID,
        submodel_element=(
            model.Property(id_short="IntProperty", value_type=model.datatypes.Int, value=42),
            model.Property(id_short="BoolProperty", value_type=model.datatypes.Boolean, value=False),
            model.Property(id_short="DoubleProperty", value_type=model.datatypes.Double, value=1.5),
            model.Property(id_short="NanProperty", value_type=model.datatypes.Double, value=math.nan),
            # xs:integer is unbounded, this value cannot be represented as a float
            model.Property(id_short="HugeIntProperty", value_type=model.datatypes.Integer, value=10**400),
            model.Property(
                id_short="DateProperty", value_type=model.datatypes.Date, value=model.datatypes.Date(2026, 8, 31)
            ),
            model.Property(id_short="EmptyProperty", value_type=model.datatypes.String, value=None),
            model.SubmodelElementList(
                id_short="ListWithEmptyElement",
                type_value_list_element=model.Property,
                value_type_list_element=model.datatypes.String,
                value=(
                    model.Property(id_short=None, value_type=model.datatypes.String, value="first"),
                    model.Property(id_short=None, value_type=model.datatypes.String, value=None),
                    model.Property(id_short=None, value_type=model.datatypes.String, value="third"),
                ),
            ),
        ),
    )


@inject_format_clients
class SubmodelValueEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$value`` routes of the ``/submodels`` subtree of
    :class:`~app.interfaces.repository.WSGIApp`.

    The ValueOnly serialization is only defined for JSON. Therefore, the tests are generated for the
    :class:`~..format_utils.JsonFormatClient` only, except for the ones checking that XML is rejected.
    """

    def setUp(self) -> None:
        super().setUp()
        self.object_store.update(create_full_example())
        self.object_store.add(_create_typed_submodel())

    @staticmethod
    def submodel_path(submodel_id: str) -> str:
        return f"/submodels/{base64url_encode(submodel_id)}"

    @classmethod
    def elements_path(cls, submodel_id: str, id_short_path: str = "") -> str:
        base = f"{cls.submodel_path(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    def get_value(self, format_client: FormatClient, path: str):
        response = format_client.get(path)
        self.assert_ok(response)
        return format_client.parse_object(response)

    # ------------------------------------------------------------------ GET /submodels/$value

    @with_json_client
    def test_submodel_all_value_get(self, format_client: FormatClient):
        response = format_client.get("/submodels/$value")

        self.assert_ok(response)
        self.assertIn(
            {"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"},
            format_client.parse_collection(response),
        )

    @with_json_client
    def test_submodel_all_value_get_pagination_limit(self, format_client: FormatClient):
        response = format_client.get("/submodels/$value?limit=1")

        self.assert_ok(response)
        self.assertEqual(1, len(format_client.parse_collection(response)))
        self.assertEqual("2", format_client.next_cursor(response))

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$value

    @with_json_client
    def test_submodel_value_get(self, format_client: FormatClient):
        value = self.get_value(format_client, f"{self.submodel_path(IDENTIFICATION_SUBMODEL_ID)}/$value")

        self.assertEqual({"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"}, value)

    @with_json_client
    def test_submodel_value_get_omits_operations_and_capabilities(self, format_client: FormatClient):
        value = self.get_value(format_client, f"{self.submodel_path(TEST_SUBMODEL_ID)}/$value")

        self.assertNotIn("ExampleOperation", value)
        self.assertNotIn("ExampleCapability", value)

    @with_json_client
    def test_submodel_value_get_level_core_empties_nested_containers(self, format_client: FormatClient):
        value = self.get_value(format_client, f"{self.submodel_path(TEST_SUBMODEL_ID)}/$value?level=core")

        # the direct children are present, their children are not
        self.assertIn("ExampleSubmodelCollection", value)
        self.assertEqual({}, value["ExampleSubmodelCollection"])
        self.assertEqual([], value["ExampleAnnotatedRelationshipElement"]["annotations"])

    @with_json_client
    def test_submodel_value_get_huge_integer(self, format_client: FormatClient):
        # integers that exceed the range of a float are also serialized when the whole Submodel is requested
        value = self.get_value(format_client, f"{self.submodel_path(TYPED_SUBMODEL_ID)}/$value")

        self.assertEqual(10**400, value["HugeIntProperty"])
        self.assertEqual(42, value["IntProperty"])

    @with_json_client
    def test_submodel_value_get_omits_property_without_value(self, format_client: FormatClient):
        value = self.get_value(format_client, f"{self.submodel_path(TYPED_SUBMODEL_ID)}/$value")

        self.assertNotIn("EmptyProperty", value)

    @with_json_client
    def test_submodel_value_get_empty_submodel(self, format_client: FormatClient):
        empty_submodel_id = "http://example.org/Empty_Submodel"
        self.object_store.add(model.Submodel(id_=empty_submodel_id))

        value = self.get_value(format_client, f"{self.submodel_path(empty_submodel_id)}/$value")

        self.assertEqual({}, value)

    @with_json_client
    def test_submodel_value_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.submodel_path('https://example.org/unknown')}/$value")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_value_get_invalid_level_returns_400(self, format_client: FormatClient):
        response = format_client.get(f"{self.submodel_path(TEST_SUBMODEL_ID)}/$value?level=bogus")

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_value_get_extent_not_implemented(self, format_client: FormatClient):
        response = format_client.get(f"{self.submodel_path(TEST_SUBMODEL_ID)}/$value?extent=withBlobValue")

        self.assert_error(response, 501)

    # ------------------------------------------------------------------ GET .../submodel-elements/$value

    @with_json_client
    def test_submodel_elements_value_get(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(IDENTIFICATION_SUBMODEL_ID)}/$value")

        self.assert_ok(response)
        self.assertEqual(
            [{"ManufacturerName": "ACPLT"}, {"InstanceId": "978-8234-234-342"}],
            format_client.parse_collection(response),
        )

    @with_json_client
    def test_submodel_elements_value_get_omits_operations_and_capabilities(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(TEST_SUBMODEL_ID)}/$value")

        self.assert_ok(response)
        id_shorts = [next(iter(entry)) for entry in format_client.parse_collection(response)]
        self.assertNotIn("ExampleOperation", id_shorts)
        self.assertNotIn("ExampleCapability", id_shorts)

    @with_json_client
    def test_submodel_elements_value_get_pagination_limit(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(IDENTIFICATION_SUBMODEL_ID)}/$value?limit=1")

        self.assert_ok(response)
        self.assertEqual([{"ManufacturerName": "ACPLT"}], format_client.parse_collection(response))
        self.assertEqual("2", format_client.next_cursor(response))

    # ------------------------------------------------------------------ GET .../<idShortPath>/$value

    @with_json_client
    def test_property_value_get_value_types(self, format_client: FormatClient):
        def get_property_value(id_short: str):
            return self.get_value(format_client, f"{self.elements_path(TYPED_SUBMODEL_ID, id_short)}/$value")

        self.assertEqual(42, get_property_value("IntProperty"))
        self.assertEqual(False, get_property_value("BoolProperty"))
        self.assertEqual(1.5, get_property_value("DoubleProperty"))
        # JSON has no representation for NaN, INF and -INF, so the XSD representation is returned instead
        self.assertEqual("NaN", get_property_value("NanProperty"))
        # integers are not converted to float, as that would raise an OverflowError for large values
        self.assertEqual(10**400, get_property_value("HugeIntProperty"))
        self.assertEqual("2026-08-31", get_property_value("DateProperty"))
        self.assertIsNone(get_property_value("EmptyProperty"))

    @with_json_client
    def test_submodel_element_list_value_get_keeps_indices(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TYPED_SUBMODEL_ID, 'ListWithEmptyElement')}/$value"
        )

        self.assertEqual(["first", None, "third"], value)

    @with_json_client
    def test_multi_language_property_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client,
            f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection.ExampleMultiLanguageProperty')}"
            "/$value",
        )

        self.assertEqual(2, len(value))
        self.assertEqual([1, 1], [len(entry) for entry in value])
        self.assertEqual(["de", "en-US"], [next(iter(entry)) for entry in value])

    @with_json_client
    def test_range_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection.ExampleRange')}/$value"
        )

        self.assertEqual({"min": 0, "max": 100}, value)

    @with_json_client
    def test_blob_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection.ExampleBlob')}/$value"
        )

        self.assertEqual(
            {"contentType": "application/pdf", "value": base64.b64encode(b"\x01\x02\x03\x04\x05").decode()}, value
        )

    @with_json_client
    def test_file_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection.ExampleFile')}/$value"
        )

        self.assertEqual({"contentType": "application/pdf", "value": "/TestFile.pdf"}, value)

    @with_json_client
    def test_reference_element_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client,
            f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection.ExampleReferenceElement')}/$value",
        )

        self.assertEqual("ModelReference", value["type"])
        self.assertEqual("Submodel", value["keys"][0]["type"])

    @with_json_client
    def test_relationship_element_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleRelationshipElement')}/$value"
        )

        self.assertEqual({"first", "second"}, set(value))
        self.assertEqual("ModelReference", value["first"]["type"])

    @with_json_client
    def test_annotated_relationship_element_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleAnnotatedRelationshipElement')}/$value"
        )

        self.assertEqual({"first", "second", "annotations"}, set(value))
        self.assertIn({"ExampleAnnotatedProperty": "exampleValue"}, value["annotations"])

    @with_json_client
    def test_basic_event_element_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleBasicEventElement')}/$value"
        )

        self.assertEqual(["observed"], list(value))
        self.assertEqual("ModelReference", value["observed"]["type"])

    @with_json_client
    def test_entity_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(BILL_OF_MATERIAL_SUBMODEL_ID, 'ExampleEntity')}/$value"
        )

        self.assertEqual("SelfManagedEntity", value["entityType"])
        self.assertEqual("http://example.org/TestAsset/", value["globalAssetId"])
        self.assertEqual("exampleValue", value["statements"]["ExampleProperty"])
        self.assertEqual("TestKey", value["specificAssetIds"][0]["name"])

    @with_json_client
    def test_submodel_element_collection_value_get(self, format_client: FormatClient):
        value = self.get_value(
            format_client, f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleSubmodelCollection')}/$value"
        )

        self.assertIn("ExampleBlob", value)
        self.assertIn("ExampleSubmodelList", value)

    @with_json_client
    def test_operation_and_capability_value_get_returns_400(self, format_client: FormatClient):
        for id_short in ("ExampleOperation", "ExampleCapability"):
            with self.subTest(id_short=id_short):
                response = format_client.get(f"{self.elements_path(TEST_SUBMODEL_ID, id_short)}/$value")

                self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_value_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(TEST_SUBMODEL_ID, 'DoesNotExist')}/$value")

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ content negotiation

    @with_xml_client
    def test_value_get_xml_not_acceptable(self, format_client: FormatClient):
        for path in (
            "/submodels/$value",
            f"{self.submodel_path(TEST_SUBMODEL_ID)}/$value",
            f"{self.elements_path(TEST_SUBMODEL_ID)}/$value",
            f"{self.elements_path(TEST_SUBMODEL_ID, 'ExampleRelationshipElement')}/$value",
        ):
            with self.subTest(path=path):
                response = format_client.get(path)

                self.assert_error(response, 406)
