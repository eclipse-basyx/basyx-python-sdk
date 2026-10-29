# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import ReferenceJsonEncoder
from basyx.aas.examples.data import example_aas


class TestReferenceSerialization(unittest.TestCase):

    def test_submodel_element(self):
        sm = example_aas.create_example_submodel()
        element = sm.get_referable("ExampleRelationshipElement")

        out_str = json.dumps(element, cls=ReferenceJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"keys", "type"}, parsed_output.keys())
        self.assertGreater(len(parsed_output["keys"]), 0)

    def test_non_referable(self):
        obj = model.AssetInformation(global_asset_id="https://example.or/TestAssetId")

        with self.assertRaises(TypeError):
            json.dumps(obj, cls=ReferenceJsonEncoder)

    def test_list_of_elements(self):
        objects = [example_aas.create_example_submodel(), example_aas.create_example_asset_administration_shell()]

        out_str = json.dumps(objects, cls=ReferenceJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, list)
        for ref in parsed_output:
            self.assertEqual({"keys", "type"}, ref.keys())
            self.assertGreater(len(ref["keys"]), 0)
