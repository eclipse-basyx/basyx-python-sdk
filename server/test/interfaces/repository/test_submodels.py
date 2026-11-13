# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import io
import json
from unittest import mock

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.examples.data import example_aas
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ..format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from .helpers import RepositoryEndpointTestBase

# ExampleSubmodelCollection (a nested namespace) and one of its children, carried by
# ``create_example_submodel()``; used as ready-made id_short paths in the tests below.
NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
NESTED_BLOB = "ExampleSubmodelCollection.ExampleBlob"
NESTED_FILE = "ExampleSubmodelCollection.ExampleFile"
# SubmodelElementList inside ExampleSubmodelCollection, only carried by ``example_aas.create_example_submodel()``.
NESTED_LIST_ID_SHORT = "ExampleSubmodelList"
EXAMPLE_QUALIFIER_TYPE = "http://example.org/Qualifier/ExampleQualifier"


def _child(elements: list, id_short: str) -> dict:
    """Returns the element with the given idShort from a list of SubmodelElements in JSON format."""
    return next(element for element in elements if element["idShort"] == id_short)


def _example_blob(submodel_elements: list) -> dict:
    """Returns ``ExampleSubmodelCollection.ExampleBlob`` from the SubmodelElements of ``create_example_submodel()``."""
    return _child(_child(submodel_elements, NESTED_COLLECTION)["value"], "ExampleBlob")


def _encode_reference(reference: model.Reference) -> str:
    return base64url_encode(json.dumps(reference, cls=AASToJsonEncoder))


# semanticId carried by ``create_example_submodel()``.
EXAMPLE_SEMANTIC_ID = model.ExternalReference(
    (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "http://example.org/SubmodelTemplates/ExampleSubmodel"),)
)


