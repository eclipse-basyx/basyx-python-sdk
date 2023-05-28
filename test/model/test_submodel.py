# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest
import dateutil.tz

from basyx.aas import model


class EntityTest(unittest.TestCase):

    def test_set_entity(self):
        with self.assertRaises(model.AASConstraintViolation) as cm:
            obj = model.Entity(id_short='Test', entity_type=model.EntityType.SELF_MANAGED_ENTITY, statement=())
        self.assertIn(
            'A self-managed entity has to have a globalAssetId or a specificAssetId',
            str(cm.exception)
        )
        with self.assertRaises(model.AASConstraintViolation) as cm:
            obj2 = model.Entity(id_short='Test', entity_type=model.EntityType.CO_MANAGED_ENTITY,
                                global_asset_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                                                 value='http://acplt.org/TestAsset/'),
                                                                       )),
                                statement=())
        self.assertIn(
            'A co-managed entity has to have neither a globalAssetId nor a specificAssetId',
            str(cm.exception)
        )

        specific_asset_id = model.SpecificAssetId(name="TestKey",
                                                  value="TestValue",
                                                  external_subject_id=model.GlobalReference((model.Key(
                                                      type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                      value='http://acplt.org/SpecificAssetId/'),)))
        with self.assertRaises(model.AASConstraintViolation) as cm:
            obj3 = model.Entity(id_short='Test', entity_type=model.EntityType.CO_MANAGED_ENTITY,
                                specific_asset_id=specific_asset_id, statement=())
        self.assertIn(
            'A co-managed entity has to have neither a globalAssetId nor a specificAssetId',
            str(cm.exception))


class PropertyTest(unittest.TestCase):
    def test_set_value(self):
        property = model.Property('test', model.datatypes.Int, 2)
        self.assertEqual(property.value, 2)
        property.value = None
        self.assertIsNone(property.value)


class RangeTest(unittest.TestCase):
    def test_set_min_max(self):
        range = model.Range('test', model.datatypes.Int, 2, 5)
        self.assertEqual(range.min, 2)
        self.assertEqual(range.max, 5)
        range.min = None
        self.assertIsNone(range.min)
        range.max = None
        self.assertIsNone(range.max)


