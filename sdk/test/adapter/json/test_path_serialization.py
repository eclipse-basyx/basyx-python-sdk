# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import PathJsonEncoder
from basyx.aas.examples.data import example_aas, example_aas_mandatory_attributes


class TestPathJsonEncoder(unittest.TestCase):
    def setUp(self):
        self.submodel = example_aas.create_example_submodel()

    def test_submodel_deep_ok(self):
        out_str = json.dumps(self.submodel, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleRelationshipElement",
            "ExampleAnnotatedRelationshipElement",
            "ExampleAnnotatedRelationshipElement.ExampleAnnotatedRange",
            "ExampleAnnotatedRelationshipElement.ExampleAnnotatedProperty",
            "ExampleOperation",
            "ExampleCapability",
            "ExampleBasicEventElement",
            "ExampleSubmodelCollection",
            "ExampleSubmodelCollection.ExampleBlob",
            "ExampleSubmodelCollection.ExampleFile",
            "ExampleSubmodelCollection.ExampleFileURI",
            "ExampleSubmodelCollection.ExampleMultiLanguageProperty",
            "ExampleSubmodelCollection.ExampleRange",
            "ExampleSubmodelCollection.ExampleReferenceElement",
            "ExampleSubmodelCollection.ExampleSubmodelList",
            "ExampleSubmodelCollection.ExampleSubmodelList[0]",
            "ExampleSubmodelCollection.ExampleSubmodelList[1]",
        ], parsed_output)

    def test_submodel_core_ok(self):
        out_str = json.dumps(self.submodel, cls=PathJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleRelationshipElement",
            "ExampleAnnotatedRelationshipElement",
            "ExampleOperation",
            "ExampleCapability",
            "ExampleBasicEventElement",
            "ExampleSubmodelCollection",
        ], parsed_output)

    def test_deep_is_default_ok(self):
        deep_output = json.loads(json.dumps(self.submodel, cls=PathJsonEncoder, deep=True))

        out_str = json.dumps(self.submodel, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_submodel_without_id_short_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()

        out_str = json.dumps(submodel, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleRelationshipElement",
            "ExampleAnnotatedRelationshipElement",
            "ExampleOperation",
            "ExampleCapability",
            "ExampleBasicEventElement",
            "ExampleSubmodelList",
            "ExampleSubmodelList[0]",
            "ExampleSubmodelList[0].ExampleBlob",
            "ExampleSubmodelList[0].ExampleFile",
            "ExampleSubmodelList[0].ExampleMultiLanguageProperty",
            "ExampleSubmodelList[0].ExampleProperty",
            "ExampleSubmodelList[0].ExampleRange",
            "ExampleSubmodelList[0].ExampleReferenceElement",
            "ExampleSubmodelList[1]",
            "ExampleSubmodelList2",
        ], parsed_output)

    def test_empty_submodel_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_empty_submodel()

        out_str = json.dumps(submodel, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual([], parsed_output)

    def test_submodel_element_collection_deep_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleSubmodelCollection",
            "ExampleSubmodelCollection.ExampleBlob",
            "ExampleSubmodelCollection.ExampleFile",
            "ExampleSubmodelCollection.ExampleFileURI",
            "ExampleSubmodelCollection.ExampleMultiLanguageProperty",
            "ExampleSubmodelCollection.ExampleRange",
            "ExampleSubmodelCollection.ExampleReferenceElement",
            "ExampleSubmodelCollection.ExampleSubmodelList",
            "ExampleSubmodelCollection.ExampleSubmodelList[0]",
            "ExampleSubmodelCollection.ExampleSubmodelList[1]",
        ], parsed_output)

    def test_submodel_element_collection_core_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=PathJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleSubmodelCollection",
            "ExampleSubmodelCollection.ExampleBlob",
            "ExampleSubmodelCollection.ExampleFile",
            "ExampleSubmodelCollection.ExampleFileURI",
            "ExampleSubmodelCollection.ExampleMultiLanguageProperty",
            "ExampleSubmodelCollection.ExampleRange",
            "ExampleSubmodelCollection.ExampleReferenceElement",
            "ExampleSubmodelCollection.ExampleSubmodelList",
        ], parsed_output)

    def test_submodel_element_list_deep_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList")

        out_str = json.dumps(sml, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleSubmodelList",
            "ExampleSubmodelList[0]",
            "ExampleSubmodelList[0].ExampleBlob",
            "ExampleSubmodelList[0].ExampleFile",
            "ExampleSubmodelList[0].ExampleMultiLanguageProperty",
            "ExampleSubmodelList[0].ExampleProperty",
            "ExampleSubmodelList[0].ExampleRange",
            "ExampleSubmodelList[0].ExampleReferenceElement",
            "ExampleSubmodelList[1]",
        ], parsed_output)

    def test_submodel_element_list_core_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList")

        out_str = json.dumps(sml, cls=PathJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleSubmodelList",
            "ExampleSubmodelList[0]",
            "ExampleSubmodelList[1]",
        ], parsed_output)

    def test_empty_submodel_element_list_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList2")

        out_str = json.dumps(sml, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["ExampleSubmodelList2"], parsed_output)

    def test_entity_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity")

        out_str = json.dumps(entity, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleEntity",
            "ExampleEntity.ExampleProperty",
            "ExampleEntity.ExampleProperty2",
        ], parsed_output)

    def test_submodel_with_entity_deep_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()

        out_str = json.dumps(submodel, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleEntity",
            "ExampleEntity.ExampleProperty",
            "ExampleEntity.ExampleProperty2",
            "ExampleEntity2",
        ], parsed_output)

    def test_submodel_with_entity_core_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()

        out_str = json.dumps(submodel, cls=PathJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertCountEqual(["ExampleEntity", "ExampleEntity2"], parsed_output)

    def test_empty_entity_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity2")

        out_str = json.dumps(entity, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["ExampleEntity2"], parsed_output)

    def test_annotated_relationship_element_ok(self):
        are = self.submodel.get_referable("ExampleAnnotatedRelationshipElement")

        out_str = json.dumps(are, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleAnnotatedRelationshipElement",
            "ExampleAnnotatedRelationshipElement.ExampleAnnotatedProperty",
            "ExampleAnnotatedRelationshipElement.ExampleAnnotatedRange",
        ], parsed_output)

    def test_annotated_relationship_element_without_annotation_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        are = submodel.get_referable("ExampleAnnotatedRelationshipElement")

        out_str = json.dumps(are, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["ExampleAnnotatedRelationshipElement"], parsed_output)

    def test_operation_variables_not_included_ok(self):
        operation = self.submodel.get_referable("ExampleOperation")

        out_str = json.dumps(operation, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["ExampleOperation"], parsed_output)

    def test_leaf_element_ok(self):
        range_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleRange")

        out_str = json.dumps(range_element, cls=PathJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(["ExampleRange"], parsed_output)

    def test_submodel_element_list_child_fail(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList")
        if not isinstance(sml, model.SubmodelElementList):
            self.fail("Expected `ExampleSubmodelList` to be of type `SubmodelElementList`.")
        sml_child = sml.value[0]

        with self.assertRaises(ValueError):
            json.dumps(sml_child, cls=PathJsonEncoder)

    def test_element_without_id_short_fail(self):
        prop = model.Property(None, model.datatypes.String)

        with self.assertRaises(ValueError):
            json.dumps(prop, cls=PathJsonEncoder)

    def test_unsupported_type_fail(self):
        unsupported = object()

        with self.assertRaises(TypeError):
            json.dumps(unsupported, cls=PathJsonEncoder)

    def test_asset_administration_shell_fail(self):
        aas = example_aas.create_example_asset_administration_shell()

        with self.assertRaises(TypeError):
            json.dumps(aas, cls=PathJsonEncoder)

    def test_concept_description_fail(self):
        concept_description = example_aas.create_example_concept_description()

        with self.assertRaises(TypeError):
            json.dumps(concept_description, cls=PathJsonEncoder)
