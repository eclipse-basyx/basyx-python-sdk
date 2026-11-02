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


@inject_format_clients
class SubmodelsMetadataEndpointsTest(RepositoryEndpointTestBase):
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
    @with_xml_client
    def test_submodels_metadata_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$metadata")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodels_metadata_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$metadata", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    def test_submodels_metadata_get_rejects_level(self):
        self.object_store.add(create_example_submodel())

        response = self.client.get("/submodels/$metadata?level=deep")

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$metadata

    @with_json_client
    @with_xml_client
    def test_submodel_metadata_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

        self.assert_ok(response)
        self.assertEqual(
            example_submodel.id, format_client.identifier(format_client.parse_object(response))
        )

    def test_submodel_metadata_get_omits_submodel_elements(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$metadata")

        self.assert_ok(response)
        self.assertNotIn("submodelElements", response.get_data(as_text=True))

    def test_submodel_metadata_get_rejects_level(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}/$metadata?level=core"
        )

        self.assert_error(response, 400)

    def test_submodel_metadata_get_not_found(self):
        response = self.client.get(
            f"/submodels/{base64url_encode('https://example.org/unknown')}/$metadata"
        )

        self.assert_error(response, 404)


@inject_format_clients
class SubmodelElementsMetadataEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$metadata`` modifier on the ``submodel-elements`` subtree.
    """

    #: Number of top-level submodel elements in ``create_example_submodel()``.
    TOP_LEVEL_COUNT = 6

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    # ------------------------------------------------------------------ GET .../submodel-elements/$metadata

    @with_json_client
    @with_xml_client
    def test_submodel_elements_metadata_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$metadata")

        self.assert_ok(response)
        self.assertEqual(self.TOP_LEVEL_COUNT, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_metadata_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(f"{self.elements_path(submodel.id)}/$metadata", limit=3, max_pages=2)

        self.assertEqual([3, 3], [len(page) for page in pages])

    def test_submodel_elements_metadata_get_rejects_level(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id)}/$metadata?level=deep")

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ GET .../<idShortPath>/$metadata

    @with_json_client
    @with_xml_client
    def test_submodel_element_metadata_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata")

        self.assert_ok(response)
        self.assertEqual(
            "ExampleProperty", format_client.field(format_client.parse_object(response), "idShort")
        )

    def test_submodel_element_metadata_get_rejects_capability(self):
        submodel = self.add_example_submodel()

        response = self.client.get(
            f"{self.elements_path(submodel.id, 'ExampleCapability')}/$metadata"
        )

        self.assert_error(response, 400)

    def test_submodel_element_metadata_get_rejects_level(self):
        submodel = self.add_example_submodel()

        response = self.client.get(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$metadata?level=core"
        )

        self.assert_error(response, 400)
