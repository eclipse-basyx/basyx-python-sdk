
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
    def test_equality(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        id2 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        id3 = model.Identifier("urn:x-test:aas1", model.IdentifierType.CUSTOM)
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

    def test_string_repr(self):
        id1 = model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)
        self.assertIn("urn:x-test:aas1", repr(id1))
        self.assertIn("IRI", repr(id1))


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

    def test_NamespaceSet(self):
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

    def test_Namespace(self):
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

    def test_OrderedNamespace(self):
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


class ReferenceTest(unittest.TestCase):

    def test_reference_typing(self):
        class DefaultProperty(model.Property):
            def __init__(self):
                super().__init__("an_id", "int")

        x = model.Reference([], DefaultProperty)
        p: model.Property = x.resolve()
