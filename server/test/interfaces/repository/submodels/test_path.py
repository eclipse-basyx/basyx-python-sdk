# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Endpoint tests for the ``/submodels`` ``$path`` content modifier.

Covers:
    * ``GET /submodels/$path``
    * ``GET /submodels/<id>/$path``
    * ``GET /submodels/<id>/submodel-elements/$path``
    * ``GET /submodels/<id>/submodel-elements/<idShortPath>/$path``

The structural correctness of the idShortPath output is covered by the SDK's :class:`PathJsonEncoder`
unit tests and is not re-asserted here.
"""

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.examples.data import example_aas
from basyx.aas.examples.data.example_aas import create_example_bill_of_material_submodel
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ...format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from ..helpers import RepositoryEndpointTestBase

NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_LIST = "ExampleSubmodelCollection.ExampleSubmodelList"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
NESTED_RANGE = "ExampleSubmodelCollection.ExampleRange"
NESTED_ANNOTATED_REL = "ExampleAnnotatedRelationshipElement"


@inject_format_clients
class SubmodelsPathEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$path`` modifier on the Submodel resource (``/submodels[/<id>]``).

    ``$path`` serialization is JSON-only; XML variants are added only where the server must respond
    with ``406 Not Acceptable``.
    """

    # 14 idShortPaths of the example submodel + 4 of the bill of material submodel
    TWO_SUBMODELS_PATH_COUNT = 18

    def two_submodels_store(self) -> model.DictIdentifiableStore:
        store: model.DictIdentifiableStore = model.DictIdentifiableStore()
        store.add(create_example_submodel())
        store.add(create_example_bill_of_material_submodel())
        return store

    # ------------------------------------------------------------------ GET /submodels/$path

    @with_json_client
    def test_submodels_path_get(self, format_client: FormatClient):
        """``result`` is a flat list of idShortPath strings of all Submodels (``GetPathItemsResult``)."""
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels/$path")

        self.assert_ok(response)
        paths = format_client.parse_collection(response)
        self.assertEqual(self.TWO_SUBMODELS_PATH_COUNT, len(paths))
        for path in paths:
            self.assertIsInstance(path, str)
        self.assertIn("ExampleSubmodelCollection.ExampleBlob", paths)
        self.assertIn("ExampleEntity.ExampleProperty", paths)

    @with_json_client
    def test_submodels_path_get_supports_pagination(self, format_client: FormatClient):
        """``limit`` counts idShortPath strings, not Submodels."""
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels/$path", limit=5, max_pages=4)

        self.assertEqual([5, 5, 5, 3], [len(page) for page in pages])
        for page in pages:
            for path in page:
                self.assertIsInstance(path, str)

    def test_submodels_path_get_rejects_invalid_level(self):
        self.object_store.add(create_example_submodel())

        response = self.client.get("/submodels/$path?level=bogus")

        self.assert_error(response, 400)

    def test_submodels_path_get_rejects_extent(self):
        self.object_store.add(create_example_submodel())

        response = self.client.get("/submodels/$path?extent=withBlobValue")

        self.assert_error(response, 400)

    @with_xml_client
    def test_submodels_path_get_xml_not_acceptable(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        response = format_client.get("/submodels/$path")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>/$path

    @with_json_client
    def test_submodel_path_get(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$path")

        self.assert_ok(response)
        paths = format_client.parse_object(response)
        self.assertIsInstance(paths, list)
        self.assertGreater(len(paths), 0)

    @with_json_client
    def test_submodel_path_get_level_core_is_shallower_than_deep(self, format_client: FormatClient):
        """The ``level`` modifier is propagated to the encoder: core returns strictly fewer paths than deep."""
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)
        base = f"/submodels/{base64url_encode(example_submodel.id)}/$path"

        deep = format_client.parse_object(format_client.get(base))
        core = format_client.parse_object(format_client.get(f"{base}?level=core"))

        self.assertLess(len(core), len(deep))

    def test_submodel_path_get_rejects_invalid_level(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}/$path?level=bogus"
        )

        self.assert_error(response, 400)

    def test_submodel_path_get_rejects_extent(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}/$path?extent=withBlobValue"
        )

        self.assert_error(response, 400)

    def test_submodel_path_get_not_found(self):
        response = self.client.get(
            f"/submodels/{base64url_encode('https://example.org/unknown')}/$path"
        )

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_path_get_xml_not_acceptable(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}/$path")

        self.assert_error(response, 406)


