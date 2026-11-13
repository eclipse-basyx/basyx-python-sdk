# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder, StrippedAASToJsonEncoder
from basyx.aas.examples.data import example_aas, example_aas_mandatory_attributes


class TestAASToJsonEncoderCore(unittest.TestCase):
    def setUp(self):
        self.submodel = example_aas.create_example_submodel()
        self.deep_submodel = json.loads(json.dumps(self.submodel, cls=AASToJsonEncoder))

    def test_deep_is_default_ok(self):
        deep_output = json.loads(json.dumps(self.submodel, cls=AASToJsonEncoder, deep=True))

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_deep_keeps_grandchildren_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=AASToJsonEncoder, deep=True)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["value"]}
        self.assertEqual(2, len(children["ExampleSubmodelList"]["value"]))

    def test_submodel_ok(self):
        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "ExampleRelationshipElement",
            "ExampleAnnotatedRelationshipElement",
            "ExampleOperation",
            "ExampleCapability",
            "ExampleBasicEventElement",
            "ExampleSubmodelCollection",
        ], [element["idShort"] for element in parsed_output["submodelElements"]])

    def test_submodel_keeps_own_attributes_ok(self):
        expected = {key: value for key, value in self.deep_submodel.items() if key != "submodelElements"}

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        parsed_output.pop("submodelElements")
        self.assertEqual(expected, parsed_output)

    def test_submodel_omits_submodel_element_collection_children_ok(self):
        deep_children = {element["idShort"]: element for element in self.deep_submodel["submodelElements"]}
        expected = deep_children["ExampleSubmodelCollection"]
        expected.pop("value")

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertEqual(expected, children["ExampleSubmodelCollection"])

    def test_submodel_omits_annotated_relationship_element_annotations_ok(self):
        deep_children = {element["idShort"]: element for element in self.deep_submodel["submodelElements"]}
        expected = deep_children["ExampleAnnotatedRelationshipElement"]
        expected.pop("annotations")

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertEqual(expected, children["ExampleAnnotatedRelationshipElement"])

    def test_submodel_keeps_leaf_children_ok(self):
        deep_children = {element["idShort"]: element for element in self.deep_submodel["submodelElements"]}

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertEqual(deep_children["ExampleRelationshipElement"], children["ExampleRelationshipElement"])
        self.assertEqual(deep_children["ExampleOperation"], children["ExampleOperation"])
        self.assertEqual(deep_children["ExampleCapability"], children["ExampleCapability"])
        self.assertEqual(deep_children["ExampleBasicEventElement"], children["ExampleBasicEventElement"])

    def test_submodel_omits_entity_statements_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        deep_output = json.loads(json.dumps(submodel, cls=AASToJsonEncoder))
        deep_children = {element["idShort"]: element for element in deep_output["submodelElements"]}
        expected = deep_children["ExampleEntity"]
        expected.pop("statements")

        out_str = json.dumps(submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertEqual(expected, children["ExampleEntity"])
        self.assertEqual(deep_children["ExampleEntity2"], children["ExampleEntity2"])

    def test_empty_submodel_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_empty_submodel()

        out_str = json.dumps(submodel, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertNotIn("submodelElements", parsed_output)

    def test_submodel_element_collection_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")
        deep_output = json.loads(json.dumps(smc, cls=AASToJsonEncoder))
        deep_children = {element["idShort"]: element for element in deep_output["value"]}
        deep_children["ExampleSubmodelList"].pop("value")

        out_str = json.dumps(smc, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["value"]}
        self.assertEqual(deep_children, children)

    def test_submodel_element_list_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList")
        deep_output = json.loads(json.dumps(sml, cls=AASToJsonEncoder))
        expected = deep_output["value"]
        expected[0].pop("value")

        out_str = json.dumps(sml, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(expected, parsed_output["value"])

    def test_empty_submodel_element_list_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        sml = submodel.get_referable("ExampleSubmodelList2")

        out_str = json.dumps(sml, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertNotIn("value", parsed_output)

    def test_entity_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity")
        deep_output = json.loads(json.dumps(entity, cls=AASToJsonEncoder))

        out_str = json.dumps(entity, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_annotated_relationship_element_ok(self):
        are = self.submodel.get_referable("ExampleAnnotatedRelationshipElement")
        deep_output = json.loads(json.dumps(are, cls=AASToJsonEncoder))

        out_str = json.dumps(are, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_leaf_element_ok(self):
        range_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleRange")
        deep_output = json.loads(json.dumps(range_element, cls=AASToJsonEncoder))

        out_str = json.dumps(range_element, cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(deep_output, parsed_output)

    def test_core_is_relative_to_each_top_level_object_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps([self.submodel, smc], cls=AASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        submodel_output, smc_output = parsed_output
        submodel_children = {element["idShort"]: element for element in submodel_output["submodelElements"]}
        self.assertNotIn("value", submodel_children["ExampleSubmodelCollection"])
        self.assertEqual(7, len(smc_output["value"]))

    def test_core_with_indent_ok(self):
        compact_output = json.loads(json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False))

        out_str = json.dumps(self.submodel, cls=AASToJsonEncoder, deep=False, indent=2)
        parsed_output = json.loads(out_str)

        self.assertEqual(compact_output, parsed_output)

    def test_stripped_core_ok(self):
        stripped_output = json.loads(json.dumps(self.submodel, cls=StrippedAASToJsonEncoder))

        out_str = json.dumps(self.submodel, cls=StrippedAASToJsonEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertEqual(stripped_output, parsed_output)

    def test_subclass_override_applies_to_children_ok(self):
        class CustomCoreEncoder(AASToJsonEncoder):
            @classmethod
            def _submodel_element_collection_to_json(cls, obj):
                data = super()._submodel_element_collection_to_json(obj)
                data["custom"] = True
                return data

        out_str = json.dumps(self.submodel, cls=CustomCoreEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertTrue(children["ExampleSubmodelCollection"]["custom"])
        self.assertNotIn("value", children["ExampleSubmodelCollection"])

    def test_subclass_override_applies_to_requested_object_ok(self):
        class CustomCoreEncoder(AASToJsonEncoder):
            @classmethod
            def _submodel_element_collection_to_json(cls, obj):
                data = super()._submodel_element_collection_to_json(obj)
                data["custom"] = True
                return data

        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=CustomCoreEncoder, deep=False)
        parsed_output = json.loads(out_str)

        self.assertTrue(parsed_output["custom"])
        self.assertEqual(7, len(parsed_output["value"]))

    def test_subclass_deep_override_ok(self):
        class CustomEncoder(AASToJsonEncoder):
            @classmethod
            def _submodel_element_collection_to_json(cls, obj):
                data = super()._submodel_element_collection_to_json(obj)
                data["childTypes"] = [type(element).__name__ for element in data["value"]]
                return data

        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        out_str = json.dumps(smc, cls=CustomEncoder)
        parsed_output = json.loads(out_str)

        self.assertCountEqual([
            "Blob",
            "File",
            "File",
            "MultiLanguageProperty",
            "Range",
            "ReferenceElement",
            "SubmodelElementList",
        ], parsed_output["childTypes"])

    def test_subclass_mapping_override_applies_to_children_ok(self):
        class CustomCoreEncoder(AASToJsonEncoder):
            @classmethod
            def _get_aas_class_serializers(cls):
                mapping = super()._get_aas_class_serializers()
                mapping[model.SubmodelElementCollection] = cls._custom_collection_to_json
                return mapping

            @classmethod
            def _custom_collection_to_json(cls, obj):
                data = cls._submodel_element_collection_to_json(obj)
                data["custom"] = True
                return data

        out_str = json.dumps(self.submodel, cls=CustomCoreEncoder, deep=False)
        parsed_output = json.loads(out_str)

        children = {element["idShort"]: element for element in parsed_output["submodelElements"]}
        self.assertTrue(children["ExampleSubmodelCollection"]["custom"])
        self.assertNotIn("value", children["ExampleSubmodelCollection"])
