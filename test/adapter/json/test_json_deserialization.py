# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
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
from aas.adapter.json import AASFromJsonDecoder, StrictAASFromJsonDecoder, read_aas_json_file
from aas import model


class JsonDeserializationTest(unittest.TestCase):
    def test_file_format_missing_list(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": []
            }"""
        with self.assertRaisesRegex(KeyError, r"submodels"):
            read_aas_json_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), True)
        self.assertIn("submodels", cm.output[0])

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
            read_aas_json_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), True)
        self.assertIn("submodels", cm.output[0])
        self.assertIn("Asset", cm.output[0])

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
            read_aas_json_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            read_aas_json_file(io.StringIO(data), True)
        self.assertIn("submodels", cm.output[0])
        self.assertIn("'foo'", cm.output[0])

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
        self.assertIn("identification", cm.output[0])
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
        self.assertIn("modelType", cm.output[0])

        # In failsafe mode, we should get a log entries for the broken object and the wrong type of the first two
        #   submodelElements
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            parsed_data = json.loads(data, cls=AASFromJsonDecoder)
        self.assertGreaterEqual(len(cm.output), 3)
        self.assertIn("SubmodelElement", cm.output[1])
        self.assertIn("SubmodelElement", cm.output[2])

        self.assertIsInstance(parsed_data[0], model.Submodel)
        self.assertEqual(1, len(parsed_data[0].submodel_element))
        cap = parsed_data[0].submodel_element.pop()
        self.assertIsInstance(cap, model.Capability)
        self.assertEqual("TestCapability", cap.id_short)


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
