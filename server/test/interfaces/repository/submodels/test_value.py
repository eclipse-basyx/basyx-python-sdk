# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Endpoint tests for the ``/submodels`` ``$value`` content modifier (ValueOnly-Serialization).

Covers:
    * ``GET /submodels/$value``
    * ``GET /submodels/<id>/$value``
    * ``GET /submodels/<id>/submodel-elements/$value``
    * ``GET /submodels/<id>/submodel-elements/<idShortPath>/$value``

ValueOnly-Serialization is JSON-only; XML variants are only used for the ``406 Not Acceptable`` cases.
"""

import base64
import math
from typing import Any

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.examples.data.example_aas import create_example_bill_of_material_submodel
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ...format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from ..helpers import RepositoryEndpointTestBase


# Top-level submodel elements of ``create_example_submodel()`` that have a ValueOnly representation, in document
# order. ExampleOperation and ExampleCapability have none and are omitted by the ``$value`` routes.
VALUE_ONLY_ID_SHORTS = (
    "ExampleRelationshipElement",
    "ExampleAnnotatedRelationshipElement",
    "ExampleBasicEventElement",
    "ExampleSubmodelCollection",
)

NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
NESTED_BLOB = "ExampleSubmodelCollection.ExampleBlob"
NESTED_FILE = "ExampleSubmodelCollection.ExampleFile"

TYPED_SUBMODEL_ID = "http://example.org/Typed_Submodel"


def create_typed_submodel() -> model.Submodel:
    """
    A Submodel containing the value types and edge cases of the ValueOnly serialization that aren't part of the
    example data.
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
class SubmodelsValueEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$value`` modifier on the Submodel resource (``/submodels[/<id>]``).

    ValueOnly-Serialization is JSON-only; XML variants are added only where the server must respond
    with ``406 Not Acceptable``.
    """

    SECOND_ID = "https://example.org/Test_Submodel_Second"

    def two_submodels_store(self) -> model.DictIdentifiableStore:
        store: model.DictIdentifiableStore = model.DictIdentifiableStore()
        store.add(create_example_submodel())
        second = create_example_submodel()
        second.id = self.SECOND_ID
        second.id_short = "SecondSubmodel"
        store.add(second)
        return store

    # ------------------------------------------------------------------ GET /submodels/$value

    @with_json_client
    def test_submodels_value_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$value")

        self.assert_ok(response)
        values = format_client.parse_collection(response)
        self.assertEqual(2, len(values))
        for value in values:
            self.assertEqual(set(VALUE_ONLY_ID_SHORTS), set(value))

    @with_json_client
    def test_submodels_value_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$value", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$value

    @with_json_client
    def test_submodel_value_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value")

        self.assert_ok(response)
        value = format_client.parse_object(response)
        # ExampleOperation and ExampleCapability have no ValueOnly representation and are omitted
        self.assertEqual(set(VALUE_ONLY_ID_SHORTS), set(value))
        self.assertEqual("exampleValue", value["ExampleSubmodelCollection"]["ExampleProperty"])

    @with_json_client
    def test_submodel_value_get_level_core_empties_nested_containers(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value?level=core")

        self.assert_ok(response)
        value = format_client.parse_object(response)
        # the direct children are present, their children are not
        self.assertEqual({}, value["ExampleSubmodelCollection"])
        self.assertEqual([], value["ExampleAnnotatedRelationshipElement"]["annotations"])

    @with_json_client
    def test_submodel_value_get_empty_submodel(self, format_client: FormatClient):
        self.object_store.add(model.Submodel(id_=TYPED_SUBMODEL_ID))

        response = format_client.get(f"/submodels/{base64url_encode(TYPED_SUBMODEL_ID)}/$value")

        self.assert_ok(response)
        self.assertEqual({}, format_client.parse_object(response))

    @with_json_client
    def test_submodel_value_get_huge_integer(self, format_client: FormatClient):
        self.object_store.add(create_typed_submodel())

        response = format_client.get(f"/submodels/{base64url_encode(TYPED_SUBMODEL_ID)}/$value")

        self.assert_ok(response)
        value = format_client.parse_object(response)
        # integers that exceed the range of a float are also serialized when the whole Submodel is requested
        self.assertEqual(10**400, value["HugeIntProperty"])
        self.assertEqual(42, value["IntProperty"])

    @with_json_client
    def test_submodel_value_get_omits_property_without_value(self, format_client: FormatClient):
        self.object_store.add(create_typed_submodel())

        response = format_client.get(f"/submodels/{base64url_encode(TYPED_SUBMODEL_ID)}/$value")

        self.assert_ok(response)
        self.assertNotIn("EmptyProperty", format_client.parse_object(response))

    @with_json_client
    def test_submodel_value_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"/submodels/{base64url_encode('https://example.org/unknown')}/$value")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_value_get_xml_not_acceptable(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodel_value_get_invalid_level_returns_400(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value?level=invalid")

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_value_get_extent_not_implemented(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}/$value?extent=withBlobValue"
        )

        self.assert_error(response, 501)


@inject_format_clients
class SubmodelElementsValueEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$value`` modifier on the ``submodel-elements`` subtree.
    """

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    def _get_element_value(self, format_client: FormatClient, submodel_id: str, id_short_path: str) -> Any:
        response = format_client.get(f"{self.elements_path(submodel_id, id_short_path)}/$value")
        self.assert_ok(response)
        return format_client.parse_object(response)

    # ------------------------------------------------------------------ GET .../submodel-elements/$value

    @with_json_client
    def test_submodel_elements_value_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$value")

        self.assert_ok(response)
        values = format_client.parse_collection(response)
        # each element is an {idShort: value} object, ExampleOperation and ExampleCapability are omitted
        self.assertEqual(list(VALUE_ONLY_ID_SHORTS), [id_short for value in values for id_short in value])

    @with_json_client
    def test_submodel_elements_value_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(f"{self.elements_path(submodel.id)}/$value", limit=3, max_pages=2)

        self.assertEqual(
            list(VALUE_ONLY_ID_SHORTS), [id_short for page in pages for value in page for id_short in value]
        )

    # ------------------------------------------------------------------ GET .../<idShortPath>/$value

    @with_json_client
    def test_submodel_element_value_get_property_value_types(self, format_client: FormatClient):
        self.object_store.add(create_typed_submodel())

        def get_value(id_short_path: str) -> Any:
            return self._get_element_value(format_client, TYPED_SUBMODEL_ID, id_short_path)

        self.assertEqual(42, get_value("IntProperty"))
        self.assertEqual(False, get_value("BoolProperty"))
        self.assertEqual(1.5, get_value("DoubleProperty"))
        # JSON has no representation for NaN, INF and -INF, so the XSD representation is returned instead
        self.assertEqual("NaN", get_value("NanProperty"))
        # integers are not converted to float, as that would raise an OverflowError for large values
        self.assertEqual(10**400, get_value("HugeIntProperty"))
        self.assertEqual("2026-08-31", get_value("DateProperty"))
        self.assertIsNone(get_value("EmptyProperty"))

    @with_json_client
    def test_submodel_element_value_get_list_keeps_indices(self, format_client: FormatClient):
        self.object_store.add(create_typed_submodel())

        value = self._get_element_value(format_client, TYPED_SUBMODEL_ID, "ListWithEmptyElement")

        self.assertEqual(["first", None, "third"], value)

    @with_json_client
    def test_submodel_element_value_get_multi_language_property(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(
            format_client, submodel.id, f"{NESTED_COLLECTION}.ExampleMultiLanguageProperty"
        )

        self.assertEqual(2, len(value))
        self.assertEqual([1, 1], [len(entry) for entry in value])
        self.assertEqual({"de", "en-US"}, {next(iter(entry)) for entry in value})

    @with_json_client
    def test_submodel_element_value_get_range(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, f"{NESTED_COLLECTION}.ExampleRange")

        self.assertEqual({"min": 0, "max": 100}, value)

    @with_json_client
    def test_submodel_element_value_get_blob(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, NESTED_BLOB)

        self.assertEqual(
            {"contentType": "application/pdf", "value": base64.b64encode(b"\x01\x02\x03\x04\x05").decode()}, value
        )

    @with_json_client
    def test_submodel_element_value_get_file(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, NESTED_FILE)

        self.assertEqual({"contentType": "application/pdf", "value": "/TestFile.pdf"}, value)

    @with_json_client
    def test_submodel_element_value_get_reference_element(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, f"{NESTED_COLLECTION}.ExampleReferenceElement")

        self.assertEqual("ModelReference", value["type"])
        self.assertEqual("Submodel", value["keys"][0]["type"])

    @with_json_client
    def test_submodel_element_value_get_relationship_element(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, "ExampleRelationshipElement")

        self.assertEqual({"first", "second"}, set(value))
        self.assertEqual("ModelReference", value["first"]["type"])

    @with_json_client
    def test_submodel_element_value_get_annotated_relationship_element(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, "ExampleAnnotatedRelationshipElement")

        self.assertEqual({"first", "second", "annotations"}, set(value))
        self.assertIn({"ExampleAnnotatedProperty": "exampleValue"}, value["annotations"])

    @with_json_client
    def test_submodel_element_value_get_basic_event_element(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, "ExampleBasicEventElement")

        self.assertEqual(["observed"], list(value))
        self.assertEqual("ModelReference", value["observed"]["type"])

    @with_json_client
    def test_submodel_element_value_get_entity(self, format_client: FormatClient):
        submodel = create_example_bill_of_material_submodel()
        self.object_store.add(submodel)

        value = self._get_element_value(format_client, submodel.id, "ExampleEntity")

        self.assertEqual("SelfManagedEntity", value["entityType"])
        self.assertEqual("http://example.org/TestAsset/", value["globalAssetId"])
        self.assertEqual("exampleValue", value["statements"]["ExampleProperty"])
        self.assertEqual("TestKey", value["specificAssetIds"][0]["name"])

    @with_json_client
    def test_submodel_element_value_get_collection(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        value = self._get_element_value(format_client, submodel.id, NESTED_COLLECTION)

        self.assertIn("ExampleBlob", value)
        self.assertEqual("exampleValue", value["ExampleProperty"])

    @with_json_client
    def test_submodel_element_value_get_rejects_operation_and_capability(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        for id_short in ("ExampleOperation", "ExampleCapability"):
            with self.subTest(id_short=id_short):
                response = format_client.get(f"{self.elements_path(submodel.id, id_short)}/$value")
                self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_value_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'DoesNotExist')}/$value")

        self.assert_error(response, 404)
