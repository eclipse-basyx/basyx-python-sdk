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
from typing import cast

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ...format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from ..helpers import RepositoryEndpointTestBase

# idShorts of top-level submodel elements of ``create_example_submodel()`` without a ValueOnly
# representation: they must not appear in a ``$value`` response.
VALUE_LESS_ID_SHORTS = ("ExampleOperation", "ExampleCapability")

NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
NESTED_BLOB = "ExampleSubmodelCollection.ExampleBlob"
UNKNOWN_SUBMODEL_ID = "https://example.org/unknown"


class ValueEndpointTestBase(RepositoryEndpointTestBase):
    """
    Shared assertions on the query parameters of the ``$value`` routes.
    """

    def assert_rejects_invalid_level(self, format_client: FormatClient, path: str) -> None:
        """
        ``level`` accepts ``deep`` and ``core`` any other value must be rejected with 400.
        """
        response = format_client.get(f"{path}?level=bogus")
        self.assert_error(response, 400)

    def assert_level_handling(self, format_client: FormatClient, path: str) -> None:
        """
        Both ``level=deep`` (default) and ``level=core`` must be accepted
        """
        with self.subTest(level="deep"):
            self.assert_ok(format_client.get(f"{path}?level=deep"))
        with self.subTest(level="core"):
            self.assert_ok(format_client.get(f"{path}?level=core"))


@inject_format_clients
class SubmodelsValueEndpointsTest(ValueEndpointTestBase):
    """
    Endpoint tests for the ``$value`` modifier on the Submodel resource (``/submodels[/<id>]``).
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
        submodels = format_client.parse_collection(response)
        self.assertEqual(2, len(submodels))
        # Spot-check ValueOnly shape: each item is a mapping, and elements that lack a ValueOnly
        # representation (Operation, Capability) are omitted.
        for submodel in submodels:
            self.assertIsInstance(submodel, dict)
            for id_short in VALUE_LESS_ID_SHORTS:
                self.assertNotIn(id_short, submodel)

    @with_json_client
    def test_submodels_value_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$value", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    @with_json_client
    def test_submodels_value_get_level_handling(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_level_handling(format_client, "/submodels/$value")

    @with_json_client
    def test_submodels_value_get_rejects_invalid_level(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_rejects_invalid_level(format_client, "/submodels/$value")

    @with_xml_client
    def test_submodels_value_get_xml_not_acceptable(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        response = format_client.get("/submodels/$value")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$value

    @with_json_client
    def test_submodel_value_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value")

        self.assert_ok(response)
        # Spot-check: body is a mapping, with elements that lack a ValueOnly representation
        # (Operation, Capability) omitted.
        value = format_client.parse_object(response)
        self.assertIsInstance(value, dict)
        for id_short in VALUE_LESS_ID_SHORTS:
            self.assertNotIn(id_short, value)

    @with_json_client
    def test_submodel_value_get_level_handling(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_level_handling(format_client, f"/submodels/{base64url_encode(example_submodel.id)}/$value")

    @with_json_client
    def test_submodel_value_get_rejects_invalid_level(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_rejects_invalid_level(
            format_client, f"/submodels/{base64url_encode(example_submodel.id)}/$value"
        )

    @with_json_client
    def test_submodel_value_get_extent_toggles_blob_value(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)
        path = f"/submodels/{base64url_encode(example_submodel.id)}/$value"

        self.assert_extent_toggles_blob_value(
            format_client, path, locate_blob=lambda body: body[NESTED_COLLECTION]["ExampleBlob"]
        )

    @with_json_client
    def test_submodel_value_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"/submodels/{base64url_encode(UNKNOWN_SUBMODEL_ID)}/$value")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_value_get_xml_not_acceptable(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$value")

        self.assert_error(response, 406)


@inject_format_clients
class SubmodelElementsValueEndpointsTest(ValueEndpointTestBase):
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

    # ------------------------------------------------------------------ GET .../submodel-elements/$value

    # TODO: Determine list behaviour
    @with_json_client
    def test_submodel_elements_value_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$value")

        self.assert_ok(response)
        # Spot-check: elements that lack a ValueOnly representation (Operation, Capability) are
        # omitted from the collection response.
        values = format_client.parse_collection(response)
        emitted = {id_short for value in values for id_short in value}
        for id_short in VALUE_LESS_ID_SHORTS:
            self.assertNotIn(id_short, emitted)

    # TODO: Determine list behaviour
    @with_json_client
    def test_submodel_elements_value_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(f"{self.elements_path(submodel.id)}/$value", limit=3, max_pages=2)

        # Value-less elements are omitted from every page.
        emitted = {id_short for page in pages for value in page for id_short in value}
        for id_short in VALUE_LESS_ID_SHORTS:
            self.assertNotIn(id_short, emitted)

    @with_json_client
    def test_submodel_elements_value_get_level_handling(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_level_handling(format_client, f"{self.elements_path(submodel.id)}/$value")

    @with_json_client
    def test_submodel_elements_value_get_rejects_invalid_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_rejects_invalid_level(format_client, f"{self.elements_path(submodel.id)}/$value")

    @with_json_client
    def test_submodel_elements_value_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID)}/$value")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_elements_value_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$value")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET .../<idShortPath>/$value

    @with_json_client
    def test_submodel_element_value_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$value")

        self.assert_ok(response)
        # Spot-check: a Property's ValueOnly representation is the raw value (not a wrapping object).
        self.assertEqual("exampleValue", format_client.parse_object(response))

    @with_json_client
    def test_submodel_element_value_get_none(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        cast(model.Property, submodel.get_referable(NESTED_PROPERTY)).value = None
        self.object_store.commit(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$value")
        self.assert_ok(response)
        self.assertIsNone(format_client.parse_object(response))

    def test_submodel_element_value_get_rejects_unsupported_types(self):
        """
        ValueOnly is not defined for Operation and Capability so the server
        needs to reject both with ``400``.
        """
        submodel = self.add_example_submodel()

        for id_short in ("ExampleOperation", "ExampleCapability"):
            with self.subTest(id_short=id_short):
                response = self.client.get(f"{self.elements_path(submodel.id, id_short)}/$value")
                self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_value_get_level_handling(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_level_handling(
            format_client, f"{self.elements_path(submodel.id, NESTED_COLLECTION)}/$value"
        )

    @with_json_client
    def test_submodel_element_value_get_rejects_invalid_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_rejects_invalid_level(
            format_client, f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$value"
        )

    @with_json_client
    def test_submodel_element_value_get_blob_extent_toggles_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        path = f"{self.elements_path(submodel.id, NESTED_BLOB)}/$value"

        self.assert_extent_toggles_blob_value(format_client, path, locate_blob=lambda body: body)

    @with_json_client
    def test_submodel_element_value_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'Unknown')}/$value")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_value_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID, NESTED_PROPERTY)}/$value")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_element_value_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$value")

        self.assert_error(response, 406)
