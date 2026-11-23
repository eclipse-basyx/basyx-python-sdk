# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Endpoint tests for the ``/submodels`` ``$reference`` content modifier.

Covers:
    * ``GET /submodels/$reference``
    * ``GET /submodels/<id>/$reference``
    * ``GET /submodels/<id>/submodel-elements/$reference``
    * ``GET /submodels/<id>/submodel-elements/<idShortPath>/$reference``

The OpenAPI only defines JSON responses for ``$reference``, the server additionally supports XML.
"""

import json

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ...format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from ..helpers import RepositoryEndpointTestBase

NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
UNKNOWN_SUBMODEL_ID = "https://example.org/unknown"


class ReferenceEndpointTestBase(RepositoryEndpointTestBase):
    """
    Shared assertions on the response and the query parameters of the ``$reference`` routes.
    """

    def assert_model_reference(self, format_client: FormatClient, node: object, keys: list[tuple[str, str]]) -> None:
        """
        Ensures the node is a ``ModelReference`` with exactly the given ``(type, value)`` keys.
        """
        self.assertEqual("ModelReference", format_client.field(node, "type"))
        self.assertEqual(keys, format_client.reference_keys(node))

    def assert_level_handling(self, format_client: FormatClient, path: str) -> None:
        """
        The combination of ``level=deep`` and ``$reference`` is not allowed, thus only ``level=core`` is accepted.
        """
        with self.subTest(level="deep"):
            self.assert_error(format_client.get(f"{path}?level=deep"), 400)
        with self.subTest(level="invalid"):
            self.assert_error(format_client.get(f"{path}?level=invalid"), 400)
        with self.subTest(level="core"):
            self.assert_ok(format_client.get(f"{path}?level=core"))


@inject_format_clients
class SubmodelsReferenceEndpointsTest(ReferenceEndpointTestBase):
    """
    Endpoint tests for the ``$reference`` modifier on the Submodel resource (``/submodels[/<id>]``).
    """

    FIRST_ID = "https://example.org/Test_Submodel_Missing"
    SECOND_ID = "https://example.org/Test_Submodel_Second"

    def two_submodels_store(self) -> model.DictIdentifiableStore:
        store: model.DictIdentifiableStore = model.DictIdentifiableStore()
        store.add(create_example_submodel())
        second = create_example_submodel()
        second.id = self.SECOND_ID
        second.id_short = "SecondSubmodel"
        store.add(second)
        return store

    # ------------------------------------------------------------------ GET /submodels/$reference

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$reference")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertCountEqual(
            [[("Submodel", self.FIRST_ID)], [("Submodel", self.SECOND_ID)]],
            [format_client.reference_keys(reference) for reference in references],
        )
        for reference in references:
            self.assertEqual("ModelReference", format_client.field(reference, "type"))

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_empty(self, format_client: FormatClient):
        response = format_client.get("/submodels/$reference")

        self.assert_ok(response)
        self.assertEqual([], format_client.parse_collection(response))

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$reference", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])
        self.assertEqual(
            {self.FIRST_ID, self.SECOND_ID},
            {format_client.reference_target(reference) for page in pages for reference in page},
        )

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_filter_by_id_short(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$reference?idShort=SecondSubmodel")

        self.assert_ok(response)
        self.assertEqual(
            [self.SECOND_ID],
            [format_client.reference_target(reference) for reference in format_client.parse_collection(response)],
        )

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_filter_by_semantic_id(self, format_client: FormatClient):
        submodel = create_example_submodel()
        other_submodel = create_example_submodel()
        other_submodel.id = self.SECOND_ID
        other_submodel.semantic_id = model.ExternalReference(
            (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "https://example.org/other"),)
        )
        self.object_store.add(submodel)
        self.object_store.add(other_submodel)
        semantic_id = base64url_encode(json.dumps(submodel.semantic_id, cls=AASToJsonEncoder))

        response = format_client.get(f"/submodels/$reference?semanticId={semantic_id}")

        self.assert_ok(response)
        self.assertEqual(
            [submodel.id],
            [format_client.reference_target(reference) for reference in format_client.parse_collection(response)],
        )

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_level(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_level_handling(format_client, "/submodels/$reference")

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_rejects_extent_with_blob_value(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        response = format_client.get("/submodels/$reference?extent=WithBLOBValue")

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client, format_client.parse_object(response), [("Submodel", example_submodel.id)]
        )

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get_level(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_level_handling(format_client, f"/submodels/{base64url_encode(example_submodel.id)}/$reference")

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get_rejects_extent_with_blob_value(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}/$reference?extent=WithBLOBValue"
        )

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get_not_found(self, format_client: FormatClient):
        response = format_client.get(
            f"/submodels/{base64url_encode(UNKNOWN_SUBMODEL_ID)}/$reference"
        )

        self.assert_error(response, 404)


@inject_format_clients
class SubmodelElementsReferenceEndpointsTest(ReferenceEndpointTestBase):
    """
    Endpoint tests for the ``$reference`` modifier on the ``submodel-elements`` subtree.
    """

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    # ------------------------------------------------------------------ GET .../submodel-elements/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        # Child elements are ignored, thus only the top-level elements are expected
        expected_keys = [
            [("Submodel", submodel.id), (type(element).__name__, element.id_short)]
            for element in submodel.submodel_element
        ]

        response = format_client.get(f"{self.elements_path(submodel.id)}/$reference")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertCountEqual(expected_keys, [format_client.reference_keys(reference) for reference in references])
        for reference in references:
            self.assertEqual("ModelReference", format_client.field(reference, "type"))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_empty(self, format_client: FormatClient):
        submodel = model.Submodel("https://example.org/Test_Submodel_Empty")
        self.object_store.add(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id)}/$reference")

        self.assert_ok(response)
        self.assertEqual([], format_client.parse_collection(response))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        limit = 3
        total = len(submodel.submodel_element)
        expected_page_sizes = [min(limit, total - start) for start in range(0, total, limit)]

        pages = format_client.get_paginated(
            f"{self.elements_path(submodel.id)}/$reference", limit=limit, max_pages=len(expected_page_sizes)
        )

        self.assertEqual(expected_page_sizes, [len(page) for page in pages])
        self.assertEqual(
            {element.id_short for element in submodel.submodel_element},
            {format_client.reference_target(reference) for page in pages for reference in page},
        )

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_level_handling(format_client, f"{self.elements_path(submodel.id)}/$reference")

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_rejects_extent_with_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$reference?extent=WithBLOBValue")

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID)}/$reference")

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ GET .../<idShortPath>/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client,
            format_client.parse_object(response),
            [
                ("Submodel", submodel.id),
                ("SubmodelElementCollection", NESTED_COLLECTION),
                ("Property", "ExampleProperty"),
            ],
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_collection_ignores_children(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_COLLECTION)}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client,
            format_client.parse_object(response),
            [("Submodel", submodel.id), ("SubmodelElementCollection", NESTED_COLLECTION)],
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_capability(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'ExampleCapability')}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client,
            format_client.parse_object(response),
            [("Submodel", submodel.id), ("Capability", "ExampleCapability")],
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_operation(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'ExampleOperation')}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client,
            format_client.parse_object(response),
            [("Submodel", submodel.id), ("Operation", "ExampleOperation")],
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_list_item_uses_index_as_key(self, format_client: FormatClient):
        submodel = create_example_submodel()
        submodel.submodel_element.add(
            model.SubmodelElementList(
                "ExampleList",
                model.Property,
                [model.Property(None, model.datatypes.String, "item")],
                value_type_list_element=model.datatypes.String,
            )
        )
        self.object_store.add(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id, 'ExampleList[0]')}/$reference")

        self.assert_ok(response)
        self.assert_model_reference(
            format_client,
            format_client.parse_object(response),
            [("Submodel", submodel.id), ("SubmodelElementList", "ExampleList"), ("Property", "0")],
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_level_handling(format_client, f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$reference")

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_rejects_extent_with_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$reference?extent=WithBLOBValue"
        )

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'DoesNotExist')}/$reference")

        self.assert_error(response, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID, NESTED_PROPERTY)}/$reference")

        self.assert_error(response, 404)
