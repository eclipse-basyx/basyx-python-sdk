# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

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
