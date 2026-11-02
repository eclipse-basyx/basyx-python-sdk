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
class SubmodelsReferenceEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$reference`` modifier on the Submodel resource (``/submodels[/<id>]``).
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

    # ------------------------------------------------------------------ GET /submodels/$reference

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$reference")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertEqual(2, len(references))
        self.assertEqual(
            {"https://example.org/Test_Submodel_Missing", self.SECOND_ID},
            {format_client.reference_target(ref) for ref in references},
        )

    @with_json_client
    @with_xml_client
    def test_submodels_reference_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$reference", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$reference")

        self.assert_ok(response)
        self.assertEqual(
            example_submodel.id, format_client.reference_target(format_client.parse_object(response))
        )

    @with_json_client
    @with_xml_client
    def test_submodel_reference_get_not_found(self, format_client: FormatClient):
        response = format_client.get(
            f"/submodels/{base64url_encode('https://example.org/unknown')}/$reference"
        )

        self.assert_error(response, 404)


@inject_format_clients
class SubmodelElementsReferenceEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$reference`` modifier on the ``submodel-elements`` subtree.
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

    # ------------------------------------------------------------------ GET .../submodel-elements/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$reference")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertEqual(self.TOP_LEVEL_COUNT, len(references))
        self.assertIn(
            "ExampleCapability", {format_client.reference_target(ref) for ref in references}
        )

    @with_json_client
    @with_xml_client
    def test_submodel_elements_reference_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(f"{self.elements_path(submodel.id)}/$reference", limit=3, max_pages=2)

        self.assertEqual([3, 3], [len(page) for page in pages])

    # ------------------------------------------------------------------ GET .../<idShortPath>/$reference

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/$reference")

        self.assert_ok(response)
        self.assertEqual(
            "ExampleProperty", format_client.reference_target(format_client.parse_object(response))
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_reference_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, 'DoesNotExist')}/$reference"
        )

        self.assert_error(response, 404)
