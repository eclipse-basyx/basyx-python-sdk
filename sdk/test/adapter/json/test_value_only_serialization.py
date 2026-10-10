import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json.value_only_serialization import AASToValueOnlyJsonEncoder


class TestValueOnlyEncoder(unittest.TestCase):
    def test_omits_empty(self):
        sm = model.Submodel(id_="http://example.org/TestingSM", id_short="TestingSM")

        prop1 = model.Property(id_short="TestProperty1", value_type=model.datatypes.String, value="TestValue1")
        prop2 = model.Property(id_short="TestProperty2", value_type=model.datatypes.Boolean, value=True)
        collection1 = model.SubmodelElementCollection(id_short="TestCollection", value=[prop1, prop2])

        prop3 = model.Property(id_short="TestProperty3", value_type=model.datatypes.String)
        mlp = model.MultiLanguageProperty(id_short="TestMLP")
        rng1 = model.Range(id_short="TestRange", value_type=model.datatypes.Int)
        file = model.File(id_short="TestFile", content_type="application/pdf")
        blob = model.Blob(id_short="TestBlob")
        ref = model.ReferenceElement(id_short="TestRef")
        rel = model.RelationshipElement(id_short="TestRelationship")
        entity = model.Entity(id_short="TestEntity", entity_type=model.EntityType.CO_MANAGED_ENTITY)

        sm_list = model.SubmodelElementList(
            id_short="EmptyList",
            type_value_list_element=model.Property,
            value_type_list_element=model.datatypes.String,
            value=[prop3],
        )
        collection2 = model.SubmodelElementCollection(
            id_short="EmptyCollection", value=[mlp, rng1, file, blob, ref, rel, entity]
        )

        sm.submodel_element.add(collection1)
        sm.submodel_element.add(collection2)
        sm.submodel_element.add(sm_list)

        sm_str = json.dumps(sm, cls=AASToValueOnlyJsonEncoder)

        sm_dict = json.loads(sm_str)
        self.assertIsInstance(sm_dict, dict)
        self.assertNotIn("EmptyList", sm_dict)
        self.assertNotIn("EmptyCollection", sm_dict)

    def test_property(self):
        prop = model.Property(id_short="TestProperty", value_type=model.datatypes.Int, value=5000)

        out_str = json.dumps(prop, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertEqual(5000, parsed_output)

    def test_submodel_element_collection(self):
        prop1 = model.Property(
            id_short="ProductClassificationSystem", value_type=model.datatypes.String, value="ECLASS"
        )
        prop2 = model.Property(id_short="ProductOwnership", value_type=model.datatypes.Boolean, value=True)
        collection = model.SubmodelElementCollection(id_short="TestCollection", value=[prop1, prop2])

        out_str = json.dumps(collection, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"ProductClassificationSystem", "ProductOwnership"}, set(parsed_output.keys()))
        self.assertEqual("ECLASS", parsed_output["ProductClassificationSystem"])
        self.assertEqual(True, parsed_output["ProductOwnership"])

    def test_submodel_element_list(self):
        prop1 = model.Property(id_short="Prop1", value_type=model.datatypes.String, value="Martha")
        prop2 = model.Property(id_short="Prop2", value_type=model.datatypes.String, value="Jonathan")
        prop3 = model.Property(id_short="Prop3", value_type=model.datatypes.String, value="Clark")
        sme_list = model.SubmodelElementList(
            id_short="Authors",
            type_value_list_element=model.Property,
            value_type_list_element=model.datatypes.String,
            value=[prop1, prop2, prop3],
        )

        out_str = json.dumps(sme_list, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, list)
        self.assertEqual(["Martha", "Jonathan", "Clark"], parsed_output)

    def test_submodel_element_list_preserves_order(self):
        prop1 = model.Property(id_short="Prop1", value_type=model.datatypes.String, value="Martha")
        prop2 = model.Property(id_short="Prop2", value_type=model.datatypes.String)
        prop3 = model.Property(id_short="Prop3", value_type=model.datatypes.String, value="Clark")
        sme_list = model.SubmodelElementList(
            id_short="Authors",
            type_value_list_element=model.Property,
            value_type_list_element=model.datatypes.String,
            value=[prop1, prop2, prop3],
        )

        out_str = json.dumps(sme_list, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, list)
        self.assertEqual(["Martha", None, "Clark"], parsed_output)

    def test_multi_language_property(self):
        mlp = model.MultiLanguageProperty(
            id_short="MLP",
            value=model.MultiLanguageTextType(
                {"de": "Das ist ein deutscher Bezeichner", "en": "That's an English label"}
            ),
        )

        out_str = json.dumps(mlp, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, list)
        self.assertEqual(2, len(parsed_output))
        self.assertIn({"de": "Das ist ein deutscher Bezeichner"}, parsed_output)
        self.assertIn({"en": "That's an English label"}, parsed_output)

    def test_range(self):
        rng = model.Range(id_short="TorqueRange", value_type=model.datatypes.Int, min=3, max=15)

        out_str = json.dumps(rng, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"min", "max"}, parsed_output.keys())
        self.assertEqual(3, parsed_output["min"])
        self.assertEqual(15, parsed_output["max"])

    def test_reference_element(self):
        ref = model.ReferenceElement(
            id_short="MaxRotationSpeedReference",
            value=model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="0173-1#02-BAA120#008"),)
            ),
        )

        out_str = json.dumps(ref, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"type", "keys"}, parsed_output.keys())
        self.assertIsInstance(parsed_output["keys"], list)
        self.assertEqual(1, len(parsed_output["keys"]))
        self.assertEqual({"type", "value"}, parsed_output["keys"][0].keys())
        self.assertEqual("GlobalReference", parsed_output["keys"][0]["type"])
        self.assertEqual("0173-1#02-BAA120#008", parsed_output["keys"][0]["value"])

    def test_file(self):
        file = model.File(
            id_short="Document", content_type="application/pdf", value="https://example.org/SafetyInstructions.pdf"
        )

        out_str = json.dumps(file, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"contentType", "value"}, parsed_output.keys())
        self.assertEqual("application/pdf", parsed_output["contentType"])
        self.assertEqual("https://example.org/SafetyInstructions.pdf", parsed_output["value"])

    def test_file_without_value(self):
        file = model.File(id_short="Document", content_type="application/pdf")

        out_str = json.dumps(file, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"contentType"}, parsed_output.keys())
        self.assertEqual("application/pdf", parsed_output["contentType"])

    def test_blob(self):
        blob = model.Blob(id_short="Logo", content_type="application/octet-stream", value=b"\x00\x01BaSyx")

        out_str = json.dumps(blob, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"contentType", "value"}, parsed_output.keys())
        self.assertEqual("application/octet-stream", parsed_output["contentType"])
        self.assertEqual("AAFCYVN5eA==", parsed_output["value"])

    def test_relationship_element(self):
        rel = model.RelationshipElement(
            id_short="CurrentFlowsFrom",
            first=model.ModelReference(
                type_=model.Property,
                key=(
                    model.Key(type_=model.KeyTypes.SUBMODEL, value="http://customer.com/demo/aas/1/1/1234859590"),
                    model.Key(type_=model.KeyTypes.PROPERTY, value="PlusPole"),
                ),
            ),
            second=model.ModelReference(
                type_=model.Property,
                key=(
                    model.Key(type_=model.KeyTypes.SUBMODEL, value="http://customer.com/demo/aas/1/0/1234859123490"),
                    model.Key(type_=model.KeyTypes.PROPERTY, value="MinusPole"),
                ),
            ),
        )

        out_str = json.dumps(rel, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"first", "second"}, parsed_output.keys())
        self.assertEqual("PlusPole", parsed_output["first"]["keys"][1]["value"])
        self.assertEqual("MinusPole", parsed_output["second"]["keys"][1]["value"])

    def test_annotated_relationship_element(self):
        anrel = model.AnnotatedRelationshipElement(
            id_short="CurrentFlowsFrom",
            first=model.ModelReference(
                type_=model.Property,
                key=(
                    model.Key(type_=model.KeyTypes.SUBMODEL, value="http://customer.com/demo/aas/1/1/1234859590"),
                    model.Key(type_=model.KeyTypes.PROPERTY, value="PlusPole"),
                ),
            ),
            second=model.ModelReference(
                type_=model.Property,
                key=(
                    model.Key(type_=model.KeyTypes.SUBMODEL, value="http://customer.com/demo/aas/1/0/1234859123490"),
                    model.Key(type_=model.KeyTypes.PROPERTY, value="MinusPole"),
                ),
            ),
            annotation=[
                model.Property(
                    id_short="AppliedRule", value_type=model.datatypes.String, value="TechnicalCurrentFlowDirection"
                )
            ],
        )

        out_str = json.dumps(anrel, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"first", "second", "annotations"}, parsed_output.keys())
        self.assertEqual("PlusPole", parsed_output["first"]["keys"][1]["value"])
        self.assertEqual("MinusPole", parsed_output["second"]["keys"][1]["value"])
        self.assertIsInstance(parsed_output["annotations"], dict)
        self.assertEqual(1, len(parsed_output["annotations"]))
        self.assertEqual("TechnicalCurrentFlowDirection", parsed_output["annotations"]["AppliedRule"])

    def test_entity(self):
        entity = model.Entity(
            id_short="MySubAssetEntity",
            entity_type=model.EntityType.SELF_MANAGED_ENTITY,
            global_asset_id="http://customer.com/demo/asset/1/1/MySubAsset",
            specific_asset_id=[
                model.SpecificAssetId(name="SpecificAsset", value="http://customer.com/demo/asset/2/2/TestAsset")
            ],
            statement=[
                model.Property(id_short="MaxRotationSpeed", value_type=model.datatypes.Int, value=5000)
            ]
        )

        out_str = json.dumps(entity, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"entityType", "globalAssetId", "specificAssetIds", "statements"}, parsed_output.keys())
        self.assertEqual(5000, parsed_output["statements"]["MaxRotationSpeed"])
        self.assertEqual("http://customer.com/demo/asset/1/1/MySubAsset", parsed_output["globalAssetId"])

    def test_basic_event_element(self):
        event = model.BasicEventElement(
            id_short="MyBasicEvent",
            observed=model.ModelReference(
                type_=model.Property,
                key=(
                    model.Key(type_=model.KeyTypes.SUBMODEL, value="http://customer.com/demo/aas/1/1/1234859590"),
                    model.Key(type_=model.KeyTypes.PROPERTY, value="MaxRotation"),
                )
            ),
            direction=model.Direction.INPUT,
            state=model.StateOfEvent.ON
        )

        out_str = json.dumps(event, cls=AASToValueOnlyJsonEncoder)
        parsed_output = json.loads(out_str)

        self.assertIsInstance(parsed_output, dict)
        self.assertEqual({"observed"}, parsed_output.keys())
        self.assertEqual("MaxRotation", parsed_output["observed"]["keys"][1]["value"])
