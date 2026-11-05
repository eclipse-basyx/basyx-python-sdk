# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Endpoint tests for the ``/submodels`` ``$metadata`` content modifier.

Covers:
    * ``GET /submodels/$metadata``
    * ``GET /submodels/<id>/$metadata``
    * ``GET /submodels/<id>/submodel-elements/$metadata``
    * ``GET /submodels/<id>/submodel-elements/<idShortPath>/$metadata``

``$metadata`` is only supported as JSON. XML requests must be rejected with ``406 Not Acceptable``.
"""

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


NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
UNKNOWN_SUBMODEL_ID = "https://example.org/unknown"


class MetadataEndpointTestBase(RepositoryEndpointTestBase):
    """
    Shared assertions on the query parameters of the ``$metadata`` routes.
    """

    def assert_rejects_level(self, format_client: FormatClient, path: str) -> None:
        """
        ``level`` is not applicable to ``$metadata``, thus every value must be rejected.
        """
        for level in ("deep", "core"):
            with self.subTest(level=level):
                self.assert_error(format_client.get(f"{path}?level={level}"), 400)

    def assert_extent_handling(self, format_client: FormatClient, path: str) -> None:
        """
        ``$metadata`` never contains BLOB values, thus only ``extent=WithoutBLOBValue`` is accepted.
        """
        with self.subTest(extent="WithBLOBValue"):
            self.assert_error(format_client.get(f"{path}?extent=WithBLOBValue"), 400)
        with self.subTest(extent="WithoutBLOBValue"):
            self.assert_ok(format_client.get(f"{path}?extent=WithoutBLOBValue"))


@inject_format_clients
class SubmodelsMetadataEndpointsTest(MetadataEndpointTestBase):
    """
    Endpoint tests for the ``$metadata`` modifier on the Submodel resource (``/submodels[/<id>]``).
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

    # ------------------------------------------------------------------ GET /submodels/$metadata

    @with_json_client
    def test_submodels_metadata_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$metadata")

        self.assert_ok(response)
        submodels = format_client.parse_collection(response)
        self.assertEqual(2, len(submodels))
        for submodel in submodels:
            self.assertNotIn("submodelElements", submodel)

    @with_json_client
    def test_submodels_metadata_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$metadata", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])
        for submodel in (submodel for page in pages for submodel in page):
            self.assertNotIn("submodelElements", submodel)

    @with_json_client
    def test_submodels_metadata_get_rejects_level(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_rejects_level(format_client, "/submodels/$metadata")

    @with_json_client
    def test_submodels_metadata_get_extent(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_extent_handling(format_client, "/submodels/$metadata")

    @with_xml_client
    def test_submodels_metadata_get_xml_not_acceptable(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$metadata")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$metadata

    @with_json_client
    def test_submodel_metadata_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

        self.assert_ok(response)
        submodel = format_client.parse_object(response)
        self.assertEqual(example_submodel.id, format_client.identifier(submodel))
        self.assertNotIn("submodelElements", submodel)

    @with_json_client
    def test_submodel_metadata_get_rejects_level(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_rejects_level(format_client, f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

    @with_json_client
    def test_submodel_metadata_get_extent(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_extent_handling(format_client, f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

    @with_json_client
    def test_submodel_metadata_get_not_found(self, format_client: FormatClient):
        response = format_client.get(
            f"/submodels/{base64url_encode(UNKNOWN_SUBMODEL_ID)}/$metadata"
        )

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_metadata_get_xml_not_acceptable(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

        self.assert_error(response, 406)


@inject_format_clients
class SubmodelElementsMetadataEndpointsTest(MetadataEndpointTestBase):
    """
    Endpoint tests for the ``$metadata`` modifier on the ``submodel-elements`` subtree.
    """

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    def assert_metadata_collection(self, elements: list) -> None:
        """
        Ensures the elements are serialized as Metadata, checked by the omitted ``value`` of the collection.
        """
        collections = [e for e in elements if e["modelType"] == "SubmodelElementCollection"]
        self.assertTrue(collections, "Expected a SubmodelElementCollection in the response")
        for collection in collections:
            self.assertNotIn("value", collection)

    # ------------------------------------------------------------------ GET .../submodel-elements/$metadata

    @with_json_client
    def test_submodel_elements_metadata_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$metadata")

        self.assert_ok(response)
        elements = format_client.parse_collection(response)
        self.assertEqual(len(submodel.submodel_element), len(elements))
        self.assert_metadata_collection(elements)

    @with_json_client
    def test_submodel_elements_metadata_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        limit = 3
        total = len(submodel.submodel_element)
        expected_page_sizes = [min(limit, total - start) for start in range(0, total, limit)]

        pages = format_client.get_paginated(
            f"{self.elements_path(submodel.id)}/$metadata", limit=limit, max_pages=len(expected_page_sizes)
        )

        self.assertEqual(expected_page_sizes, [len(page) for page in pages])
        self.assert_metadata_collection([element for page in pages for element in page])

    @with_json_client
    def test_submodel_elements_metadata_get_rejects_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_rejects_level(format_client, f"{self.elements_path(submodel.id)}/$metadata")

    @with_json_client
    def test_submodel_elements_metadata_get_extent(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_extent_handling(format_client, f"{self.elements_path(submodel.id)}/$metadata")

    @with_json_client
    def test_submodel_elements_metadata_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID)}/$metadata")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_elements_metadata_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$metadata")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET .../<idShortPath>/$metadata

    @with_json_client
    def test_submodel_element_metadata_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata")

        self.assert_ok(response)
        element = format_client.parse_object(response)
        self.assertEqual("ExampleProperty", format_client.field(element, "idShort"))
        # The Metadata serialization omits the value of a Property
        self.assertNotIn("value", element)

    @with_json_client
    def test_submodel_element_metadata_get_rejects_capability(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, 'ExampleCapability')}/$metadata"
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_metadata_get_rejects_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_rejects_level(format_client, f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata")

    @with_json_client
    def test_submodel_element_metadata_get_extent(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_extent_handling(format_client, f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata")

    @with_json_client
    def test_submodel_element_metadata_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'Unknown')}/$metadata")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_metadata_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path(UNKNOWN_SUBMODEL_ID, NESTED_PROPERTY)}/$metadata")

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_element_metadata_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata")

        self.assert_error(response, 406)
