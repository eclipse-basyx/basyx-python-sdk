# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder, MetadataJsonEncoder
from basyx.aas.examples.data import example_aas, example_aas_mandatory_attributes


class TestMetadataJsonEncoder(unittest.TestCase):
    """
    Tests follow Table Metadata Attributes of the AAS API spec. For every class, verify that the fields
    listed as "not available in metadata representation" are dropped, while other attributes are retained.
    """

    def setUp(self):
        self.submodel = example_aas.create_example_submodel()

    # ================================================================== Identifiables

    # ----- AssetAdministrationShell: drops assetInformation, submodels
    def test_asset_administration_shell_drops_asset_information_and_submodels_ok(self):
        aas = example_aas.create_example_asset_administration_shell()

        base_output = json.loads(json.dumps(aas, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(aas, cls=MetadataJsonEncoder))

        self.assertNotIn("assetInformation", parsed_output)
        self.assertNotIn("submodels", parsed_output)
        self.assertEqual({"assetInformation", "submodels"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("AssetAdministrationShell", parsed_output["modelType"])

    # ----- Submodel: drops submodelElements
    def test_submodel_drops_submodel_elements_ok(self):
        base_output = json.loads(json.dumps(self.submodel, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(self.submodel, cls=MetadataJsonEncoder))

        self.assertNotIn("submodelElements", parsed_output)
        self.assertEqual({"submodelElements"}, set(base_output.keys()) - set(parsed_output.keys()))

    def test_submodel_keeps_identifiable_fields_ok(self):
        parsed_output = json.loads(json.dumps(self.submodel, cls=MetadataJsonEncoder))

        self.assertEqual(self.submodel.id, parsed_output["id"])
        self.assertEqual(self.submodel.id_short, parsed_output["idShort"])
        self.assertEqual("Submodel", parsed_output["modelType"])

    def test_empty_submodel_ok(self):
        submodel = example_aas_mandatory_attributes.create_example_empty_submodel()

        parsed_output = json.loads(json.dumps(submodel, cls=MetadataJsonEncoder))

        self.assertNotIn("submodelElements", parsed_output)
        self.assertEqual(submodel.id, parsed_output["id"])

    # ================================================================== SubmodelElements

    # ----- SubmodelElementCollection: drops value
    def test_submodel_element_collection_drops_value_ok(self):
        smc = self.submodel.get_referable("ExampleSubmodelCollection")

        base_output = json.loads(json.dumps(smc, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(smc, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertEqual({"value"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("SubmodelElementCollection", parsed_output["modelType"])

    # ----- SubmodelElementList: drops value
    def test_submodel_element_list_drops_value_ok(self):
        sml = self.submodel.get_referable("ExampleSubmodelCollection.ExampleSubmodelList")

        base_output = json.loads(json.dumps(sml, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(sml, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertEqual({"value"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("SubmodelElementList", parsed_output["modelType"])
        # List-level metadata (type/semantics of elements) must be retained
        self.assertIn("typeValueListElement", parsed_output)

    # ----- Entity: drops statements, globalAssetId, specificAssetId
    def test_entity_drops_statements_and_asset_identifiers_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity")

        base_output = json.loads(json.dumps(entity, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(entity, cls=MetadataJsonEncoder))

        self.assertNotIn("statements", parsed_output)
        self.assertNotIn("globalAssetId", parsed_output)
        self.assertNotIn("specificAssetIds", parsed_output)
        self.assertEqual(
            {"statements", "globalAssetId", "specificAssetIds"},
            set(base_output.keys()) - set(parsed_output.keys()),
        )
        self.assertEqual("Entity", parsed_output["modelType"])
        self.assertEqual("SelfManagedEntity", parsed_output["entityType"])

    def test_entity_without_statements_ok(self):
        submodel = example_aas.create_example_bill_of_material_submodel()
        entity = submodel.get_referable("ExampleEntity2")

        parsed_output = json.loads(json.dumps(entity, cls=MetadataJsonEncoder))

        self.assertNotIn("statements", parsed_output)

    # ----- BasicEventElement: drops observed
    def test_basic_event_element_drops_observed_ok(self):
        basic_event_element = self.submodel.get_referable("ExampleBasicEventElement")

        base_output = json.loads(json.dumps(basic_event_element, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(basic_event_element, cls=MetadataJsonEncoder))

        self.assertNotIn("observed", parsed_output)
        self.assertEqual({"observed"}, set(base_output.keys()) - set(parsed_output.keys()))
        # Other BasicEventElement metadata fields must be kept
        self.assertIn("direction", parsed_output)
        self.assertIn("state", parsed_output)

    # ----- Capability: no fields dropped
    def test_capability_ok(self):
        capability = self.submodel.get_referable("ExampleCapability")

        base_output = json.loads(json.dumps(capability, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(capability, cls=MetadataJsonEncoder))

        self.assertEqual(set(base_output.keys()), set(parsed_output.keys()))
        self.assertEqual("Capability", parsed_output["modelType"])

    # ----- Operation: no fields dropped
    def test_operation_ok(self):
        operation = self.submodel.get_referable("ExampleOperation")

        base_output = json.loads(json.dumps(operation, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(operation, cls=MetadataJsonEncoder))

        # Operation metadata keeps input/output/inoutput variables (they describe shape, not value)
        self.assertEqual(set(base_output.keys()), set(parsed_output.keys()))
        self.assertEqual("Operation", parsed_output["modelType"])

    # ================================================================== DataElements

    # ----- Property: drops value, valueId
    def test_property_drops_value_and_value_id_ok(self):
        prop = model.Property(
            "Prop",
            model.datatypes.String,
            value="exampleValue",
            value_id=model.ExternalReference(
                (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "https://example.org/ValueId"),)
            ),
        )

        base_output = json.loads(json.dumps(prop, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(prop, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertNotIn("valueId", parsed_output)
        self.assertEqual({"value", "valueId"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertIn("valueType", parsed_output)

    # ----- MultiLanguageProperty: drops value, valueId
    def test_multi_language_property_drops_value_and_value_id_ok(self):
        mlp = self.submodel.get_referable("ExampleSubmodelCollection.ExampleMultiLanguageProperty")

        base_output = json.loads(json.dumps(mlp, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(mlp, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertNotIn("valueId", parsed_output)
        self.assertLessEqual(
            set(base_output.keys()) - set(parsed_output.keys()),
            {"value", "valueId"},
        )
        self.assertEqual("MultiLanguageProperty", parsed_output["modelType"])

    # ----- Range: drops min, max
    def test_range_drops_min_and_max_ok(self):
        range_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleRange")

        base_output = json.loads(json.dumps(range_element, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(range_element, cls=MetadataJsonEncoder))

        self.assertNotIn("min", parsed_output)
        self.assertNotIn("max", parsed_output)
        self.assertEqual({"min", "max"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertIn("valueType", parsed_output)

    # ----- ReferenceElement: drops value
    def test_reference_element_drops_value_ok(self):
        reference_element = self.submodel.get_referable("ExampleSubmodelCollection.ExampleReferenceElement")

        base_output = json.loads(json.dumps(reference_element, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(reference_element, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertEqual({"value"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("ReferenceElement", parsed_output["modelType"])

    # ----- RelationshipElement: drops first, second
    def test_relationship_element_drops_first_and_second_ok(self):
        relationship_element = self.submodel.get_referable("ExampleRelationshipElement")

        base_output = json.loads(json.dumps(relationship_element, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(relationship_element, cls=MetadataJsonEncoder))

        self.assertNotIn("first", parsed_output)
        self.assertNotIn("second", parsed_output)
        self.assertEqual({"first", "second"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("RelationshipElement", parsed_output["modelType"])

    # ----- AnnotatedRelationshipElement: drops first, second, annotations
    def test_annotated_relationship_element_drops_endpoints_and_annotations_ok(self):
        are = self.submodel.get_referable("ExampleAnnotatedRelationshipElement")

        base_output = json.loads(json.dumps(are, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(are, cls=MetadataJsonEncoder))

        self.assertNotIn("first", parsed_output)
        self.assertNotIn("second", parsed_output)
        self.assertNotIn("annotations", parsed_output)
        self.assertEqual(
            {"first", "second", "annotations"},
            set(base_output.keys()) - set(parsed_output.keys()),
        )
        self.assertEqual("AnnotatedRelationshipElement", parsed_output["modelType"])

    # ----- Blob: drops value, contentType
    def test_blob_drops_value_and_content_type_ok(self):
        blob = self.submodel.get_referable("ExampleSubmodelCollection.ExampleBlob")

        base_output = json.loads(json.dumps(blob, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(blob, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertNotIn("contentType", parsed_output)
        self.assertEqual({"value", "contentType"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("Blob", parsed_output["modelType"])

    # ----- File: drops value, contentType
    def test_file_drops_value_and_content_type_ok(self):
        file = self.submodel.get_referable("ExampleSubmodelCollection.ExampleFile")

        base_output = json.loads(json.dumps(file, cls=AASToJsonEncoder))
        parsed_output = json.loads(json.dumps(file, cls=MetadataJsonEncoder))

        self.assertNotIn("value", parsed_output)
        self.assertNotIn("contentType", parsed_output)
        self.assertEqual({"value", "contentType"}, set(base_output.keys()) - set(parsed_output.keys()))
        self.assertEqual("File", parsed_output["modelType"])

    # ================================================================== Unsupported types

    def test_concept_description_fail(self):
        concept_description = example_aas.create_example_concept_description()

        with self.assertRaises(TypeError):
            json.dumps(concept_description, cls=MetadataJsonEncoder)

    # ================================================================== Composite

    def test_list_of_elements_ok(self):
        elements = [
            self.submodel.get_referable("ExampleRelationshipElement"),
            self.submodel.get_referable("ExampleSubmodelCollection"),
        ]

        parsed_output = json.loads(json.dumps(elements, cls=MetadataJsonEncoder))

        self.assertEqual(2, len(parsed_output))
        self.assertNotIn("first", parsed_output[0])
        self.assertNotIn("second", parsed_output[0])
        self.assertNotIn("value", parsed_output[1])
