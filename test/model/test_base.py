
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

    def test_string_repr(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        self.assertIn("urn:x-test:aas1", repr(id1))
        self.assertIn("IRI", repr(id1))


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
        with self.assertRaises(ValueError):
            test_object.id_short = "98sdsfdAS"
        with self.assertRaises(ValueError):
            test_object.id_short = "_sdsfdAS"
        with self.assertRaises(ValueError):
            test_object.id_short = "asdlujSAD8348@S"
        with self.assertRaises(ValueError):
            test_object.id_short = None

    def test_id_short_constraint_aasd_001(self):
        test_object = ExampleIdentifiable()
        test_object.id_short = None
        self.assertEqual(None, test_object.id_short)


class ExampleNamespace(model.Namespace):
    def __init__(self, values=()):
        super().__init__()
        self.set1 = model.NamespaceSet(self, values)
        self.set2 = model.NamespaceSet(self)


class ModelNamespaceTest(unittest.TestCase):
    _namespace_class = ExampleNamespace

    def setUp(self):
        self.prop1 = model.Property("Prop1", "int")
        self.prop2 = model.Property("Prop2", "int")
        self.prop1alt = model.Property("Prop1", "int")
        self.namespace = self._namespace_class()

    def test_NamespaceSet(self) -> None:
        self.namespace.set1.add(self.prop1)
        self.namespace.set1.add(self.prop2)
        self.assertEqual(2, len(self.namespace.set1))
        self.assertIs(self.prop1, self.namespace.set1.get("Prop1"))
        self.assertIn(self.prop1, self.namespace.set1)
        self.assertNotIn(self.prop1alt, self.namespace.set1)
        self.assertIs(self.namespace, self.prop1.parent)

        with self.assertRaises(KeyError):
            self.namespace.set1.add(self.prop1alt)

        with self.assertRaises(KeyError):
            self.namespace.set1.add(self.prop1alt)

        with self.assertRaises(KeyError):
            self.namespace.set2.add(self.prop2)

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
        with self.assertRaises(KeyError):
            namespace_test = ExampleNamespace([self.prop1, self.prop2, self.prop1alt])
        self.assertIsNone(self.prop1.parent)

        namespace = self._namespace_class([self.prop1, self.prop2])
        self.assertIs(self.prop2, namespace.get_referable("Prop2"))
        with self.assertRaises(KeyError):
            namespace.get_referable("Prop3")


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
        with self.assertRaises(KeyError):
            self.namespace.set2.insert(0, self.prop1alt)
        self.assertEqual((self.prop2, self.prop1), tuple(self.namespace.set1))
        self.assertEqual(self.prop1, self.namespace.set1[1])

        with self.assertRaises(KeyError):
            self.namespace.set1[1] = self.prop2
        prop3 = model.Property("Prop3", "int")
        self.namespace.set1[1] = prop3
        self.assertEqual(2, len(self.namespace.set1))
        self.assertIsNone(self.prop1.parent)
        self.assertIs(self.namespace, prop3.parent)
        self.assertEqual((self.prop2, prop3), tuple(self.namespace.set1))

        del self.namespace.set1[0]
        self.assertIsNone(self.prop2.parent)
        self.assertEqual(1, len(self.namespace.set1))


class AASReferenceTest(unittest.TestCase):

    def test_reference_typing(self) -> None:
        dummy_submodel = model.Submodel(model.Identifier("urn:x-test:x", model.IdentifierType.IRI))

        class DummyRegistry(model.AbstractRegistry):
            def get_identifiable(self, identifier: Identifier) -> Identifiable:
                return dummy_submodel

        x = model.AASReference([model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI)],
                               model.Submodel)
        submodel: model.Submodel = x.resolve(DummyRegistry())
        self.assertIs(submodel, submodel)

    def test_resolve(self) -> None:
        prop = model.Property("prop", "int")
        collection = model.SubmodelElementCollectionUnordered("collection", {prop})
        prop.parent = collection
        submodel = model.Submodel(model.Identifier("urn:x-test:submodel", model.IdentifierType.IRI), {collection})
        collection.parent = submodel

        class DummyRegistry(model.AbstractRegistry):
            def get_identifiable(self, identifier: Identifier) -> Identifiable:
                if identifier == submodel.identification:
                    return submodel
                else:
                    raise KeyError()

        ref1 = model.AASReference([model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel", model.KeyType.IRI),
                                   model.Key(model.KeyElements.SUBMODEL_ELEMENT_COLLECTION, False, "collection",
                                             model.KeyType.IDSHORT),
                                   model.Key(model.KeyElements.PROPERTY, False, "prop", model.KeyType.IDSHORT)],
                                  model.Property)
        self.assertIs(prop, ref1.resolve(DummyRegistry()))

        ref1.key.append(model.Key(model.KeyElements.PROPERTY, False, "prop", model.KeyType.IDSHORT))
        # ref1.resolve should raise a type error now, b/c the Property (resolved by the 3rd key) is not a Namespace
        with self.assertRaises(TypeError):
            ref1.resolve(DummyRegistry())

        ref1.key[2].value = "prop1"
        # Oh no, a typo! We should get a KeyError when trying to find urn:x-test:submodel / collection / prop1
        with self.assertRaises(KeyError):
            ref1.resolve(DummyRegistry())

        ref2 = model.AASReference([model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:sub", model.KeyType.IRI)],
                                  model.Property)
        # Oh no, yet another typo!
        with self.assertRaises(KeyError):
            ref2.resolve(DummyRegistry())
        ref2.key[0].value = "urn:x-test:submodel"
        # Okay, typo is fixed, but the type is not what we expect. However, we should get the the submodel via the
        # exception's value attribute
        with self.assertRaises(model.UnexpectedTypeError) as cm:
            ref2.resolve(DummyRegistry())
        self.assertIs(submodel, cm.exception.value)
