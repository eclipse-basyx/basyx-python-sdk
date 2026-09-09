# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import base64
import io
import json
import unittest
from typing import Type, TypeVar

from app.interfaces.base import AASX_CONTENT_TYPE
from app.interfaces.repository import WSGIApp
from basyx.aas import model
from basyx.aas.adapter.aasx import AASXReader, DictSupplementaryFileContainer
from basyx.aas.examples.data.example_aas import create_full_example
from lxml import etree
from werkzeug.test import Client

BASE_PATH = "/api/v3.1"
SERIALIZATION_PATH = BASE_PATH + "/serialization"
# the only ConceptDescription of the example data, referenced by the semanticId of a SubmodelElement of
# CONCEPT_DESCRIPTION_SUBMODEL_ID
CONCEPT_DESCRIPTION_ID = "https://example.org/Test_ConceptDescription"
CONCEPT_DESCRIPTION_SUBMODEL_ID = "https://example.org/Test_Submodel"
# file referenced by a File SubmodelElement of the example data
SUPPLEMENTARY_FILE_NAME = "/TestFile.pdf"

_T = TypeVar("_T", bound=model.Identifiable)


def _encode_id(identifier: model.Identifier) -> str:
    return base64.urlsafe_b64encode(identifier.encode()).decode()


class SerializationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.example_data = create_full_example()
        self.aas = self._get_first_of_type(model.AssetAdministrationShell)
        self.submodel = self._get_by_id(CONCEPT_DESCRIPTION_SUBMODEL_ID, model.Submodel)
        self.file_store = DictSupplementaryFileContainer()
        self.file_store.add_file(SUPPLEMENTARY_FILE_NAME, io.BytesIO(b"%PDF-1.4 test"), "application/pdf")
        self.client = Client(WSGIApp(self.example_data, self.file_store))

    def _get_first_of_type(self, type_: Type[_T]) -> _T:
        return next(obj for obj in self.example_data if isinstance(obj, type_))

    def _get_by_id(self, identifier: model.Identifier, type_: Type[_T]) -> _T:
        obj = self.example_data.get(identifier)
        assert isinstance(obj, type_)
        return obj

    def _get_json_environment(self, query: str = "") -> dict:
        response = self.client.get(SERIALIZATION_PATH + query)
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.content_type)
        return json.loads(response.data)

    def test_without_ids_returns_whole_repository(self) -> None:
        environment = self._get_json_environment()
        expected_aas = [obj.id for obj in self.example_data if isinstance(obj, model.AssetAdministrationShell)]
        expected_submodels = [obj.id for obj in self.example_data if isinstance(obj, model.Submodel)]
        self.assertEqual(sorted(expected_aas), sorted(aas["id"] for aas in environment["assetAdministrationShells"]))
        self.assertEqual(sorted(expected_submodels), sorted(submodel["id"] for submodel in environment["submodels"]))

    def test_unreferenced_concept_descriptions_are_included_without_filter(self) -> None:
        orphan = model.ConceptDescription(id_="https://example.org/Orphan_ConceptDescription")
        self.example_data.add(orphan)
        environment = self._get_json_environment()
        self.assertIn(
            orphan.id, [concept_description["id"] for concept_description in environment["conceptDescriptions"]]
        )

    def test_concept_descriptions_are_excluded_without_filter(self) -> None:
        environment = self._get_json_environment("?includeConceptDescriptions=false")
        self.assertNotIn("conceptDescriptions", environment)

    def test_aas_ids_filter(self) -> None:
        environment = self._get_json_environment("?aasIds=" + _encode_id(self.aas.id))
        self.assertEqual([self.aas.id], [aas["id"] for aas in environment["assetAdministrationShells"]])
        self.assertNotIn("submodels", environment)

    def test_submodel_ids_filter(self) -> None:
        environment = self._get_json_environment("?submodelIds=" + _encode_id(self.submodel.id))
        self.assertEqual([self.submodel.id], [submodel["id"] for submodel in environment["submodels"]])
        self.assertNotIn("assetAdministrationShells", environment)

    def test_aas_and_submodel_ids_filter(self) -> None:
        environment = self._get_json_environment(
            f"?aasIds={_encode_id(self.aas.id)}&submodelIds={_encode_id(self.submodel.id)}"
        )
        self.assertEqual([self.aas.id], [aas["id"] for aas in environment["assetAdministrationShells"]])
        self.assertEqual([self.submodel.id], [submodel["id"] for submodel in environment["submodels"]])

    def test_referenced_concept_descriptions_are_included(self) -> None:
        environment = self._get_json_environment("?submodelIds=" + _encode_id(self.submodel.id))
        self.assertEqual(
            [CONCEPT_DESCRIPTION_ID],
            [concept_description["id"] for concept_description in environment["conceptDescriptions"]],
        )

    def test_unreferenced_concept_descriptions_are_excluded(self) -> None:
        submodel = self._get_by_id("http://example.org/Submodels/Assets/TestAsset/Identification", model.Submodel)
        environment = self._get_json_environment("?submodelIds=" + _encode_id(submodel.id))
        self.assertNotIn("conceptDescriptions", environment)

    def test_include_concept_descriptions_false(self) -> None:
        environment = self._get_json_environment(
            f"?submodelIds={_encode_id(self.submodel.id)}&includeConceptDescriptions=false"
        )
        self.assertNotIn("conceptDescriptions", environment)

    def test_invalid_include_concept_descriptions_returns_400(self) -> None:
        response = self.client.get(SERIALIZATION_PATH + "?includeConceptDescriptions=yes")
        self.assertEqual(400, response.status_code)

    def test_xml_serialization(self) -> None:
        response = self.client.get(SERIALIZATION_PATH, headers={"Accept": "application/xml"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/xml", response.content_type)
        root = etree.fromstring(response.data)
        self.assertEqual("{https://admin-shell.io/aas/3/1}environment", root.tag)

    def test_aasx_serialization(self) -> None:
        response = self.client.get(
            SERIALIZATION_PATH + "?aasIds=" + _encode_id(self.aas.id), headers={"Accept": AASX_CONTENT_TYPE}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(AASX_CONTENT_TYPE, response.content_type)
        objects: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        AASXReader(io.BytesIO(response.data)).read_into(objects, DictSupplementaryFileContainer())
        self.assertEqual([self.aas.id], [obj.id for obj in objects])

    def test_unknown_id_returns_404(self) -> None:
        response = self.client.get(SERIALIZATION_PATH + "?aasIds=" + _encode_id("http://example.org/nonexistent_aas"))
        self.assertEqual(404, response.status_code)

    def test_aasx_serialization_contains_supplementary_files(self) -> None:
        response = self.client.get(
            SERIALIZATION_PATH + "?submodelIds=" + _encode_id(self.submodel.id), headers={"Accept": AASX_CONTENT_TYPE}
        )
        self.assertEqual(200, response.status_code)
        file_store = DictSupplementaryFileContainer()
        AASXReader(io.BytesIO(response.data)).read_into(model.DictIdentifiableStore(), file_store)
        self.assertIn(SUPPLEMENTARY_FILE_NAME, file_store)

    def test_text_xml_serialization(self) -> None:
        response = self.client.get(SERIALIZATION_PATH, headers={"Accept": "text/xml"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("text/xml", response.content_type)
        self.assertEqual("{https://admin-shell.io/aas/3/1}environment", etree.fromstring(response.data).tag)

    def test_invalid_base64_id_returns_400(self) -> None:
        response = self.client.get(SERIALIZATION_PATH + "?aasIds=invalid_base64!")
        self.assertEqual(400, response.status_code)

    def test_id_of_wrong_type_returns_404(self) -> None:
        response = self.client.get(SERIALIZATION_PATH + "?aasIds=" + _encode_id(self.submodel.id))
        self.assertEqual(404, response.status_code)

    def test_unresolvable_semantic_id_is_skipped(self) -> None:
        # a semanticId whose key path descends into a Property, which is not a namespace, must not render the whole
        # repository unserializable
        submodel_element = next(iter(self.submodel.submodel_element))
        submodel_element.semantic_id = model.ModelReference(
            (
                model.Key(model.KeyTypes.SUBMODEL, self.submodel.id),
                model.Key(model.KeyTypes.PROPERTY, submodel_element.id_short),
                model.Key(model.KeyTypes.PROPERTY, "nonexistent"),
            ),
            model.ConceptDescription,
        )
        environment = self._get_json_environment("?submodelIds=" + _encode_id(self.submodel.id))
        self.assertEqual([self.submodel.id], [submodel["id"] for submodel in environment["submodels"]])
        self.assertNotIn("conceptDescriptions", environment)

    def test_errors_are_returned_as_json_if_aasx_is_requested(self) -> None:
        response = self.client.get(
            SERIALIZATION_PATH + "?aasIds=" + _encode_id("http://example.org/nonexistent_aas"),
            headers={"Accept": AASX_CONTENT_TYPE},
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual("application/json", response.content_type)
        self.assertFalse(json.loads(response.data)["success"])

    def test_aasx_is_accepted_on_other_routes(self) -> None:
        # content negotiation happens before the route is matched, thus the AASX content type is accepted everywhere
        # and other routes respond with JSON instead of 406
        response = self.client.get(BASE_PATH + "/shells", headers={"Accept": AASX_CONTENT_TYPE})
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.content_type)


if __name__ == "__main__":
    unittest.main()
