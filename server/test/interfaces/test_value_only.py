# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import json
import math
import unittest
from typing import Any

from app.interfaces.repository import WSGIApp
from basyx.aas import model
from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.examples.data.example_aas import create_full_example
from basyx.aas.model import DictIdentifiableStore
from werkzeug.test import Client

BASE_PATH = "/api/v3.1"
TEST_SUBMODEL_ID = "https://example.org/Test_Submodel"
IDENTIFICATION_SUBMODEL_ID = "http://example.org/Submodels/Assets/TestAsset/Identification"
TYPED_SUBMODEL_ID = "http://example.org/Typed_Submodel"


def _encode(identifier: str) -> str:
    return base64.urlsafe_b64encode(identifier.encode()).decode()


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


class ValueOnlyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.example_data = create_full_example()
        self.example_data.add(_create_typed_submodel())
        self.client = Client(WSGIApp(self.example_data, DictSupplementaryFileContainer()))

    def _get_json(self, url: str, status_code: int = 200, **kwargs: Any) -> Any:
        response = self.client.get(f"{BASE_PATH}{url}", **kwargs)
        self.assertEqual(status_code, response.status_code, response.data)
        return json.loads(response.data)

    # --------- GET /submodels/{submodelIdentifier}/$value ---------

    def test_submodel_value(self) -> None:
        value = self._get_json(f"/submodels/{_encode(IDENTIFICATION_SUBMODEL_ID)}/$value")
        self.assertEqual({"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"}, value)

    def test_submodel_value_omits_operations_and_capabilities(self) -> None:
        value = self._get_json(f"/submodels/{_encode(TEST_SUBMODEL_ID)}/$value")
        self.assertNotIn("ExampleOperation", value)
        self.assertNotIn("ExampleCapability", value)

    def test_submodel_value_level_core_empties_nested_containers(self) -> None:
        value = self._get_json(f"/submodels/{_encode(TEST_SUBMODEL_ID)}/$value?level=core")
        # the direct children are present, their children are not
        self.assertIn("ExampleSubmodelCollection", value)
        self.assertEqual({}, value["ExampleSubmodelCollection"])
        self.assertEqual([], value["ExampleAnnotatedRelationshipElement"]["annotations"])

    def test_submodel_value_unknown_submodel(self) -> None:
        self._get_json(f"/submodels/{_encode('http://example.org/does_not_exist')}/$value", status_code=404)

    # --------- GET /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/$value ---------

    def test_property_value_types(self) -> None:
        base_url = f"/submodels/{_encode(TYPED_SUBMODEL_ID)}/submodel-elements"
        self.assertEqual(42, self._get_json(f"{base_url}/IntProperty/$value"))
        self.assertEqual(False, self._get_json(f"{base_url}/BoolProperty/$value"))
        self.assertEqual(1.5, self._get_json(f"{base_url}/DoubleProperty/$value"))
        # JSON has no representation for NaN, INF and -INF, so the XSD representation is returned instead
        self.assertEqual("NaN", self._get_json(f"{base_url}/NanProperty/$value"))
        # integers are not converted to float, as that would raise an OverflowError for large values
        self.assertEqual(10**400, self._get_json(f"{base_url}/HugeIntProperty/$value"))
        self.assertEqual("2026-08-31", self._get_json(f"{base_url}/DateProperty/$value"))
        self.assertIsNone(self._get_json(f"{base_url}/EmptyProperty/$value"))

    def test_submodel_value_with_huge_integer(self) -> None:
        # integers that exceed the range of a float are also serialized when the whole Submodel is requested
        value = self._get_json(f"/submodels/{_encode(TYPED_SUBMODEL_ID)}/$value")
        self.assertEqual(10**400, value["HugeIntProperty"])
        self.assertEqual(42, value["IntProperty"])

    def test_property_without_value_is_omitted_in_containers(self) -> None:
        value = self._get_json(f"/submodels/{_encode(TYPED_SUBMODEL_ID)}/$value")
        self.assertNotIn("EmptyProperty", value)

    def test_submodel_element_list_keeps_indices(self) -> None:
        value = self._get_json(f"/submodels/{_encode(TYPED_SUBMODEL_ID)}/submodel-elements/ListWithEmptyElement/$value")
        self.assertEqual(["first", None, "third"], value)

    def test_multi_language_property_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}"
            "/submodel-elements/ExampleSubmodelCollection.ExampleMultiLanguageProperty/$value"
        )
        self.assertEqual(2, len(value))
        self.assertEqual([1, 1], [len(entry) for entry in value])
        self.assertEqual(["de", "en-US"], [next(iter(entry)) for entry in value])

    def test_range_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleSubmodelCollection.ExampleRange/$value"
        )
        self.assertEqual({"min": 0, "max": 100}, value)

    def test_blob_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleSubmodelCollection.ExampleBlob/$value"
        )
        self.assertEqual(
            {"contentType": "application/pdf", "value": base64.b64encode(b"\x01\x02\x03\x04\x05").decode()}, value
        )

    def test_file_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleSubmodelCollection.ExampleFile/$value"
        )
        self.assertEqual({"contentType": "application/pdf", "value": "/TestFile.pdf"}, value)

    def test_reference_element_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}"
            "/submodel-elements/ExampleSubmodelCollection.ExampleReferenceElement/$value"
        )
        self.assertEqual("ModelReference", value["type"])
        self.assertEqual("Submodel", value["keys"][0]["type"])

    def test_relationship_element_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleRelationshipElement/$value"
        )
        self.assertEqual({"first", "second"}, set(value))
        self.assertEqual("ModelReference", value["first"]["type"])

    def test_annotated_relationship_element_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleAnnotatedRelationshipElement/$value"
        )
        self.assertEqual({"first", "second", "annotations"}, set(value))
        self.assertIn({"ExampleAnnotatedProperty": "exampleValue"}, value["annotations"])

    def test_basic_event_element_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleBasicEventElement/$value"
        )
        self.assertEqual(["observed"], list(value))
        self.assertEqual("ModelReference", value["observed"]["type"])

    def test_entity_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode('http://example.org/Submodels/Assets/TestAsset/BillOfMaterial')}"
            "/submodel-elements/ExampleEntity/$value"
        )
        self.assertEqual("SelfManagedEntity", value["entityType"])
        self.assertEqual("http://example.org/TestAsset/", value["globalAssetId"])
        self.assertEqual("exampleValue", value["statements"]["ExampleProperty"])
        self.assertEqual("TestKey", value["specificAssetIds"][0]["name"])

    def test_submodel_element_collection_value(self) -> None:
        value = self._get_json(
            f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/ExampleSubmodelCollection/$value"
        )
        self.assertIn("ExampleBlob", value)
        self.assertIn("ExampleSubmodelList", value)

    def test_operation_and_capability_are_rejected(self) -> None:
        base_url = f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements"
        self._get_json(f"{base_url}/ExampleOperation/$value", status_code=400)
        self._get_json(f"{base_url}/ExampleCapability/$value", status_code=400)

    def test_unknown_submodel_element(self) -> None:
        self._get_json(f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/DoesNotExist/$value", status_code=404)

    # --------- GET /submodels/{submodelIdentifier}/submodel-elements/$value ---------

    def test_submodel_elements_value(self) -> None:
        result = self._get_json(f"/submodels/{_encode(IDENTIFICATION_SUBMODEL_ID)}/submodel-elements/$value")
        self.assertEqual(
            [{"ManufacturerName": "ACPLT"}, {"InstanceId": "978-8234-234-342"}],
            result["result"],
        )

    def test_submodel_elements_value_omits_operations_and_capabilities(self) -> None:
        result = self._get_json(f"/submodels/{_encode(TEST_SUBMODEL_ID)}/submodel-elements/$value")
        id_shorts = [next(iter(entry)) for entry in result["result"]]
        self.assertNotIn("ExampleOperation", id_shorts)
        self.assertNotIn("ExampleCapability", id_shorts)

    def test_submodel_elements_value_pagination(self) -> None:
        result = self._get_json(f"/submodels/{_encode(IDENTIFICATION_SUBMODEL_ID)}/submodel-elements/$value?limit=1")
        self.assertEqual([{"ManufacturerName": "ACPLT"}], result["result"])
        self.assertEqual("2", result["paging_metadata"]["cursor"])

    # --------- GET /submodels/$value ---------

    def test_submodel_all_value(self) -> None:
        result = self._get_json("/submodels/$value")
        self.assertIn({"ManufacturerName": "ACPLT", "InstanceId": "978-8234-234-342"}, result["result"])

    def test_submodel_all_value_pagination(self) -> None:
        result = self._get_json("/submodels/$value?limit=1")
        self.assertEqual(1, len(result["result"]))
        self.assertEqual("2", result["paging_metadata"]["cursor"])

    # --------- serialization modifiers and content negotiation ---------

    def test_xml_is_not_acceptable(self) -> None:
        response = self.client.get(
            f"{BASE_PATH}/submodels/{_encode(TEST_SUBMODEL_ID)}/$value", headers={"Accept": "application/xml"}
        )
        self.assertEqual(406, response.status_code)

    def test_extent_is_not_implemented(self) -> None:
        response = self.client.get(f"{BASE_PATH}/submodels/{_encode(TEST_SUBMODEL_ID)}/$value?extent=withBlobValue")
        self.assertEqual(501, response.status_code)

    def test_invalid_level(self) -> None:
        response = self.client.get(f"{BASE_PATH}/submodels/{_encode(TEST_SUBMODEL_ID)}/$value?level=invalid")
        self.assertEqual(400, response.status_code)


class ValueOnlyEmptyStoreTest(unittest.TestCase):
    def test_empty_submodel(self) -> None:
        object_store: DictIdentifiableStore = DictIdentifiableStore()
        object_store.add(model.Submodel(id_=TYPED_SUBMODEL_ID))
        client = Client(WSGIApp(object_store, DictSupplementaryFileContainer()))
        response = client.get(f"{BASE_PATH}/submodels/{_encode(TYPED_SUBMODEL_ID)}/$value")
        self.assertEqual(200, response.status_code)
        self.assertEqual({}, json.loads(response.data))


if __name__ == "__main__":
    unittest.main()
