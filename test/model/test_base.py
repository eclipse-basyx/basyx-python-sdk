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

import unittest

from aas import model
from aas.model import Identifier, Identifiable


class KeyTest(unittest.TestCase):
    def test_get_identifier(self):
        key1 = model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel1", model.KeyType.IRI)
        key2 = model.Key(model.KeyElements.PROPERTY, True, "prop1", model.KeyType.IDSHORT)
        self.assertEqual("urn:x-test:submodel1", key1.get_identifier().id)
        self.assertEqual(model.IdentifierType.IRI, key1.get_identifier().id_type)
        self.assertIsNone(key2.get_identifier())

    def test_string_representation(self):
        key1 = model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel1", model.KeyType.IRI)
        self.assertEqual("IRI=urn:x-test:submodel1", key1.__str__())

    def test_equality(self):
        key1 = model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel1", model.KeyType.IRI)
        ident = model.Identifier('test', model.IdentifierType.CUSTOM)
        self.assertEqual(key1.__eq__(ident), NotImplemented)


class IdentifierTest(unittest.TestCase):
    def test_equality_hashing(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        id2 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        id3 = model.Identifier("urn:x-test:aas1", model.IdentifierType.CUSTOM)
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

        ids = set()
        ids.add(id1)
        self.assertIn(id1, ids)
        self.assertIn(id2, ids)
        self.assertNotIn(id3, ids)

        key1 = model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel1", model.KeyType.IRI)
        self.assertEqual(id1.__eq__(key1), NotImplemented)

    def test_string_repr(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        self.assertIn("urn:x-test:aas1", repr(id1))
        self.assertIn("IRI", repr(id1))

    def test_set_identifier(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        with self.assertRaises(AttributeError) as cm:
            id1.id = 'test'
        self.assertEqual('Identifier are immutable', str(cm.exception))


class ExampleReferable(model.Referable):
    def __init__(self):
        super().__init__()


class ExampleIdentifiable(model.Identifiable):
    def __init__(self):
        super().__init__()


class ReferableTest(unittest.TestCase):
    def test_id_short_constraint_aasd_002(self):
        test_object = ExampleReferable()
        test_object.id_short = ""
        self.assertEqual("", test_object.id_short)
        test_object.id_short = "asdASd123_"
        self.assertEqual("asdASd123_", test_object.id_short)
        test_object.id_short = "AAs12_"
        self.assertEqual("AAs12_", test_object.id_short)
        with self.assertRaises(ValueError) as cm:
            test_object.id_short = "98sdsfdAS"
        self.assertEqual("The id_short must start with a letter", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            test_object.id_short = "_sdsfdAS"
        self.assertEqual("The id_short must start with a letter", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            test_object.id_short = "asdlujSAD8348@S"
        self.assertEqual("The id_short must contain only letters, digits and underscore", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            test_object.id_short = None
        self.assertEqual("The id_short for not identifiable elements is mandatory", str(cm.exception))

    def test_id_short_constraint_aasd_001(self):
        test_object = ExampleIdentifiable()
        test_object.id_short = None
        self.assertEqual(None, test_object.id_short)

    def test_representation(self):
        class DummyClass:
            def __init__(self, value: model.Referable):
                self.value: model.Referable = value

        ref = ExampleReferable()
        test_object = DummyClass(ref)
        ref.parent = test_object
        with self.assertRaises(AttributeError) as cm:
            ref.__repr__()
        self.assertEqual('Referable must have an identifiable as root object and only parents that are referable',
                         str(cm.exception))


class ExampleNamespace(model.Namespace):
    def __init__(self, values=()):
        super().__init__()
        self.set1 = model.NamespaceSet(self, values)
        self.set2 = model.NamespaceSet(self)


class ModelNamespaceTest(unittest.TestCase):
    _namespace_class = ExampleNamespace

    def setUp(self):
        self.prop1 = model.Property("Prop1", model.datatypes.Int)
        self.prop2 = model.Property("Prop2", model.datatypes.Int)
        self.prop1alt = model.Property("Prop1", model.datatypes.Int)
        self.namespace = self._namespace_class()

    def test_NamespaceSet(self) -> None:
        self.namespace.set1.add(self.prop1)
        self.namespace.set1.add(self.prop2)
        self.assertEqual(2, len(self.namespace.set1))
        self.assertIs(self.prop1, self.namespace.set1.get("Prop1"))
        self.assertIn(self.prop1, self.namespace.set1)
        self.assertNotIn(self.prop1alt, self.namespace.set1)
        self.assertIs(self.namespace, self.prop1.parent)

        with self.assertRaises(KeyError) as cm:
            self.namespace.set1.add(self.prop1alt)
        self.assertEqual('"Referable with id_short \'Prop1\' is already present in this set of objects"',
                         str(cm.exception))

        with self.assertRaises(KeyError) as cm:
            self.namespace.set2.add(self.prop2)
        self.assertEqual('"Referable with id_short \'Prop2\' is already present in another set in the same namespace"',
                         str(cm.exception))

        self.namespace.set1.remove(self.prop1)
        self.assertEqual(1, len(self.namespace.set1))
        self.assertIsNone(self.prop1.parent)
        self.namespace.set2.add(self.prop1alt)

        self.assertIs(self.prop2, self.namespace.set1.pop())
        self.assertEqual(0, len(self.namespace.set1))

        self.namespace.set2.clear()
        self.assertIsNone(self.prop1alt.parent)
        self.assertEqual(0, len(self.namespace.set2))

        self.namespace.set1.add(self.prop1)
        self.namespace.set1.discard(self.prop1)
        self.assertEqual(0, len(self.namespace.set1))
        self.assertIsNone(self.prop1.parent)
        self.namespace.set1.discard(self.prop1)

    def test_Namespace(self) -> None:
        with self.assertRaises(KeyError) as cm:
            namespace_test = ExampleNamespace([self.prop1, self.prop2, self.prop1alt])
        self.assertEqual('"Referable with id_short \'Prop1\' is already present in this set of objects"',
                         str(cm.exception))
        self.assertIsNone(self.prop1.parent)

        namespace = self._namespace_class([self.prop1, self.prop2])
        self.assertIs(self.prop2, namespace.get_referable("Prop2"))
        with self.assertRaises(KeyError) as cm:
            namespace.get_referable("Prop3")
        self.assertEqual("'Referable with id_short Prop3 not found in this namespace'", str(cm.exception))

    def test_add_and_remove(self):
        namespace2 = ExampleNamespace()
        namespace2.set1.add(self.prop1)
        with self.assertRaises(ValueError) as cm:
            self.namespace.set1.add(self.prop1)
        self.assertEqual('Object has already a parent, but it must not be part of two namespaces.', str(cm.exception))
        namespace2.set1.get_referable('Prop1')
        namespace2.set1.remove('Prop1')
        with self.assertRaises(KeyError) as cm:
            namespace2.set1.get_referable('Prop1')
        self.assertEqual("'Prop1'", str(cm.exception))


class ExampleOrderedNamespace(model.Namespace):
    def __init__(self, values=()):
        super().__init__()
        self.set1 = model.OrderedNamespaceSet(self, values)
        self.set2 = model.OrderedNamespaceSet(self)


class ModelOrderedNamespaceTest(ModelNamespaceTest):
    _namespace_class = ExampleOrderedNamespace  # type: ignore

    def test_OrderedNamespace(self) -> None:
        # Tests from ModelNamespaceTest are inherited, but with ExampleOrderedNamespace instead of ExampleNamespace
        # So, we only need to test order-related things here
        self.namespace.set1.add(self.prop1)
        self.namespace.set1.insert(0, self.prop2)
        with self.assertRaises(KeyError) as cm:
            self.namespace.set2.insert(0, self.prop1alt)
        self.assertEqual('"Referable with id_short \'Prop1\' is already present in another set in the same namespace"',
                         str(cm.exception))
        self.assertEqual((self.prop2, self.prop1), tuple(self.namespace.set1))
        self.assertEqual(self.prop1, self.namespace.set1[1])

        with self.assertRaises(KeyError) as cm:
            self.namespace.set1[1] = self.prop2
        self.assertEqual('"Referable with id_short \'Prop2\' is already present in this set of objects"',
                         str(cm.exception))
        prop3 = model.Property("Prop3", model.datatypes.Int)
        self.namespace.set1[1] = prop3
        self.assertEqual(2, len(self.namespace.set1))
        self.assertIsNone(self.prop1.parent)
        self.assertIs(self.namespace, prop3.parent)
        self.assertEqual((self.prop2, prop3), tuple(self.namespace.set1))

        del self.namespace.set1[0]
        self.assertIsNone(self.prop2.parent)
        self.assertEqual(1, len(self.namespace.set1))

        namespace2 = ExampleOrderedNamespace()
        namespace2.set1.add(self.prop1)
        namespace2.set1.get_referable('Prop1')
        namespace2.set1.remove('Prop1')
        with self.assertRaises(KeyError) as cm:
            namespace2.set1.get_referable('Prop1')
        self.assertEqual("'Prop1'", str(cm.exception))


class AASReferenceTest(unittest.TestCase):
    def test_set_reference(self):
        ref = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),),
                                 model.Submodel)
        with self.assertRaises(AttributeError) as cm:
            ref.type = model.Property
        self.assertEqual('Reference is immutable', str(cm.exception))
        with self.assertRaises(AttributeError) as cm:
            ref.key = model.Key(model.KeyElements.PROPERTY, False, "urn:x-test:x", model.KeyType.IRI)
        self.assertEqual('Reference is immutable', str(cm.exception))
        with self.assertRaises(AttributeError) as cm:
            ref.key = ()
        self.assertEqual('Reference is immutable', str(cm.exception))

    def test_equality(self):
        ref = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),),
                                 model.Submodel)
        ident = model.Identifier('test', model.IdentifierType.CUSTOM)
        self.assertEqual(ref.__eq__(ident), NotImplemented)
        ref_2 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),
                                    model.Key(model.KeyElements.PROPERTY, False, "test", model.KeyType.IRI)),
                                   model.Submodel)
        self.assertFalse(ref == ref_2)

    def test_reference_typing(self) -> None:
        dummy_submodel = model.Submodel(model.Identifier("urn:x-test:x", model.IdentifierType.IRI))

        class DummyObjectProvider(model.AbstractObjectProvider):
            def get_identifiable(self, identifier: Identifier) -> Identifiable:
                return dummy_submodel

        x = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),),
                               model.Submodel)
        submodel: model.Submodel = x.resolve(DummyObjectProvider())
        self.assertIs(submodel, submodel)

    def test_resolve(self) -> None:
        prop = model.Property("prop", model.datatypes.Int)
        collection = model.SubmodelElementCollectionUnordered("collection", {prop})
        prop.parent = collection
        submodel = model.Submodel(model.Identifier("urn:x-test:submodel", model.IdentifierType.IRI), {collection})
        collection.parent = submodel

        class DummyObjectProvider(model.AbstractObjectProvider):
            def get_identifiable(self, identifier: Identifier) -> Identifiable:
                if identifier == submodel.identification:
                    return submodel
                else:
                    raise KeyError()

        ref1 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel",
                                             model.KeyType.IRI),
                                   model.Key(model.KeyElements.SUBMODEL_ELEMENT_COLLECTION, False, "collection",
                                             model.KeyType.IDSHORT),
                                   model.Key(model.KeyElements.PROPERTY, False, "prop", model.KeyType.IDSHORT)),
                                  model.Property)
        self.assertIs(prop, ref1.resolve(DummyObjectProvider()))

        ref2 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel",
                                             model.KeyType.IRI),
                                   model.Key(model.KeyElements.SUBMODEL_ELEMENT_COLLECTION, False, "collection",
                                             model.KeyType.IDSHORT),
                                   model.Key(model.KeyElements.PROPERTY, False, "prop", model.KeyType.IDSHORT),
                                   model.Key(model.KeyElements.PROPERTY, False, "prop", model.KeyType.IDSHORT)),
                                  model.Property)
        with self.assertRaises(TypeError) as cm:
            ref2.resolve(DummyObjectProvider())
        self.assertEqual("Object retrieved at Identifier(IRI=urn:x-test:submodel) is not a Namespace",
                         str(cm.exception))

        with self.assertRaises(AttributeError) as cm_2:
            ref1.key[2].value = "prop1"
        self.assertEqual("Reference is immutable", str(cm_2.exception))

        ref3 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:sub", model.KeyType.IRI),),
                                  model.Property)
        # Oh no, yet another typo!
        with self.assertRaises(KeyError) as cm_3:
            ref3.resolve(DummyObjectProvider())
        self.assertEqual("'Could not resolve global reference key Identifier(IRI=urn:x-test:sub)'", str(cm_3.exception))

        ref4 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel",
                                             model.KeyType.IRI),),
                                  model.Property)
        # Okay, typo is fixed, but the type is not what we expect. However, we should get the the submodel via the
        # exception's value attribute
        with self.assertRaises(model.UnexpectedTypeError) as cm_4:
            ref4.resolve(DummyObjectProvider())
        self.assertIs(submodel, cm_4.exception.value)

        ref5 = model.AASReference((), model.Submodel)
        with self.assertRaises(IndexError) as cm_5:
            ref5.resolve(DummyObjectProvider())
        self.assertEqual('List of keys is empty', str(cm_5.exception))

    def test_from_referable(self) -> None:
        prop = model.Property("prop", model.datatypes.Int)
        collection = model.SubmodelElementCollectionUnordered("collection", {prop})
        prop.parent = collection
        submodel = model.Submodel(model.Identifier("urn:x-test:submodel", model.IdentifierType.IRI), {collection})
        collection.parent = submodel

        # Test normal usage for Identifiable and Referable objects
        ref1 = model.AASReference.from_referable(submodel)
        self.assertEqual(1, len(ref1.key))
        self.assertIs(ref1.type, model.Submodel)
        self.assertEqual("urn:x-test:submodel", ref1.key[0].value)
        self.assertEqual(model.KeyType.IRI, ref1.key[0].id_type)
        self.assertEqual(model.KeyElements.SUBMODEL, ref1.key[0].type)

        ref2 = model.AASReference.from_referable(prop)
        self.assertEqual(3, len(ref2.key))
        self.assertIs(ref2.type, model.Property)
        self.assertEqual("urn:x-test:submodel", ref2.key[0].value)
        self.assertEqual(model.KeyType.IRI, ref2.key[0].id_type)
        self.assertEqual("prop", ref2.key[2].value)
        self.assertEqual(model.KeyType.IDSHORT, ref2.key[2].id_type)
        self.assertEqual(model.KeyElements.PROPERTY, ref2.key[2].type)

        # Test exception for element without identifiable ancestor
        submodel.submodel_element.remove(collection)
        with self.assertRaises(ValueError) as cm:
            ref3 = model.AASReference.from_referable(prop)
        self.assertEqual("The given Referable object is not embedded within an Identifiable object", str(cm.exception))

        # Test creating a reference to a custom Referable class
        class DummyThing(model.Referable):
            def __init__(self, id_short: str):
                super().__init__()
                self.id_short = id_short

        class DummyIdentifyableNamespace(model.Identifiable, model.Namespace):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification
                self.things: model.NamespaceSet = model.NamespaceSet(self)

        thing = DummyThing("thing")
        identifable_thing = DummyIdentifyableNamespace(model.Identifier("urn:x-test:thing", model.IdentifierType.IRI))
        identifable_thing.things.add(thing)
        ref4 = model.AASReference.from_referable(thing)
        self.assertIs(ref4.type, model.Referable)