@inject_format_clients
class SubmodelElementsPathEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``$path`` modifier on the ``submodel-elements`` subtree.
    """

    # 6 top-level elements + 2 annotations + 6 collection children of the example submodel
    EXAMPLE_SUBMODEL_PATH_COUNT = 14

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    def add_bill_of_material_submodel(self) -> model.Submodel:
        submodel = create_example_bill_of_material_submodel()
        self.object_store.add(submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    # ------------------------------------------------------------------ GET .../submodel-elements/$path

    @with_json_client
    def test_submodel_elements_path_get(self, format_client: FormatClient):
        """``result`` is a flat list of idShortPath strings (``GetPathItemsResult``)."""
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$path")

        self.assert_ok(response)
        paths = format_client.parse_collection(response)
        self.assertEqual(self.EXAMPLE_SUBMODEL_PATH_COUNT, len(paths))
        for path in paths:
            self.assertIsInstance(path, str)
        self.assertIn(NESTED_COLLECTION, paths)
        self.assertIn(NESTED_PROPERTY, paths)

    @with_json_client
    def test_submodel_elements_path_get_supports_pagination(self, format_client: FormatClient):
        """``limit`` counts idShortPath strings, not top-level SubmodelElements."""
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(f"{self.elements_path(submodel.id)}/$path", limit=3, max_pages=5)

        self.assertEqual([3, 3, 3, 3, 2], [len(page) for page in pages])

    def test_submodel_elements_path_get_rejects_invalid_level(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id)}/$path?level=bogus")

        self.assert_error(response, 400)

    def test_submodel_elements_path_get_rejects_extent(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id)}/$path?extent=withBlobValue")

        self.assert_error(response, 400)

    @with_xml_client
    def test_submodel_elements_path_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}/$path")

        self.assert_error(response, 406)

    # ------------------------------------------------------------------ GET .../<idShortPath>/$path

    @with_json_client
    def test_submodel_element_path_get_collection(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_COLLECTION)}/$path")

        self.assert_ok(response)
        paths = format_client.parse_object(response)
        self.assertIsInstance(paths, list)
        self.assertIn(NESTED_COLLECTION, paths)

    @with_json_client
    def test_submodel_element_path_get_list_uses_index_notation(self, format_client: FormatClient):
        """
        SML children are addressed by ``[<index>]``. Every idShortPath starts with the idShort of the requested
        element, not with the top-level element of the Submodel (IDTA-01001, Format "Path").
        """
        # Only the full example submodel contains a SubmodelElementList
        submodel = example_aas.create_example_submodel()
        self.object_store.add(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_LIST)}/$path")

        self.assert_ok(response)
        paths = format_client.parse_object(response)
        self.assertEqual(["ExampleSubmodelList", "ExampleSubmodelList[0]", "ExampleSubmodelList[1]"], paths)

    @with_json_client
    def test_submodel_element_path_get_entity(self, format_client: FormatClient):
        submodel = self.add_bill_of_material_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'ExampleEntity')}/$path")

        self.assert_ok(response)
        paths = format_client.parse_object(response)
        self.assertIsInstance(paths, list)
        self.assertIn("ExampleEntity", paths)

    @with_json_client
    def test_submodel_element_path_get_annotated_relationship_element(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_ANNOTATED_REL)}/$path")

        self.assert_ok(response)
        paths = format_client.parse_object(response)
        self.assertIsInstance(paths, list)
        self.assertIn(NESTED_ANNOTATED_REL, paths)

    def test_submodel_element_path_get_rejects_unsupported_types(self):
        """
        $path is defined for Submodel, SubmodelElementCollection, SubmodelElementList, Entity and
        AnnotatedRelationshipElement only. Every other SubmodelElement subtype must
        be rejected by the server with ``400 Bad Request``.
        """
        submodel = self.add_example_submodel()

        for id_short_path in (NESTED_PROPERTY, NESTED_RANGE, "ExampleOperation", "ExampleBasicEventElement"):
            with self.subTest(id_short_path=id_short_path):
                response = self.client.get(f"{self.elements_path(submodel.id, id_short_path)}/$path")
                self.assert_error(response, 400)

    def test_submodel_element_path_get_not_found(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id, 'Unknown')}/$path")

        self.assert_error(response, 404)

    def test_submodel_element_path_get_submodel_not_found(self):
        response = self.client.get(
            f"{self.elements_path('https://example.org/unknown', NESTED_COLLECTION)}/$path"
        )

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_element_path_get_xml_not_acceptable(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_COLLECTION)}/$path")

        self.assert_error(response, 406)