class SubmodelElementListTest(unittest.TestCase):
    def test_constraints(self):
        # AASd-107
        mlp = model.MultiLanguageProperty("test", semantic_id=model.GlobalReference(
            (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:invalid"),)
        ))
        with self.assertRaises(model.AASConstraintViolation) as cm:
            model.SubmodelElementList("test_list", model.MultiLanguageProperty, {mlp},
                                      semantic_id_list_element=model.GlobalReference((
                                          model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:test"),)))
        self.assertEqual("If semantic_id_list_element=GlobalReference(key=(Key(type=GLOBAL_REFERENCE, "
                         "value=urn:x-test:test),)) is specified all first level children must have "
                         "the same semantic_id, got MultiLanguageProperty[test] with "
                         "semantic_id=GlobalReference(key=(Key(type=GLOBAL_REFERENCE, value=urn:x-test:invalid),)) "
                         "(Constraint AASd-107)", str(cm.exception))
        model.SubmodelElementList("test_list", model.MultiLanguageProperty, {mlp},
                                  semantic_id_list_element=model.GlobalReference((
                                      model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:invalid"),)))
        mlp.parent = None
        model.SubmodelElementList("test_list", model.MultiLanguageProperty, {mlp}, semantic_id_list_element=None)
        mlp = model.MultiLanguageProperty("test")
        model.SubmodelElementList("test_list", model.MultiLanguageProperty, {mlp},
                                  semantic_id_list_element=model.GlobalReference((
                                      model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:invalid"),)))

        # AASd-108
        are = model.AnnotatedRelationshipElement(
            "test",
            model.GlobalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:test-first"),)),
            model.GlobalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:test-second"),))
        )
        # This tests checks if subclasses of the required type are rejected in a SubmodelElementList.
        # Thus, a requirement is that AnnotatedRelationshipElement is a subclass of RelationshipElement:
        self.assertIsInstance(are, model.RelationshipElement)
        with self.assertRaises(model.AASConstraintViolation) as cm:
            model.SubmodelElementList("test_list", model.RelationshipElement, {are})
        self.assertEqual("All first level elements must be of the type specified in "
                         "type_value_list_element=RelationshipElement, got AnnotatedRelationshipElement[test] "
                         "(Constraint AASd-108)", str(cm.exception))
        model.SubmodelElementList("test_list", model.AnnotatedRelationshipElement, {are})

        # AASd-109
        # Pass an item to the constructor to assert that this constraint is checked before items are added.
        prop = model.Property("test", model.datatypes.Int, 0)
        with self.assertRaises(model.AASConstraintViolation) as cm:
            model.SubmodelElementList("test_list", model.Property, [prop])
        self.assertEqual("type_value_list_element=Property, but value_type_list_element is not set! "
                         "(Constraint AASd-109)", str(cm.exception))
        model.SubmodelElementList("test_list", model.Property, [prop], value_type_list_element=model.datatypes.Int)

        prop = model.Property("test_prop", model.datatypes.String)
        with self.assertRaises(model.AASConstraintViolation) as cm:
            model.SubmodelElementList("test_list", model.Property, {prop}, value_type_list_element=model.datatypes.Int)
        self.assertEqual("All first level elements must have the value_type specified by value_type_list_element=Int, "
                         "got Property[test_prop] with value_type=str (Constraint AASd-109)", str(cm.exception))
        model.SubmodelElementList("test_list", model.Property, {prop}, value_type_list_element=model.datatypes.String)

        # AASd-114
        semantic_id1 = model.GlobalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:test"),))
        semantic_id2 = model.GlobalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "urn:x-test:different"),))
        mlp1 = model.MultiLanguageProperty("mlp1", semantic_id=semantic_id1)
        mlp2 = model.MultiLanguageProperty("mlp2", semantic_id=semantic_id2)
        with self.assertRaises(model.AASConstraintViolation) as cm:
            model.SubmodelElementList("test_list", model.MultiLanguageProperty, [mlp1, mlp2])
        self.assertEqual("Element to be added MultiLanguageProperty[mlp2] has semantic_id "
                         "GlobalReference(key=(Key(type=GLOBAL_REFERENCE, value=urn:x-test:different),)), "
                         "while already contained element MultiLanguageProperty[test_list / mlp1] has semantic_id "
                         "GlobalReference(key=(Key(type=GLOBAL_REFERENCE, value=urn:x-test:test),)), "
                         "which aren't equal. (Constraint AASd-114)", str(cm.exception))
        mlp2.semantic_id = semantic_id1
        model.SubmodelElementList("test_list", model.MultiLanguageProperty, [mlp1, mlp2])

    def test_aasd_108_add_set(self):
        prop = model.Property("test", model.datatypes.Int)
        mlp1 = model.MultiLanguageProperty("mlp1")
        mlp2 = model.MultiLanguageProperty("mlp2")
        list_ = model.SubmodelElementList("test_list", model.MultiLanguageProperty)
        with self.assertRaises(model.AASConstraintViolation) as cm:
            list_.add_referable(prop)
        self.assertEqual("All first level elements must be of the type specified in type_value_list_element="
                         "MultiLanguageProperty, got Property[test] (Constraint AASd-108)", str(cm.exception))
        list_.add_referable(mlp1)

        with self.assertRaises(model.AASConstraintViolation) as cm:
            list_.value.add(prop)
        self.assertEqual("All first level elements must be of the type specified in type_value_list_element="
                         "MultiLanguageProperty, got Property[test] (Constraint AASd-108)", str(cm.exception))
        list_.value.add(mlp2)

        with self.assertRaises(model.AASConstraintViolation) as cm:
            list_.value[0] = prop
        self.assertEqual("All first level elements must be of the type specified in type_value_list_element="
                         "MultiLanguageProperty, got Property[test] (Constraint AASd-108)", str(cm.exception))
        del list_.value[1]
        list_.value[0] = mlp2

        with self.assertRaises(model.AASConstraintViolation) as cm:
            list_.value = [mlp1, prop]
        self.assertEqual("All first level elements must be of the type specified in type_value_list_element="
                         "MultiLanguageProperty, got Property[test] (Constraint AASd-108)", str(cm.exception))
        list_.value = [mlp1, mlp2]

    def test_immutable_attributes(self):
        list_ = model.SubmodelElementList("test_list", model.File)
        with self.assertRaises(AttributeError):
            list_.type_value_list_element = model.MultiLanguageProperty
        with self.assertRaises(AttributeError):
            list_.order_relevant = False
        with self.assertRaises(AttributeError):
            list_.semantic_id_list_element = model.GlobalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, "t"),))
        with self.assertRaises(AttributeError):
            list_.value_type_list_element = model.datatypes.Int


class BasicEventElementTest(unittest.TestCase):
    def test_constraints(self):
        with self.assertRaises(ValueError) as cm:
            model.BasicEventElement("test_basic_event_element",
                                    model.ModelReference((model.Key(model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                                                                    "urn:x-test:AssetAdministrationShell"),),
                                                         model.AssetAdministrationShell),
                                    model.Direction.INPUT,
                                    model.StateOfEvent.ON,
                                    max_interval=model.datatypes.Duration(minutes=10))
        self.assertEqual("max_interval is not applicable if direction = input!", str(cm.exception))
        bee = model.BasicEventElement("test_basic_event_element",
                                      model.ModelReference((model.Key(model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                                                                      "urn:x-test:AssetAdministrationShell"),),
                                                           model.AssetAdministrationShell),
                                      model.Direction.OUTPUT,
                                      model.StateOfEvent.ON,
                                      max_interval=model.datatypes.Duration(minutes=10))
        with self.assertRaises(ValueError) as cm:
            bee.direction = model.Direction.INPUT
        self.assertEqual("max_interval is not applicable if direction = input!", str(cm.exception))

        bee.max_interval = None
        bee.direction = model.Direction.INPUT

        timestamp_tzinfo = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456,
                                                    dateutil.tz.gettz("Europe/Berlin"))
        with self.assertRaises(ValueError) as cm:
            bee.last_update = timestamp_tzinfo
        self.assertEqual("last_update must be specified in UTC!", str(cm.exception))

        timestamp = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456)
        with self.assertRaises(ValueError) as cm:
            bee.last_update = timestamp
        self.assertEqual("last_update must be specified in UTC!", str(cm.exception))

        timestamp_tzinfo_utc = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456, dateutil.tz.UTC)
        bee.last_update = timestamp_tzinfo_utc


class EventPayloadTest(unittest.TestCase):
    def test_constraints(self):
        event_payload_obj = model.EventPayload(
            model.ModelReference((model.Key(model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                                            "urn:x-test:AssetAdministrationShell"),
                                  model.Key(model.KeyTypes.BASIC_EVENT_ELEMENT,
                                            "urn:x-test:EventElement")),
                                 model.EventElement),
            model.ModelReference((model.Key(model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                                            "urn:x-test:AssetAdministrationShell"),), model.AssetAdministrationShell),
            model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456, dateutil.tz.UTC)
        )

        timestamp_tzinfo = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456,
                                                    dateutil.tz.gettz("Europe/Berlin"))
        with self.assertRaises(ValueError) as cm:
            event_payload_obj.timestamp = timestamp_tzinfo
        self.assertEqual("timestamp must be specified in UTC!", str(cm.exception))

        timestamp = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456)
        with self.assertRaises(ValueError) as cm:
            event_payload_obj.timestamp = timestamp
        self.assertEqual("timestamp must be specified in UTC!", str(cm.exception))

        timestamp_tzinfo_utc = model.datatypes.DateTime(2022, 11, 13, 23, 45, 30, 123456, dateutil.tz.UTC)
        event_payload_obj.timestamp = timestamp_tzinfo_utc