class AdministrativeInformationTest(unittest.TestCase):

    def test_setting_version_revision(self) -> None:
        with self.assertRaises(ValueError) as cm:
            obj = model.AdministrativeInformation(revision='0.9')
        self.assertEqual("A revision requires a version. This means, if there is no version there is no "
                         "revision neither.", str(cm.exception))

    def test_setting_revision(self) -> None:
        obj = model.AdministrativeInformation()
        with self.assertRaises(ValueError) as cm:
            obj.revision = '0.3'
        self.assertEqual("A revision requires a version. This means, if there is no version there is no revision "
                         "neither. Please set version first.", str(cm.exception))


class QualifierTest(unittest.TestCase):
    def test_set_value(self):
        qualifier = model.Qualifier('test', model.datatypes.Int, 2)
        self.assertEqual(qualifier.value, 2)
        qualifier.value = None
        self.assertIsNone(qualifier.value)


class ValueReferencePairTest(unittest.TestCase):
    def test_set_value(self):
        pair = model.ValueReferencePair(model.datatypes.Int, 2, model.Reference((model.Key(
            model.KeyElements.GLOBAL_REFERENCE, False, 'test', model.KeyType.CUSTOM),)))
        self.assertEqual(pair.value, 2)
        with self.assertRaises(AttributeError) as cm:
            pair.value = None
        self.assertEqual('Value can not be None', str(cm.exception))
        pair.value = 3
        self.assertEqual(pair.value, 3)
