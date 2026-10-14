# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import json
import unittest

from basyx.aas.adapter.json import PathJsonEncoder, ShallowPathJsonEncoder
from basyx.aas.examples.data import example_aas


class TestPathSerialization(unittest.TestCase):
    def test_submodel_top_level(self):
        sm = example_aas.create_example_submodel()

        out_str = json.dumps(sm, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")
        self.assertNotIn(sm.id_short, parsed_output)
        self.assertIn("ExampleOperation", parsed_output)
        self.assertIn("ExampleCapability", parsed_output)
        self.assertIn("ExampleBasicEventElement", parsed_output)
        self.assertIn("ExampleRelationshipElement", parsed_output)
        self.assertIn("ExampleAnnotatedRelationshipElement", parsed_output)
        self.assertIn("ExampleSubmodelCollection", parsed_output)

    def test_submodel_collection_deep(self):
        sm = example_aas.create_example_submodel()

        out_str = json.dumps(sm, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")

        self.assertIn("ExampleSubmodelCollection.ExampleBlob", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleFile", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleFileURI", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleMultiLanguageProperty", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleRange", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleReferenceElement", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleSubmodelList", parsed_output)

    def test_submodel_list_deep(self):
        sm = example_aas.create_example_submodel()

        out_str = json.dumps(sm, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")

        self.assertIn("ExampleSubmodelCollection.ExampleSubmodelList[0]", parsed_output)
        self.assertIn("ExampleSubmodelCollection.ExampleSubmodelList[1]", parsed_output)

    def test_annotation_deep(self):
        sm = example_aas.create_example_submodel()

        out_str = json.dumps(sm, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")

        self.assertIn("ExampleAnnotatedRelationshipElement.ExampleAnnotatedProperty", parsed_output)
        self.assertIn("ExampleAnnotatedRelationshipElement.ExampleAnnotatedRange", parsed_output)

    def test_nested_element(self):
        sm = example_aas.create_example_submodel()
        sml = sm.get_referable("ExampleSubmodelCollection.ExampleSubmodelList")

        out_str = json.dumps(sml, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")

        self.assertIn("ExampleSubmodelList[0]", parsed_output)
        self.assertIn("ExampleSubmodelList[1]", parsed_output)

    def test_error_on_unsupported_types(self):
        aas = example_aas.create_example_asset_administration_shell()

        with self.assertRaises(TypeError):
            json.dumps(aas, cls=PathJsonEncoder)

    def test_level_core(self):
        sm = example_aas.create_example_submodel()

        out_str = json.dumps(sm, cls=ShallowPathJsonEncoder)
        parsed_output = json.loads(out_str)

        if not isinstance(parsed_output, list):
            self.fail("Path serialization is not a list")

        self.assertIn("ExampleOperation", parsed_output)
        self.assertIn("ExampleCapability", parsed_output)
        self.assertIn("ExampleBasicEventElement", parsed_output)
        self.assertIn("ExampleRelationshipElement", parsed_output)
        self.assertIn("ExampleAnnotatedRelationshipElement", parsed_output)
        self.assertIn("ExampleSubmodelCollection", parsed_output)
        self.assertNotIn("ExampleSubmodelCollection.ExampleBlob", parsed_output)
        self.assertNotIn("ExampleSubmodelCollection.ExampleSubmodelList[0]", parsed_output)
        self.assertNotIn("ExampleAnnotatedRelationshipElement.ExampleAnnotatedProperty", parsed_output)
