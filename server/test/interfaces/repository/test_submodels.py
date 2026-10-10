# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import io
import json
import math
from typing import Any
from unittest import mock

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.examples.data.example_aas import create_example_bill_of_material_submodel
from basyx.aas.examples.data.example_aas_missing_attributes import create_example_submodel

from ..format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from .helpers import RepositoryEndpointTestBase


def _encode_reference(reference: model.Reference) -> str:
    return base64url_encode(json.dumps(reference, cls=AASToJsonEncoder))


# semanticId carried by ``create_example_submodel()``.
EXAMPLE_SEMANTIC_ID = model.ExternalReference(
    (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "http://example.org/SubmodelTemplates/ExampleSubmodel"),)
)

# Top-level submodel elements of ``create_example_submodel()`` that have a ValueOnly representation, in document
# order. ExampleOperation and ExampleCapability have none and are omitted by the ``$value`` routes.
VALUE_ONLY_ID_SHORTS = (
    "ExampleRelationshipElement",
    "ExampleAnnotatedRelationshipElement",
    "ExampleBasicEventElement",
    "ExampleSubmodelCollection",
)

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
        response = format_client.get(f"/submodels?{query}")
        self.assert_ok(response)
        return {format_client.identifier(node) for node in format_client.parse_collection(response)}

    # ------------------------------------------------------------------ GET /submodels

    @with_json_client
    @with_xml_client
    def test_submodels_get(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        response = format_client.get("/submodels")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodels_get_empty(self, format_client: FormatClient):
        response = format_client.get("/submodels")

        self.assert_ok(response)
        self.assertEqual(0, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodels_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_submodels_store())

        pages = format_client.get_paginated("/submodels", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

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

    # ------------------------------------------------------------------ GET /submodels/<submodel_id>

    @with_json_client
    @with_xml_client
    def test_submodel_get_success(self, format_client: FormatClient):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.get(f"/submodels/{base64url_encode(example_submodel.id)}")

        self.assert_ok(response)
        self.assertEqual(example_submodel.id, format_client.identifier(format_client.parse_object(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"/submodels/{base64url_encode('https://example.org/unknown')}")

        self.assert_error(response, 404)

    def test_submodel_get_stripped_omits_submodel_elements(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)
        path = f"/submodels/{base64url_encode(example_submodel.id)}"

        full = self.client.get(path)
        stripped = self.client.get(f"{path}?level=core")

        self.assert_ok(full)
        self.assert_ok(stripped)
        self.assertIn("submodelElements", full.get_data(as_text=True))
        self.assertNotIn("submodelElements", stripped.get_data(as_text=True))

    def test_submodel_get_invalid_level_returns_400(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(f"/submodels/{base64url_encode(example_submodel.id)}?level=bogus")

        self.assert_error(response, 400)

    def test_submodel_get_extent_not_implemented(self):
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = self.client.get(
            f"/submodels/{base64url_encode(example_submodel.id)}?extent=withBlobValue"
        )

        self.assert_error(response, 501)

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


# ExampleSubmodelCollection (a nested namespace) and one of its children, carried by
# ``create_example_submodel()``; used as ready-made id_short paths in the tests below.
NESTED_COLLECTION = "ExampleSubmodelCollection"
NESTED_PROPERTY = "ExampleSubmodelCollection.ExampleProperty"
NESTED_BLOB = "ExampleSubmodelCollection.ExampleBlob"
NESTED_FILE = "ExampleSubmodelCollection.ExampleFile"
EXAMPLE_QUALIFIER_TYPE = "http://example.org/Qualifier/ExampleQualifier"


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

    def _get_element_value(self, format_client: FormatClient, submodel_id: str, id_short_path: str) -> Any:
        response = format_client.get(f"{self.elements_path(submodel_id, id_short_path)}/$value")
        self.assert_ok(response)
        return format_client.parse_object(response)

    # ------------------------------------------------------------------ GET .../submodel-elements

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id))

        self.assert_ok(response)
        self.assertEqual(self.TOP_LEVEL_COUNT, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_pagination_limit(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(f"{self.elements_path(submodel.id)}?limit=2")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_supports_pagination(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        pages = format_client.get_paginated(self.elements_path(submodel.id), limit=3, max_pages=2)

        self.assertEqual([3, 3], [len(page) for page in pages])

    @with_json_client
    @with_xml_client
    def test_submodel_elements_get_submodel_not_found(self, format_client: FormatClient):
        response = format_client.get(self.elements_path("https://example.org/unknown"))

        self.assert_error(response, 404)

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

    # ------------------------------------------------------------------ GET .../submodel-elements/<idShortPath>

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_top_level(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id, "ExampleCapability"))

        self.assert_ok(response)
        self.assertEqual(
            "ExampleCapability", format_client.field(format_client.parse_object(response), "idShort")
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_nested(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id, NESTED_PROPERTY))

        self.assert_ok(response)
        self.assertEqual(
            "ExampleProperty", format_client.field(format_client.parse_object(response), "idShort")
        )

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(self.elements_path(submodel.id, "DoesNotExist"))

        self.assert_error(response, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_get_nested_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.get(
            self.elements_path(submodel.id, f"{NESTED_COLLECTION}.DoesNotExist")
        )

        self.assert_error(response, 404)

    def test_submodel_element_get_path_through_non_namespace_returns_400(self):
        submodel = self.add_example_submodel()

        response = self.client.get(self.elements_path(submodel.id, f"{NESTED_PROPERTY}.Child"))

        self.assert_error(response, 400)

    def test_submodel_element_get_malformed_id_short_path_returns_400(self):
        submodel = self.add_example_submodel()

        response = self.client.get(self.elements_path(submodel.id, "a..b"))

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

    def test_submodel_element_post_into_non_namespace_returns_400(self):
        submodel = self.add_example_submodel()
        payload = json.dumps(
            model.Property("Child", model.datatypes.String, "v"), cls=AASToJsonEncoder
        )

        response = self.client.post(
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
        follow_up = format_client.get(self.elements_path(submodel.id, NESTED_PROPERTY))
        self.assert_error(follow_up, 404)

    @with_json_client
    @with_xml_client
    def test_submodel_element_delete_not_found(self, format_client: FormatClient):
        submodel = self.add_example_submodel()

        response = format_client.delete(self.elements_path(submodel.id, "DoesNotExist"))

        self.assert_error(response, 404)

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

    # ------------------------------------------------------------------ .../<idShortPath>/attachment

    def test_submodel_element_attachment_get_blob(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/pdf", response.mimetype)
        self.assertEqual(bytes([1, 2, 3, 4, 5]), response.get_data())

    def test_submodel_element_attachment_get_file(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"
        self._nested_file(submodel, NESTED_FILE).content_type = "application/pdf"

        self.file_store.write_file.side_effect = lambda name, stream: stream.write(b"file-content")

        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/pdf", response.content_type)
        self.file_store.write_file.assert_any_call("/TestFile.pdf", mock.ANY)
        self.assertEqual(b"file-content", response.data)

    def test_submodel_element_attachment_get_on_non_file_returns_400(self):
        submodel = self.add_example_submodel()

        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment")

        self.assert_error(response, 400)

    def test_submodel_element_attachment_get_file_without_value_returns_404(self):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None
        self.object_store.add(submodel)

        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 404)

    def test_submodel_element_attachment_get_external_file_return_400(self):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "C:\\Users\\Test\\File.pdf"
        self.object_store.add(submodel)

        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 400)

    def test_submodel_element_attachment_get_missing_file_return_404(self):
        submodel = create_example_submodel()
        self.object_store.add(submodel)

        self.file_store.write_file.side_effect = KeyError
        response = self.client.get(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assert_error(response, 404)

    def test_submodel_element_attachment_put_success(self):
        submodel = create_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None
        self.object_store.add(submodel)
        self.file_store.add_file.return_value = "/uploaded.pdf"

        response = self.client.put(
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

    def test_submodel_element_attachment_put_conflict_when_value_present(self):
        submodel = self.add_example_submodel()

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={
                "fileName": "/uploaded.pdf",
                "file": (io.BytesIO(b"pdf-bytes"), "uploaded.pdf", "application/pdf"),
            },
            content_type="multipart/form-data",
        )

        self.assert_error(response, 409)

    def test_submodel_element_attachment_put_on_non_file_returns_400(self):
        submodel = self.add_example_submodel()

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment",
            data={"fileName": "/x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    def test_submodel_element_attachment_put_missing_filename_returns_400(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    def test_submodel_element_attachment_put_external_filename_returns_400(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "C:\\Users\\Test\\x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    def test_submodel_element_attachment_put_missing_file_returns_400(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "/x.pdf"},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 400)

    def test_submodel_element_attachment_put_mimetype_mismatch_returns_400(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = None

        response = self.client.put(
            f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment",
            data={"fileName": "/x.pdf", "file": (io.BytesIO(b"x"), "x.pdf", "application/xml")},
            content_type="multipart/form-data",
        )

        self.assert_error(response, 415)

    def test_submodel_element_attachment_delete_blob(self):
        submodel = self.add_example_submodel()

        response = self.client.delete(f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment")

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self._nested_blob(self._stored_submodel(submodel.id), NESTED_BLOB).value)

    def test_submodel_element_attachment_delete_file(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"

        response = self.client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(204, response.status_code)
        self.file_store.delete_file.assert_any_call("/TestFile.pdf")
        self.assertIsNone(self._nested_file(self._stored_submodel(submodel.id), NESTED_FILE).value)

    def test_submodel_element_attachment_delete_file_ignores_store_error(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "/TestFile.pdf"

        self.file_store.delete_file.side_effect = KeyError

        response = self.client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

        self.assertEqual(204, response.status_code)
        self.file_store.delete_file.assert_any_call("/TestFile.pdf")
        self.assertIsNone(self._nested_file(self._stored_submodel(submodel.id), NESTED_FILE).value)

    def test_submodel_element_attachment_delete_on_non_attachment_returns_400(self):
        submodel = self.add_example_submodel()

        response = self.client.delete(
            f"{self.elements_path(submodel.id, NESTED_PROPERTY)}/attachment"
        )

        self.assert_error(response, 400)

    def test_submodel_element_attachment_delete_no_value_returns_404(self):
        submodel = self.add_example_submodel()
        self._nested_blob(submodel, NESTED_BLOB).value = None

        response = self.client.delete(
            f"{self.elements_path(submodel.id, NESTED_BLOB)}/attachment"
        )

        self.assert_error(response, 404)

    def test_submodel_element_attachment_delete_external_file_returns_400(self):
        submodel = self.add_example_submodel()
        self._nested_file(submodel, NESTED_FILE).value = "C:\\Users\\Test\\x.pdf"

        response = self.client.delete(f"{self.elements_path(submodel.id, NESTED_FILE)}/attachment")

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
