# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Additional tests for the adapter.json.json_deserialization module.

Deserialization is also somehow tested in the serialization tests -- at least, we get to know if exceptions are raised
when trying to reconstruct the serialized data structure. This module additionally tests error behaviour and verifies
deserialization results.
"""
import io
import json
import logging
import unittest
from basyx.aas.adapter.json import AASFromJsonDecoder, StrictAASFromJsonDecoder, StrictStrippedAASFromJsonDecoder, \
    read_aas_json_file, read_aas_json_file_into
from basyx.aas import model


class JsonDeserializationTest(unittest.TestCase):
    def test_file_format_missing_list(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": []
            }"""
        with self.assertRaisesRegex(KeyError, r"submodels"):
            read_aas_json_file(io.StringIO(data), failsafe=False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), failsafe=True)
        self.assertIn("submodels", cm.output[0])  # type: ignore

    def test_file_format_wrong_list(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": [],
                "submodels": [
                    {
                        "modelType": {
                            "name": "Asset"
                        },
                        "identification": {
                            "id": "https://acplt.org/Test_Asset",
                            "idType": "IRI"
                        },
                        "kind": "Instance"
                    }
                ]
            }"""
        with self.assertRaisesRegex(TypeError, r"submodels.*Asset"):
            read_aas_json_file(io.StringIO(data), failsafe=False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), failsafe=True)
        self.assertIn("submodels", cm.output[0])  # type: ignore
        self.assertIn("Asset", cm.output[0])  # type: ignore

    def test_file_format_unknown_object(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": [],
                "submodels": [
                    { "x": "foo" }
                ]
            }"""
        with self.assertRaisesRegex(TypeError, r"submodels.*'foo'"):
            read_aas_json_file(io.StringIO(data), failsafe=False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), failsafe=True)
        self.assertIn("submodels", cm.output[0])  # type: ignore
        self.assertIn("'foo'", cm.output[0])  # type: ignore

    def test_broken_asset(self) -> None:
        data = """
            [
                {
                    "modelType": {"name": "Asset"},
                    "kind": "Instance"
                },
                {
                    "modelType": {"name": "Asset"},
                    "identification": ["https://acplt.org/Test_Asset_broken_id", "IRI"],
                    "kind": "Instance"
                },
                {
                    "modelType": {"name": "Asset"},
                    "identification": {"id": "https://acplt.org/Test_Asset", "idType": "IRI"},
                    "kind": "Instance"
                }
            ]"""
        # In strict mode, we should catch an exception
        with self.assertRaisesRegex(KeyError, r"identification"):
            json.loads(data, cls=StrictAASFromJsonDecoder)

        # In failsafe mode, we should get a log entry and the first Asset entry should be returned as untouched dict
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            parsed_data = json.loads(data, cls=AASFromJsonDecoder)
        self.assertIn("identification", cm.output[0])  # type: ignore
        self.assertIsInstance(parsed_data, list)
        self.assertEqual(3, len(parsed_data))

        self.assertIsInstance(parsed_data[0], dict)
        self.assertIsInstance(parsed_data[1], dict)
        self.assertIsInstance(parsed_data[2], model.Asset)
        self.assertEqual("https://acplt.org/Test_Asset", parsed_data[2].identification.id)

    def test_wrong_submodel_element_type(self) -> None:
        data = """
            [
                {
                    "modelType": {"name": "Submodel"},
                    "identification": {
                        "id": "http://acplt.org/Submodels/Assets/TestAsset/Identification",
                        "idType": "IRI"
                    },
                    "submodelElements": [
                        {
                            "modelType": {"name": "Asset"},
                            "identification": {"id": "https://acplt.org/Test_Asset", "idType": "IRI"},
                            "kind": "Instance"
                        },
                        {
                            "modelType": "Broken modelType"
                        },
                        {
                            "modelType": {"name": "Capability"},
                            "idShort": "TestCapability"
                        }
                    ]
                }
            ]"""
        # In strict mode, we should catch an exception for the unexpected Asset within the Submodel
        # The broken object should not raise an exception, but log a warning, even in strict mode.
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            with self.assertRaisesRegex(TypeError, r"SubmodelElement.*Asset"):
                json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIn("modelType", cm.output[0])  # type: ignore

        # In failsafe mode, we should get a log entries for the broken object and the wrong type of the first two
        #   submodelElements
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            parsed_data = json.loads(data, cls=AASFromJsonDecoder)
        self.assertGreaterEqual(len(cm.output), 3)  # type: ignore
        self.assertIn("SubmodelElement", cm.output[1])  # type: ignore
        self.assertIn("SubmodelElement", cm.output[2])  # type: ignore

        self.assertIsInstance(parsed_data[0], model.Submodel)
        self.assertEqual(1, len(parsed_data[0].submodel_element))
        cap = parsed_data[0].submodel_element.pop()
        self.assertIsInstance(cap, model.Capability)
        self.assertEqual("TestCapability", cap.id_short)

    def test_duplicate_identifier(self) -> None:
        data = """
            {
                "assetAdministrationShells": [{
                    "modelType": {"name": "AssetAdministrationShell"},
                    "identification": {"idType": "IRI", "id": "http://acplt.org/test_aas"},
                    "asset": {
                        "keys": [{
                            "idType": "IRI",
                            "local": false,
                            "type": "Asset",
                            "value": "http://acplt.org/test_aas"
                        }]
                    }
                }],
                "submodels": [{
                    "modelType": {"name": "Submodel"},
                    "identification": {"idType": "IRI", "id": "http://acplt.org/test_aas"}
                }],
                "assets": [],
                "conceptDescriptions": []
            }"""
        string_io = io.StringIO(data)
        with self.assertLogs(logging.getLogger(), level=logging.ERROR) as cm:
            read_aas_json_file(string_io, failsafe=True)
        self.assertIn("duplicate identifier", cm.output[0])  # type: ignore
        string_io.seek(0)
        with self.assertRaisesRegex(KeyError, r"duplicate identifier"):
            read_aas_json_file(string_io, failsafe=False)

    def test_duplicate_identifier_object_store(self) -> None:
        sm_id = model.Identifier("http://acplt.org/test_submodel", model.IdentifierType.IRI)

        def get_clean_store() -> model.DictObjectStore:
            store: model.DictObjectStore = model.DictObjectStore()
            submodel_ = model.Submodel(sm_id, id_short="test123")
            store.add(submodel_)
            return store

        data = """
            {
                "submodels": [{
                    "modelType": {"name": "Submodel"},
                    "identification": {"idType": "IRI", "id": "http://acplt.org/test_submodel"},
                    "idShort": "test456"
                }],
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": []
            }"""

        string_io = io.StringIO(data)

        object_store = get_clean_store()
        identifiers = read_aas_json_file_into(object_store, string_io, replace_existing=True, ignore_existing=False)
        self.assertEqual(identifiers.pop(), sm_id)
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test456")

        string_io.seek(0)

        object_store = get_clean_store()
        with self.assertLogs(logging.getLogger(), level=logging.INFO) as log_ctx:
            identifiers = read_aas_json_file_into(object_store, string_io, replace_existing=False, ignore_existing=True)
        self.assertEqual(len(identifiers), 0)
        self.assertIn("already exists in the object store", log_ctx.output[0])  # type: ignore
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test123")

        string_io.seek(0)

        object_store = get_clean_store()
        with self.assertRaisesRegex(KeyError, r"already exists in the object store"):
            identifiers = read_aas_json_file_into(object_store, string_io, replace_existing=False,
                                                  ignore_existing=False)
        self.assertEqual(len(identifiers), 0)
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test123")


