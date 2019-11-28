
import unittest

from aas import model


class ExampleNamespace(model.Namespace):
    def __init__(self, values=()):
        super().__init__()
        self.set1 = model.NamespaceSet(self, values)
        self.set2 = model.NamespaceSet(self)


class ModelBaseTest(unittest.TestCase):
    def test_NamespaceSet(self):
        namespace = ExampleNamespace()
        prop1 = model.Property("Prop1", "int")
        prop2 = model.Property("Prop2", "int")
        prop1alt = model.Property("Prop1", "int")

        namespace.set1.add(prop1)
        namespace.set1.add(prop2)
        self.assertEqual(2, len(namespace.set1))
        self.assertIs(prop1, namespace.set1.get("Prop1"))
        self.assertIs(namespace, prop1.parent)

        with self.assertRaises(KeyError):
            namespace.set1.add(prop1alt)

        with self.assertRaises(KeyError):
            namespace.set1.add(prop1alt)

        with self.assertRaises(KeyError):
            namespace.set2.add(prop2)

        namespace.set1.remove(prop1)
        self.assertEqual(1, len(namespace.set1))
        self.assertIsNone(prop1.parent)
        namespace.set2.add(prop1alt)

    def test_Namespace(self):
        prop1 = model.Property("Prop1", "int")
        prop2 = model.Property("Prop2", "int")
        prop1alt = model.Property("Prop1", "int")

        with self.assertRaises(KeyError):
            namespace_test = ExampleNamespace([prop1, prop2, prop1alt])
        self.assertIsNone(prop1.parent)

        namespace = ExampleNamespace([prop1, prop2])
        self.assertIs(prop2, namespace.get_referable("Prop2"))
        with self.assertRaises(KeyError):
            namespace.get_referable("Prop3")
