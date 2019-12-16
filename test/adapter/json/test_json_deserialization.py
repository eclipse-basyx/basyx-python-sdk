# Copyright 2019 PyI40AAS Contributors
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
import logging
import unittest
from aas.adapter.json import json_deserialization


class JsonDeserializationTest(unittest.TestCase):
    def test_file_format_missing_list(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": []
            }"""
        with self.assertRaisesRegex(KeyError, r"submodels"):
            json_deserialization.read_json_aas_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            json_deserialization.read_json_aas_file(io.StringIO(data), True)
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
            json_deserialization.read_json_aas_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            json_deserialization.read_json_aas_file(io.StringIO(data), True)
        self.assertIn("submodels", cm.output[0])
        self.assertIn("Asset", cm.output[0])

    def test_file_format_unknown_object(self) -> None:
        data = """
            {
                "assetAdministrationShells": [],
                "assets": [],
                "conceptDescriptions": [],
                "submodels": [
                    "foo"
                ]
            }"""
        with self.assertRaisesRegex(TypeError, r"submodels.*'foo'"):
            json_deserialization.read_json_aas_file(io.StringIO(data), False)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as cm:
            json_deserialization.read_json_aas_file(io.StringIO(data), True)
        self.assertIn("submodels", cm.output[0])
        self.assertIn("'foo'", cm.output[0])