class JsonDeserializationDerivingTest(unittest.TestCase):
    def test_asset_constructor_overriding(self) -> None:
        class EnhancedAsset(model.Asset):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.enhanced_attribute = "fancy!"

        class EnhancedAASDecoder(AASFromJsonDecoder):
            @classmethod
            def _construct_asset(cls, dct):
                return super()._construct_asset(dct, object_class=EnhancedAsset)

        data = """
            [
                {
                    "modelType": {"name": "Asset"},
                    "identification": {"id": "https://acplt.org/Test_Asset", "idType": "IRI"},
                    "kind": "Instance"
                }
            ]"""
        parsed_data = json.loads(data, cls=EnhancedAASDecoder)
        self.assertEqual(1, len(parsed_data))
        self.assertIsInstance(parsed_data[0], EnhancedAsset)
        self.assertEqual(parsed_data[0].enhanced_attribute, "fancy!")


class JsonDeserializationStrippedObjectsTest(unittest.TestCase):
    def test_stripped_qualifiable(self) -> None:
        data = """
            {
                "modelType": {"name": "Submodel"},
                "identification": {"idType": "IRI", "id": "http://acplt.org/test_stripped_submodel"},
                "submodelElements": [{
                    "modelType": {"name": "Operation"},
                    "idShort": "test_operation",
                    "qualifiers": [{
                        "modelType": {"name": "Qualifier"},
                        "type": "test_qualifier",
                        "valueType": "string"
                    }]
                }],
                "qualifiers": [{
                    "modelType": {"name": "Qualifier"},
                    "type": "test_qualifier",
                    "valueType": "string"
                }]
            }"""

        # check if JSON with constraints can be parsed successfully
        submodel = json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIsInstance(submodel, model.Submodel)
        assert isinstance(submodel, model.Submodel)
        self.assertEqual(len(submodel.qualifier), 1)
        operation = submodel.submodel_element.pop()
        self.assertEqual(len(operation.qualifier), 1)

        # check if constraints are ignored in stripped mode
        submodel = json.loads(data, cls=StrictStrippedAASFromJsonDecoder)
        self.assertIsInstance(submodel, model.Submodel)
        assert isinstance(submodel, model.Submodel)
        self.assertEqual(len(submodel.qualifier), 0)
        self.assertEqual(len(submodel.submodel_element), 0)

    def test_stripped_annotated_relationship_element(self) -> None:
        data = """
            {
                "modelType": {"name": "AnnotatedRelationshipElement"},
                "idShort": "test_annotated_relationship_element",
                "first": {
                    "keys": [{
                        "idType": "IdShort",
                        "local": true,
                        "type": "AnnotatedRelationshipElement",
                        "value": "test_ref"
                    }]
                },
                "second": {
                    "keys": [{
                        "idType": "IdShort",
                        "local": true,
                        "type": "AnnotatedRelationshipElement",
                        "value": "test_ref"
                    }]
                },
                "annotation": [{
                    "modelType": {"name": "MultiLanguageProperty"},
                    "idShort": "test_multi_language_property"
                }]
            }"""

        # check if JSON with annotation can be parsed successfully
        are = json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIsInstance(are, model.AnnotatedRelationshipElement)
        assert isinstance(are, model.AnnotatedRelationshipElement)
        self.assertEqual(len(are.annotation), 1)

        # check if annotation is ignored in stripped mode
        are = json.loads(data, cls=StrictStrippedAASFromJsonDecoder)
        self.assertIsInstance(are, model.AnnotatedRelationshipElement)
        assert isinstance(are, model.AnnotatedRelationshipElement)
        self.assertEqual(len(are.annotation), 0)

    def test_stripped_entity(self) -> None:
        data = """
            {
                "modelType": {"name": "Entity"},
                "idShort": "test_entity",
                "entityType": "CoManagedEntity",
                "statements": [{
                    "modelType": {"name": "MultiLanguageProperty"},
                    "idShort": "test_multi_language_property"
                }]
            }"""

        # check if JSON with statements can be parsed successfully
        entity = json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIsInstance(entity, model.Entity)
        assert isinstance(entity, model.Entity)
        self.assertEqual(len(entity.statement), 1)

        # check if statements is ignored in stripped mode
        entity = json.loads(data, cls=StrictStrippedAASFromJsonDecoder)
        self.assertIsInstance(entity, model.Entity)
        assert isinstance(entity, model.Entity)
        self.assertEqual(len(entity.statement), 0)

    def test_stripped_submodel_element_collection(self) -> None:
        data = """
            {
                "modelType": {"name": "SubmodelElementCollection"},
                "idShort": "test_submodel_element_collection",
                "ordered": false,
                "value": [{
                    "modelType": {"name": "MultiLanguageProperty"},
                    "idShort": "test_multi_language_property"
                }]
            }"""

        # check if JSON with value can be parsed successfully
        sec = json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIsInstance(sec, model.SubmodelElementCollectionUnordered)
        assert isinstance(sec, model.SubmodelElementCollectionUnordered)
        self.assertEqual(len(sec.value), 1)

        # check if value is ignored in stripped mode
        sec = json.loads(data, cls=StrictStrippedAASFromJsonDecoder)
        self.assertIsInstance(sec, model.SubmodelElementCollectionUnordered)
        assert isinstance(sec, model.SubmodelElementCollectionUnordered)
        self.assertEqual(len(sec.value), 0)

    def test_stripped_asset_administration_shell(self) -> None:
        data = """
            {
                "modelType": {"name": "AssetAdministrationShell"},
                "identification": {"idType": "IRI", "id": "http://acplt.org/test_aas"},
                "asset": {
                    "keys": [{
                        "idType": "IRI",
                        "local": false,
                        "type": "Asset",
                        "value": "http://acplt.org/test_aas"
                    }]
                },
                "submodels": [{
                    "keys": [{
                        "idType": "IRI",
                        "local": false,
                        "type": "Submodel",
                        "value": "http://acplt.org/test_submodel"
                    }]
                }],
                "views": [{
                    "modelType": {"name": "View"},
                    "idShort": "test_view"
                }]
            }"""

        # check if JSON with submodels and views can be parsed successfully
        aas = json.loads(data, cls=StrictAASFromJsonDecoder)
        self.assertIsInstance(aas, model.AssetAdministrationShell)
        assert isinstance(aas, model.AssetAdministrationShell)
        self.assertEqual(len(aas.submodel), 1)
        self.assertEqual(len(aas.view), 1)

        # check if submodels and views are ignored in stripped mode
        aas = json.loads(data, cls=StrictStrippedAASFromJsonDecoder)
        self.assertIsInstance(aas, model.AssetAdministrationShell)
        assert isinstance(aas, model.AssetAdministrationShell)
        self.assertEqual(len(aas.submodel), 0)
        self.assertEqual(len(aas.view), 0)