@inject_format_clients
class SubmodelsEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the implemented ``/submodels`` routes of :class:`~app.interfaces.repository.WSGIApp`
    that operate on the Submodel itself (the ``/submodel-elements`` subtree is covered separately).

    Bodies are written once against the format-agnostic ``format_client`` helper.
    For each test two variants are generated where the :class:`~..format_utils.JsonFormatClient` and
    :class:`~..format_utils.XmlFormatClient` are injected respectively.
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

    def _get_submodel_ids(self, format_client: FormatClient, query: str) -> set:
        response = format_client.get(f"/submodels?{query}&extent=WithBLOBValue")
        self.assert_ok(response)
        return {format_client.identifier(node) for node in format_client.parse_collection(response)}

    # ------------------------------------------------------------------ GET /submodels

    @with_json_client
    @with_xml_client
    def test_submodels_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodels_get_empty(self, format_client: FormatClient):
        response = format_client.get("/submodels?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(0, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodels_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels?extent=WithBLOBValue", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    @with_json_client
    def test_submodels_get_extent_toggles_blob_value(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_extent_toggles_blob_value(
            format_client, "/submodels", locate_blob=lambda body: _example_blob(body["result"][0]["submodelElements"])
        )

    @with_xml_client
    def test_submodels_get_xml_requires_blob_value(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())

        self.assert_xml_requires_blob_value(format_client, "/submodels")

    @with_xml_client
    def test_submodels_get_xml_rejects_level_core(self, format_client: FormatClient):
        response = format_client.get("/submodels?level=core")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodels_get_level_core(self, format_client: FormatClient):
        """
        ``level=core`` keeps the direct children of each Submodel but omits their children.
        """
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels?level=core")

        self.assert_ok(response)
        submodels = format_client.parse_collection(response)
        self.assertEqual(2, len(submodels))
        for submodel in submodels:
            self.assertNotIn("value", _child(submodel["submodelElements"], NESTED_COLLECTION))

    @with_json_client
    def test_submodels_get_rejects_limit_below_one(self, format_client: FormatClient):
        """
        ``limit=0`` would return an empty page whose cursor points to the same start, so ``limit`` must be positive.
        """
        self.object_store.update(self.two_submodels_store())

        for limit in (0, -1):
            with self.subTest(limit=limit):
                self.assert_error(format_client.get(f"/submodels?limit={limit}"), 400)

    # ------------------------------------------------------------------ GET /submodels?idShort=...&semanticId=...

    @with_json_client
    @with_xml_client
    def test_submodels_get_filter_by_id_short(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        ids = self._get_submodel_ids(format_client, "idShort=SecondSubmodel")

        self.assertEqual({self.SECOND_ID}, ids)

    @with_json_client
    @with_xml_client
    def test_submodels_get_filter_by_id_short_no_match(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        ids = self._get_submodel_ids(format_client, "idShort=Unknown")

        self.assertEqual(set(), ids)

    @with_json_client
    @with_xml_client
    def test_submodels_get_filter_by_semantic_id(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        ids = self._get_submodel_ids(format_client, f"semanticId={_encode_reference(EXAMPLE_SEMANTIC_ID)}")

        self.assertEqual({"https://example.org/Test_Submodel_Missing", self.SECOND_ID}, ids)

    @with_json_client
    @with_xml_client
    def test_submodels_get_filter_by_semantic_id_no_match(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())
        other = model.ExternalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "https://example.org/other"),))

        ids = self._get_submodel_ids(format_client, f"semanticId={_encode_reference(other)}")

        self.assertEqual(set(), ids)

    # ------------------------------------------------------------------ POST /submodels

    @with_json_client
    @with_xml_client
    def test_submodels_post_success(self, format_client: FormatClient):
        example_submodel = create_example_submodel()

        response = format_client.post("/submodels", obj=example_submodel)

        self.assertEqual(201, response.status_code)
        self.assertIsNotNone(self.object_store.get(example_submodel.id, None))

    @with_json_client
    @with_xml_client
    def test_submodels_post_bad(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        example_submodel.id = None  # type: ignore

        response = format_client.post("/submodels", obj=example_submodel)

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_submodels_post_conflict(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.post("/submodels", obj=example_submodel)

        self.assert_error(response, 409)

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>

    @with_json_client
    @with_xml_client
    def test_submodel_get_success(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(example_submodel.id, format_client.identifier(format_client.parse_object(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_get_not_found(self, format_client: FormatClient):
        response = format_client.get(
            f"/submodels/{base64url_encode('https://example.org/unknown')}?extent=WithBLOBValue"
        )

        self.assert_error(response, 404)

    @with_xml_client
    def test_submodel_get_not_found_xml_without_extent_returns_406(self, format_client: FormatClient):
        """
        The modifiers are checked before the Submodel is looked up, so clients learn that XML without BLOB values is
        not supported, even if the Submodel doesn't exist.
        """
        response = format_client.get(f"/submodels/{base64url_encode('https://example.org/unknown')}")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodel_get_extent_toggles_blob_value(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_extent_toggles_blob_value(
            format_client,
            f"/submodels/{base64url_encode(example_submodel.id)}",
            locate_blob=lambda body: _example_blob(body["submodelElements"]),
        )

    @with_xml_client
    def test_submodel_get_xml_requires_blob_value(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        self.assert_xml_requires_blob_value(format_client, f"/submodels/{base64url_encode(example_submodel.id)}")

    @with_xml_client
    def test_submodel_get_xml_rejects_level_core(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}?level=core")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodel_get_level_core(self, format_client: FormatClient):
        """
        ``level=core`` keeps the direct children of the Submodel but omits their children.
        """
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}?level=core")

        self.assert_ok(response)
        submodel_elements = format_client.parse_object(response)["submodelElements"]
        self.assertEqual(len(example_submodel.submodel_element), len(submodel_elements))
        self.assertNotIn("value", _child(submodel_elements, NESTED_COLLECTION))

    @with_json_client
    def test_submodel_get_invalid_level_returns_400(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}?level=bogus")

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ PUT /submodels/<submodel_id>

    @with_json_client
    @with_xml_client
    def test_submodel_put_success(self, format_client: FormatClient):
        self.object_store.add(create_example_submodel())
        updated_submodel = create_example_submodel()
        updated_submodel.id_short = "UpdatedIdShort"

        response = format_client.put(
            f"/submodels/{base64url_encode(updated_submodel.id)}", obj=updated_submodel
        )

        self.assertEqual(204, response.status_code)
        retrieved_submodel = self.object_store.get(updated_submodel.id, None)
        self.assertIsInstance(retrieved_submodel, model.Submodel)
        assert isinstance(retrieved_submodel, model.Submodel)  # make mypy happy
        self.assertEqual("UpdatedIdShort", retrieved_submodel.id_short)

    @with_json_client
    @with_xml_client
    def test_submodel_put_not_found(self, format_client: FormatClient):
        updated_submodel = create_example_submodel()

        response = format_client.put(
            f"/submodels/{base64url_encode('https://example.org/unknown')}", obj=updated_submodel
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ DELETE /submodels/<submodel_id>

    @with_json_client
    @with_xml_client
    def test_submodel_delete_success(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.delete(f"/submodels/{base64url_encode(example_submodel.id)}")

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self.object_store.get(example_submodel.id, None))

    @with_json_client
    @with_xml_client
    def test_submodel_delete_not_found(self, format_client: FormatClient):
        response = format_client.delete(f"/submodels/{base64url_encode('https://example.org/unknown')}")

        self.assert_error(response, 404)


@inject_format_clients
class SubmodelElementsEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the ``/submodels/<id>/submodel-elements`` subtree of
    :class:`~app.interfaces.repository.WSGIApp`, including the ``$metadata`` / ``$reference`` modifiers,
    the ``attachment`` file routes and the ``qualifiers`` routes.

    Bodies are written once against the format-agnostic ``format_client`` helper.
    For each test two variants are generated where the :class:`~..format_utils.JsonFormatClient` and
    :class:`~..format_utils.XmlFormatClient` are injected respectively.
    """

    #: Number of top-level submodel elements in ``create_example_submodel()``.
    TOP_LEVEL_COUNT = 6

    def add_example_submodel(self) -> model.Submodel:
        submodel = create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    def add_full_example_submodel(self) -> model.Submodel:
        """
        Adds the full example submodel, which nests a SubmodelElementList inside ``ExampleSubmodelCollection``.
        """
        submodel = example_aas.create_example_submodel()
        self.object_store.add(submodel)
        return submodel

    def _stored_submodel(self, submodel_id: str) -> model.Submodel:
        submodel = self.object_store.get(submodel_id)
        assert isinstance(submodel, model.Submodel)
        return submodel

    @staticmethod
    def elements_path(submodel_id: str, id_short_path: str = "") -> str:
        base = f"/submodels/{base64url_encode(submodel_id)}/submodel-elements"
        return f"{base}/{id_short_path}" if id_short_path else base

    def _nested_element(self, submodel: model.Submodel, id_short_path: str) -> model.SubmodelElement:
        referable: model.Referable = submodel
        for id_short in id_short_path.split("."):
            assert isinstance(referable, model.UniqueIdShortNamespace)
            referable = referable.get_referable(id_short)
        assert isinstance(referable, model.SubmodelElement)
        return referable

    def _nested_property(self, submodel: model.Submodel, id_short_path: str) -> model.Property:
        element = self._nested_element(submodel, id_short_path)
        assert isinstance(element, model.Property)
        return element

    def _nested_file(self, submodel: model.Submodel, id_short_path: str) -> model.File:
        element = self._nested_element(submodel, id_short_path)
        assert isinstance(element, model.File)
        return element

    def _nested_blob(self, submodel: model.Submodel, id_short_path: str) -> model.Blob:
        element = self._nested_element(submodel, id_short_path)
        assert isinstance(element, model.Blob)
        return element

    # ------------------------------------------------------------------ GET .../submodel-elements

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(self.TOP_LEVEL_COUNT, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_pagination_limit(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}?limit=2&extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(
            f"{self.elements_path(submodel.id)}?extent=WithBLOBValue", limit=3, max_pages=2
        )

        self.assertEqual([3, 3], [len(page) for page in pages])

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(f"{self.elements_path('https://example.org/unknown')}?extent=WithBLOBValue")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_elements_get_extent_toggles_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_extent_toggles_blob_value(
            format_client, self.elements_path(submodel.id), locate_blob=lambda body: _example_blob(body["result"])
        )

    @with_xml_client
    def test_submodel_elements_get_xml_requires_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_xml_requires_blob_value(format_client, self.elements_path(submodel.id))

    @with_xml_client
    def test_submodel_elements_get_xml_rejects_level_core(self, format_client: FormatClient):
        submodel = self.add_full_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}?level=core")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodel_elements_get_level_core(self, format_client: FormatClient):
        """
        ``level=core`` keeps the direct children of each SubmodelElement but omits their children.
        """
        submodel = self.add_full_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}?level=core")

        self.assert_ok(response)
        collection = _child(format_client.parse_collection(response), NESTED_COLLECTION)
        self.assertIn("value", collection)
        self.assertNotIn("value", _child(collection["value"], NESTED_LIST_ID_SHORT))

    # ------------------------------------------------------------------ POST .../submodel-elements

    @with_json_client
    @with_xml_client
    def test_submodel_elements_post_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        new_element = model.Property("NewProperty", model.datatypes.String, "some-value")

        response = format_client.post(self.elements_path(submodel.id), obj=new_element)

        self.assertEqual(201, response.status_code)
        self.assertIn("Location", response.headers)
        retrieved = self._stored_submodel(submodel.id)
        self.assertIsInstance(retrieved.get_referable("NewProperty"), model.Property)

    @with_json_client
    @with_xml_client
    def test_submodel_elements_post_conflict(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        duplicate = model.Property("ExampleCapability", model.datatypes.String, "v")

        response = format_client.post(self.elements_path(submodel.id), obj=duplicate)

        self.assert_error(response, 409)

    @with_json_client
    @with_xml_client
    def test_submodel_elements_post_submodel_not_found(self, format_client: FormatClient):
        new_element = model.Property("NewProperty", model.datatypes.String, "v")

        response = format_client.post(
            self.elements_path("https://example.org/unknown"), obj=new_element
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ GET .../submodel-elements/<idShortPath>

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_top_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'ExampleCapability')}?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(
            "ExampleCapability", format_client.field(format_client.parse_object(response), "idShort")
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_nested(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}?extent=WithBLOBValue")

        self.assert_ok(response)
        self.assertEqual(
            "ExampleProperty", format_client.field(format_client.parse_object(response), "idShort")
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, 'DoesNotExist')}?extent=WithBLOBValue")

        self.assert_error(response, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_nested_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, f'{NESTED_COLLECTION}.DoesNotExist')}?extent=WithBLOBValue"
        )

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_get_extent_toggles_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_extent_toggles_blob_value(
            format_client, self.elements_path(submodel.id, NESTED_BLOB), locate_blob=lambda body: body
        )

    @with_xml_client
    def test_submodel_element_get_xml_requires_blob_value(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        self.assert_xml_requires_blob_value(format_client, self.elements_path(submodel.id, NESTED_COLLECTION))

    @with_xml_client
    def test_submodel_element_get_xml_rejects_level_core(self, format_client: FormatClient):
        submodel = self.add_full_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_COLLECTION)}?level=core")

        self.assert_error(response, 406)

    @with_json_client
    def test_submodel_element_get_level_core(self, format_client: FormatClient):
        """
        ``level=core`` keeps the direct children of the requested SubmodelElement but omits their children.
        """
        submodel = self.add_full_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_COLLECTION)}?level=core")

        self.assert_ok(response)
        collection = format_client.parse_object(response)
        self.assertIn("value", collection)
        self.assertNotIn("value", _child(collection["value"], NESTED_LIST_ID_SHORT))

    @with_json_client
    def test_submodel_element_get_path_through_non_namespace_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id, f"{NESTED_PROPERTY}.Child"))

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_get_malformed_id_short_path_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id, "a..b"))

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ POST .../submodel-elements/<idShortPath>

    @with_json_client
    @with_xml_client
    def test_submodel_element_post_child_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        new_element = model.Property("AddedChild", model.datatypes.String, "v")

        response = format_client.post(
            self.elements_path(submodel.id, NESTED_COLLECTION), obj=new_element
        )

        self.assertEqual(201, response.status_code)
        retrieved = self._stored_submodel(submodel.id)
        self.assertIsInstance(
            self._nested_element(retrieved, f"{NESTED_COLLECTION}.AddedChild"), model.Property
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_post_child_conflict(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        duplicate = model.Property("ExampleProperty", model.datatypes.String, "v")

        response = format_client.post(
            self.elements_path(submodel.id, NESTED_COLLECTION), obj=duplicate
        )

        self.assert_error(response, 409)

    @with_json_client
    @with_xml_client
    def test_submodel_element_post_into_list_location_uses_index(self, format_client: FormatClient):
        """
        Elements of a SubmodelElementList are addressed by their index. The internal idShort the SDK generates for
        list elements without an idShort must not leak into the ``Location`` header.
        """
        sml = model.SubmodelElementList(
            "ExampleList",
            model.Property,
            value_type_list_element=model.datatypes.String,
            value=[model.Property(None, model.datatypes.String, "existing")],
        )
        submodel = model.Submodel("https://example.org/Test_Submodel_List", submodel_element=[sml])
        self.object_store.add(submodel)
        new_element = model.Property(None, model.datatypes.String, "added")

        response = format_client.post(self.elements_path(submodel.id, "ExampleList"), obj=new_element)

        self.assertEqual(201, response.status_code)
        self.assertNotIn(model.SubmodelElementList.GENERATED_ID_SHORT_PREFIX, response.headers["Location"])
        created = format_client.get(f"{response.headers['Location']}?extent=WithBLOBValue")
        self.assert_ok(created)
        self.assertEqual("added", format_client.field(format_client.parse_object(created), "value"))

    @with_json_client
    def test_submodel_element_post_into_non_namespace_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        payload = json.dumps(
            model.Property("Child", model.datatypes.String, "v"), cls=AASToJsonEncoder
        )

        response = format_client.post(
            self.elements_path(submodel.id, NESTED_PROPERTY),
            data=payload,
            content_type="application/json",
        )

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ PUT .../submodel-elements/<idShortPath>

    @with_json_client
    @with_xml_client
    def test_submodel_element_put_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        updated = model.Property("ExampleProperty", model.datatypes.String, "updated-value")

        response = format_client.put(
            self.elements_path(submodel.id, NESTED_PROPERTY), obj=updated
        )

        self.assertEqual(204, response.status_code)
        retrieved = self._nested_property(self._stored_submodel(submodel.id), NESTED_PROPERTY)
        self.assertEqual("updated-value", retrieved.value)

    @with_json_client
    @with_xml_client
    def test_submodel_element_put_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        updated = model.Property("DoesNotExist", model.datatypes.String, "v")

        response = format_client.put(
            self.elements_path(submodel.id, "DoesNotExist"), obj=updated
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ DELETE .../submodel-elements/<idShortPath>

    @with_json_client
    @with_xml_client
    def test_submodel_element_delete_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(self.elements_path(submodel.id, NESTED_PROPERTY))

        self.assertEqual(204, response.status_code)
        follow_up = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}?extent=WithBLOBValue")
        self.assert_error(follow_up, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_delete_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(self.elements_path(submodel.id, "DoesNotExist"))

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ .../<idShortPath>/attachment

    @with_json_client
    def test_submodel_element_attachment_get_blob(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/pdf", response.mimetype)
        self.assertEqual(bytes([1, 2, 3, 4, 5]), response.get_data())

    @with_json_client
    def test_submodel_element_attachment_get_file(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"
        self._nested_file(submodel, NESTED_FILE).content_type = "application/pdf"

        self.file_store.write_file.side_effect = lambda name, stream: stream.write(b"file-content")

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/pdf", response.content_type)
        self.file_store.write_file.assert_any_call("/TestFile.pdf", mock.ANY)
        self.assertEqual(b"file-content", response.data)

    @with_json_client
    def test_submodel_element_attachment_get_on_non_file_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment")

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_get_file_without_value_returns_404(self, format_client: FormatClient):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None
        self.object_store.add(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_attachment_get_external_file_return_400(self, format_client: FormatClient):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "C:\\Users\\Test\\File.pdf"
        self.object_store.add(submodel)

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_get_missing_file_return_404(self, format_client: FormatClient):
        submodel = create_example_submodel()
        self.object_store.add(submodel)

        self.file_store.write_file.side_effect = KeyError
        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_attachment_put_success(self, format_client: FormatClient):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None
        self.object_store.add(submodel)
        self.file_store.add_file.return_value = "/uploaded.pdf"

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={
                "fileName": "/uploaded.pdf",
                "file": (io.BytesIO(b"pdf-bytes"), "uploaded.pdf", "application/pdf"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(204, response.status_code)
        self.file_store.add_file.assert_called_once_with("/uploaded.pdf", mock.ANY, "application/pdf")
        self.assertEqual(
            "/uploaded.pdf", self._nested_file(self._stored_submodel(submodel.id), NESTED_FILE).value
        )

    @with_json_client
    def test_submodel_element_attachment_put_conflict_when_value_present(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={
                "fileName": "/uploaded.pdf",
                "file": (io.BytesIO(b"pdf-bytes"), "uploaded.pdf", "application/pdf"),
            },
            content_type="multipart/form-data",
        )

        self.assert_error(response, 409)

    @with_json_client
    def test_submodel_element_attachment_put_on_non_file_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment",
            data={"fileName": "/x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_put_missing_filename_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_put_external_filename_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "C:\\Users\\Test\\x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_put_missing_file_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "/x.pdf"},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_put_mimetype_mismatch_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "/x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/xml")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 415)

    @with_json_client
    def test_submodel_element_attachment_delete_blob(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment")

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self._nested_blob(self._stored_submodel(submodel.id), NESTED_BLOB).value)

    @with_json_client
    def test_submodel_element_attachment_delete_file(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"

        response = format_client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(204, response.status_code)
        self.file_store.delete_file.assert_any_call("/TestFile.pdf")
        self.assertIsNone(self._nested_file(self._stored_submodel(submodel.id), NESTED_FILE).value)

    @with_json_client
    def test_submodel_element_attachment_delete_file_ignores_store_error(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"

        self.file_store.delete_file.side_effect = KeyError

        response = format_client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(204, response.status_code)
        self.file_store.delete_file.assert_any_call("/TestFile.pdf")
        self.assertIsNone(self._nested_file(self._stored_submodel(submodel.id), NESTED_FILE).value)

    @with_json_client
    def test_submodel_element_attachment_delete_on_non_attachment_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment"
        )

        self.assert_error(response, 400)

    @with_json_client
    def test_submodel_element_attachment_delete_no_value_returns_404(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_blob(submodel, NESTED_BLOB).value = None

        response = format_client.delete(
            f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment"
        )

        self.assert_error(response, 404)

    @with_json_client
    def test_submodel_element_attachment_delete_external_file_returns_400(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "C:\\Users\\Test\\x.pdf"

        response = format_client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(400, response.status_code)

    # ------------------------------------------------------------------ .../<idShortPath>/qualifiers

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifiers_get_list(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers")

        self.assert_ok(response)
        types = {format_client.field(node, "type") for node in format_client.parse_collection(response)}
        self.assertEqual({EXAMPLE_QUALIFIER_TYPE}, types)

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_get_by_type(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/"
            f"{base64url_encode(EXAMPLE_QUALIFIER_TYPE)}"
        )

        self.assert_ok(response)
        self.assertEqual(
            EXAMPLE_QUALIFIER_TYPE, format_client.field(format_client.parse_object(response), "type")
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_get_by_type_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/"
            f"{base64url_encode('urn:unknown-qualifier')}"
        )

        self.assert_error(response, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifiers_post_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        qualifier = model.Qualifier("AddedQualifier", model.datatypes.String, "v")

        response = format_client.post(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers", obj=qualifier
        )

        self.assertEqual(201, response.status_code)
        retrieved = self._nested_element(self._stored_submodel(submodel.id), NESTED_PROPERTY)
        self.assertTrue(retrieved.qualifier.contains_id("type", "AddedQualifier"))

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifiers_post_conflict(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        qualifier = model.Qualifier(EXAMPLE_QUALIFIER_TYPE, model.datatypes.String, "v")

        response = format_client.post(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers", obj=qualifier
        )

        self.assert_error(response, 409)

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_put_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        updated = model.Qualifier(EXAMPLE_QUALIFIER_TYPE, model.datatypes.String, "changed-value")

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/"
            f"{base64url_encode(EXAMPLE_QUALIFIER_TYPE)}",
            obj=updated,
        )

        self.assert_ok(response)
        retrieved = self._nested_element(self._stored_submodel(submodel.id), NESTED_PROPERTY)
        self.assertEqual("changed-value", retrieved.get_qualifier_by_type(EXAMPLE_QUALIFIER_TYPE).value)

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_put_changed_type_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        new_type = "http://example.org/Qualifier/ExampleQualifier_Changed"
        updated = model.Qualifier(new_type, model.datatypes.String, "changed-value")

        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/{base64url_encode(EXAMPLE_QUALIFIER_TYPE)}",
            obj=updated,
        )

        self.assertEqual(201, response.status_code)
        retrieved = self._nested_element(self._stored_submodel(submodel.id), NESTED_PROPERTY)
        self.assertTrue(retrieved.qualifier.contains_id("type", new_type))
        self.assertEqual(new_type, format_client.field(format_client.parse_object(response), "type"))

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_put_conflict(self, format_client: FormatClient):
        submodel = self.add_example_submodel()
        new_type = "http://example.org/Qualifier/ExampleQualifier_Changed"
        self._nested_property(submodel, NESTED_PROPERTY).qualifier.add(
            model.Qualifier(type_=new_type, value_type=model.datatypes.String, value="test")
        )
        self.object_store.commit(submodel)

        updated = model.Qualifier(new_type, model.datatypes.String, "changed-value")
        response = format_client.put(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/{base64url_encode(EXAMPLE_QUALIFIER_TYPE)}",
            obj=updated,
        )

        self.assertEqual(409, response.status_code)

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_delete_success(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/"
            f"{base64url_encode(EXAMPLE_QUALIFIER_TYPE)}"
        )

        self.assertEqual(204, response.status_code)
        retrieved = self._nested_element(self._stored_submodel(submodel.id), NESTED_PROPERTY)
        self.assertFalse(retrieved.qualifier.contains_id("type", EXAMPLE_QUALIFIER_TYPE))

    @with_json_client
    @with_xml_client
    def test_submodel_element_qualifier_delete_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/qualifiers/"
            f"{base64url_encode('urn:unknown-qualifier')}"
        )

        self.assert_error(response, 404)
