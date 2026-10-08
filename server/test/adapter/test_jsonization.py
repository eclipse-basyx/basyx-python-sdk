# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import json
import unittest
from typing import Any

from app.adapter import ServerAASToJsonEncoder

from .descriptor_utils import example_aas_descriptor, example_submodel_descriptor


class TestRegistryObjectSerialization(unittest.TestCase):
    """
    Tests the serialization of full :class:`~app.model.descriptor.Descriptor` objects
    """

    def _assert_example_protocol(self, protocol: dict[str, Any]) -> None:
        self.assertEqual("https://example.org/endpoint", protocol["href"])
        self.assertEqual("ExampleProtocol", protocol["endpointProtocol"])
        self.assertEqual(["1", "2"], protocol["endpointProtocolVersion"])
        self.assertEqual("ExampleSubprotocol", protocol["subprotocol"])
        self.assertEqual("ExampleProtocolBody", protocol["subprotocolBody"])
        self.assertEqual("ExampleEncoding", protocol["subprotocolBodyEncoding"])

        # TODO: Endpoint security is currently not serialized (issue #632)
        # self.assertIsInstance(protocol["securityAttributes"], list)
        # self.assertEqual(1, len(protocol["securityAttributes"]))
        # self.assertEqual("NONE", protocol["securityAttributes"][0]["type"])
        # self.assertEqual("ExampleKey", protocol["securityAttributes"][0]["key"])
        # self.assertEqual("ExampleValue", protocol["securityAttributes"][0]["value"])

    def test_ass_descriptor_serialization(self) -> None:
        aas_descriptor = example_aas_descriptor(id_="http://example.org/Test_AAS")

        dump = json.dumps(aas_descriptor, cls=ServerAASToJsonEncoder)
        result = json.loads(dump)

        self.assertEqual("http://example.org/Test_AAS", result["id"])

        # description is list of model.LangStringTextType (covered in basyx.aas.adpater)
        self.assertIsInstance(result["description"], list)
        self.assertEqual(2, len(result["description"]))

        # displayName is list of model.LangStringNameType (covered in basyx.aas.adapter)
        self.assertIsInstance(result["displayName"], list)
        self.assertEqual(2, len(result["displayName"]))

        # TODO: enable when Descriptor serializes extensions (issue 630)
        # extensions attribute is list of model.Extension
        # self.assertIn("extensions", result)
        # self.assertIsInstance(result["extensions"], list)

        # administration is model.AdministrativeInformation
        self.assertIsInstance(result["administration"], dict)
        self.assertEqual("http://example.org/AdministrativeInformation", result["administration"]["templateId"])

        self.assertEqual("Instance", result["assetKind"])

        self.assertEqual("http://example.org/TestAssetType/", result["assetType"])

        self.assertIsInstance(result["endpoints"], list)
        self.assertEqual(1, len(result["endpoints"]))
        self.assertEqual("AAS-3.0", result["endpoints"][0]["interface"])
        self._assert_example_protocol(result["endpoints"][0]["protocolInformation"])

        self.assertEqual("http://example.org/TestAsset/", result["globalAssetId"])
        self.assertEqual("TestAsset", result["idShort"])

        # specificAssetIds attribute is list of model.SpecificAssetId (covered in basyx.aas.adpater)
        self.assertIsInstance(result["specificAssetIds"], list)
        self.assertEqual(1, len(result["specificAssetIds"]))

    def test_submodel_descriptor_serialization(self) -> None:
        sm_descriptor = example_submodel_descriptor(id_="http://example.org/Test_Submodel")

        dump = json.dumps(sm_descriptor, cls=ServerAASToJsonEncoder)
        result = json.loads(dump)

        self.assertEqual("http://example.org/Test_Submodel", result["id"])

        # description is list of model.LangStringTextType (covered in basyx.aas.adpater)
        self.assertIsInstance(result["description"], list)
        self.assertEqual(2, len(result["description"]))

        # displayName is list of model.LangStringNameType (covered in basyx.aas.adapter)
        self.assertIsInstance(result["displayName"], list)
        self.assertEqual(2, len(result["displayName"]))

        # TODO: enable when Descriptor serializes extensions (issue #630)
        # extensions attribute is list of model.Extension
        # self.assertIn("extensions", result)
        # self.assertIsInstance(result["extensions"], list)

        self.assertIsInstance(result["endpoints"], list)
        self.assertEqual(1, len(result["endpoints"]))
        self.assertEqual("SUBMODEL-3.0", result["endpoints"][0]["interface"])
        self._assert_example_protocol(result["endpoints"][0]["protocolInformation"])

        self.assertEqual("TestSubmodel", result["idShort"])
        # semanticId is model.Reference (covered in basyx.aas.adapter)
        self.assertEqual("http://example.org/SubmodelDescription/", result["semanticId"]["keys"][0]["value"])

        # TODO: SubmodelDescriptor currently uses trailing "s" (issue #631)
        # supplementalSemanticId is list of model.Reference
        # self.assertIsInstance(result["supplementalSemanticId"], list)
        # self.assertEqual(
        #     "http://example.org/SupplementalID/",
        #     result["supplementalSemanticId"][0]["keys"][0]["value"]
        # )
