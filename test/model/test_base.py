# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest
from unittest import mock
from typing import Optional, List

from basyx.aas import model
from basyx.aas.backend import backends
from basyx.aas.model import Identifier, Identifiable
from basyx.aas.examples.data import example_aas


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


class ExampleRefereableWithNamespace(model.Referable, model.Namespace):
    def __init__(self):
        super().__init__()


class MockBackend(backends.Backend):
    @classmethod
    def update_object(cls,
                      updated_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None: ...

    @classmethod
    def commit_object(cls,
                      committed_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None: ...

    update_object = mock.Mock()
    commit_object = mock.Mock()


class ExampleIdentifiable(model.Identifiable):
    def __init__(self):
        super().__init__()


def generate_example_referable_tree() -> model.Referable:
    """
    Generates an example referable tree, built like this:

        example_grandparent -> example_parent -> example_referable -> example_child -> example_grandchild
        example_grandparent and example_grandchild both have an nonempty source, pointing to the mock-backend

    :return: example_referable
    """
    def generate_example_referable_with_namespace(id_short: str,
                                                  child: Optional[model.Referable] = None) -> model.Referable:
        """
        Generates an example referable with a namespace.

        :param id_short: id_short of the referable created
        :param child: Child to be added to the namespace sets of the Referable
        :return: The generated Referable
        """
        referable = ExampleRefereableWithNamespace()
        referable.id_short = id_short
        if child:
            namespace_set = model.NamespaceSet(parent=referable, items=[child])
        return referable

    example_grandchild = generate_example_referable_with_namespace("exampleGrandchild")
    example_child = generate_example_referable_with_namespace("exampleChild", example_grandchild)
    example_referable = generate_example_referable_with_namespace("exampleReferable", example_child)
    example_parent = generate_example_referable_with_namespace("exampleParent", example_referable)
    example_grandparent = generate_example_referable_with_namespace("exampleGrandparent", example_parent)

    example_grandchild.source = "mockScheme:exampleGrandchild"
    example_grandparent.source = "mockScheme:exampleGrandparent"

    return example_referable


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
        with self.assertRaises(ValueError) as cm:
            test_object.id_short = "abc\n"
        self.assertEqual("The id_short must contain only letters, digits and underscore", str(cm.exception))

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

    def test_update(self):
        backends.register_backend("mockScheme", MockBackend)
        example_referable = generate_example_referable_tree()
        example_grandparent = example_referable.parent.parent
        example_grandchild = example_referable.get_referable("exampleChild").get_referable("exampleGrandchild")

        # Test update with parameter "recursive=False"
        example_referable.update(recursive=False)
        MockBackend.update_object.assert_called_once_with(
            updated_object=example_referable,
            store_object=example_grandparent,
            relative_path=["exampleGrandparent", "exampleParent", "exampleReferable"]
        )
        MockBackend.update_object.reset_mock()

        # Test update with parameter "recursive=True"
        example_referable.update()
        self.assertEqual(MockBackend.update_object.call_count, 2)
        MockBackend.update_object.assert_has_calls([
            mock.call(updated_object=example_referable,
                      store_object=example_grandparent,
                      relative_path=["exampleGrandparent", "exampleParent", "exampleReferable"]),
            mock.call(updated_object=example_grandchild,
                      store_object=example_grandchild,
                      relative_path=[])
        ])
        MockBackend.update_object.reset_mock()

        # Test update with source != "" in example_referable
        example_referable.source = "mockScheme:exampleReferable"
        example_referable.update(recursive=False)
        MockBackend.update_object.assert_called_once_with(
            updated_object=example_referable,
            store_object=example_referable,
            relative_path=[]
        )
        MockBackend.update_object.reset_mock()

        # Test update with no source available
        example_grandparent.source = ""
        example_referable.source = ""
        example_referable.update(recursive=False)
        MockBackend.update_object.assert_not_called()

    def test_commit(self):
        backends.register_backend("mockScheme", MockBackend)
        example_referable = generate_example_referable_tree()
        example_grandparent = example_referable.parent.parent
        example_grandchild = example_referable.get_referable("exampleChild").get_referable("exampleGrandchild")

        # Test commit starting from example_referable
        example_referable.commit()
        self.assertEqual(MockBackend.commit_object.call_count, 2)
        MockBackend.commit_object.assert_has_calls([
            mock.call(committed_object=example_referable,
                      store_object=example_grandparent,
                      relative_path=["exampleParent", "exampleReferable"]),
            mock.call(committed_object=example_grandchild,
                      store_object=example_grandchild,
                      relative_path=[])
        ])
        MockBackend.commit_object.reset_mock()

        # Test commit starting from example_grandchild
        example_grandchild.commit()
        self.assertEqual(MockBackend.commit_object.call_count, 2)
        MockBackend.commit_object.assert_has_calls([
            mock.call(committed_object=example_grandchild,
                      store_object=example_grandparent,
                      relative_path=["exampleParent", "exampleReferable", "exampleChild", "exampleGrandchild"]),
            mock.call(committed_object=example_grandchild,
                      store_object=example_grandchild,
                      relative_path=[])
        ])
        MockBackend.commit_object.reset_mock()

        # Test commit starting from example_grandchild after adding a source to example_referable
        example_referable.source = "mockScheme:exampleReferable"
        example_grandchild.commit()
        self.assertEqual(MockBackend.commit_object.call_count, 3)
        MockBackend.commit_object.assert_has_calls([
            mock.call(committed_object=example_grandchild,
                      store_object=example_referable,
                      relative_path=["exampleChild", "exampleGrandchild"]),
            mock.call(committed_object=example_grandchild,
                      store_object=example_grandparent,
                      relative_path=["exampleParent", "exampleReferable", "exampleChild", "exampleGrandchild"]),
            mock.call(committed_object=example_grandchild,
                      store_object=example_grandchild,
                      relative_path=[])
        ])

    def test_update_from(self):
        example_submodel = example_aas.create_example_submodel()
        example_relel = example_submodel.get_referable('ExampleRelationshipElement')

        other_submodel = example_aas.create_example_submodel()
        other_relel = other_submodel.get_referable('ExampleRelationshipElement')

        other_submodel.category = "NewCat"
        other_relel.category = "NewRelElCat"

        # Test basic functionality
        example_submodel.update_from(other_submodel)
        self.assertEqual("NewCat", example_submodel.category)
        self.assertEqual("NewRelElCat", example_relel.category)
        # References to Referable objects shall remain stable
        self.assertIs(example_relel, example_submodel.get_referable('ExampleRelationshipElement'))
        self.assertIs(example_relel, example_submodel.submodel_element.get('ExampleRelationshipElement'))
        # Check Namespace & parent consistency
        self.assertIs(example_submodel.namespace_element_sets[0], example_submodel.submodel_element)
        self.assertIs(example_relel.parent, example_submodel)

        # Test source update
        example_relel.source = "scheme:OldRelElSource"
        other_submodel.source = "scheme:NewSource"
        other_relel.source = "scheme:NewRelElSource"

        example_submodel.update_from(other_submodel)
        # Sources of the object itself should not be updated by default
        self.assertEqual("", example_submodel.source)
        # Sources of embedded objects should always be updated
        self.assertEqual("scheme:NewRelElSource", example_relel.source)


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

        namespace2 = self._namespace_class()
        with self.assertRaises(ValueError) as cm2:
            namespace2.set1.add(self.prop1)
        self.assertIn('has already a parent', str(cm2.exception))

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

        namespace.remove_referable("Prop2")
        with self.assertRaises(KeyError) as cm2:
            namespace.get_referable("Prop2")
            self.assertEqual("'Referable with id_short Prop2 not found in this namespace'", str(cm2.exception))

        with self.assertRaises(KeyError) as cm3:
            namespace.remove_referable("Prop2")
            self.assertEqual("'Referable with id_short Prop2 not found in this namespace'", str(cm3.exception))

    def test_renaming(self) -> None:
        self.namespace.set1.add(self.prop1)
        self.namespace.set1.add(self.prop2)

        self.prop1.id_short = "Prop3"
        self.assertEqual("Prop3", self.prop1.id_short)
        self.assertIs(self.prop1, self.namespace.get_referable('Prop3'))
        with self.assertRaises(KeyError):
            self.namespace.get_referable('Prop1')

        with self.assertRaises(KeyError) as cm:
            self.prop1.id_short = "Prop2"
        self.assertIn("already present", str(cm.exception))

    def test_Namespaceset_update_from(self) -> None:
        # Prop1 is getting its value updated by namespace2.set1
        # Prop2 is getting deleted since it does not exist in namespace2.set1
        # Prop3 is getting added, since it does not exist in namespace1.set1 yet
        namespace1 = self._namespace_class()
        prop1 = model.Property("Prop1", model.datatypes.Int, 1)
        prop2 = model.Property("Prop2", model.datatypes.Int, 0)
        namespace1.set1.add(prop1)
        namespace1.set1.add(prop2)
        namespace2 = self._namespace_class()
        namespace2.set1.add(model.Property("Prop1", model.datatypes.Int, 0))
        namespace2.set1.add(model.Property("Prop3", model.datatypes.Int, 2))
        namespace1.set1.update_nss_from(namespace2.set1)
        # Check that Prop1 got updated correctly
        self.assertIs(namespace1.get_referable("Prop1"), prop1)
        self.assertEqual(prop1.value, 0)
        self.assertIs(namespace1.get_referable("Prop1").parent, namespace1)
        # Check that Prop3 got added correctly
        prop3_new = namespace1.set1.get_referable("Prop3")
        self.assertIs(prop3_new.parent, namespace1)
        assert isinstance(prop3_new, model.Property)
        self.assertEqual(prop3_new.value, 2)
        # Check that Prop2 got removed correctly
        self.assertNotIn("Prop2", namespace1.set1)
        with self.assertRaises(KeyError):
            namespace1.get_referable("Prop2")
        self.assertIsNone(prop2.parent)


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
        self.assertEqual("Object retrieved at Identifier(IRI=urn:x-test:submodel) / collection / prop is not a "
                         "Namespace", str(cm.exception))

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

        with self.assertRaises(ValueError) as cm_5:
            ref5 = model.AASReference((), model.Submodel)
        self.assertEqual('A reference must have at least one key!', str(cm_5.exception))

        ref6 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:submodel",
                                             model.KeyType.IRI),
                                   model.Key(model.KeyElements.SUBMODEL_ELEMENT_COLLECTION, False, "collection",
                                             model.KeyType.IDSHORT),
                                   model.Key(model.KeyElements.PROPERTY, False, "prop_false",
                                             model.KeyType.IDSHORT)), model.Property)

        with self.assertRaises(KeyError) as cm_6:
            ref6.resolve(DummyObjectProvider())
            self.assertEqual("'Could not resolve id_short prop_false at Identifier(IRI=urn:x-test:submodel)'",
                             str(cm_6.exception))

    def test_get_identifier(self) -> None:
        ref = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),),
                                 model.Submodel)
        self.assertEqual(model.Identifier("urn:x-test:x", model.IdentifierType.IRI), ref.get_identifier())

        ref2 = model.AASReference((model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),
                                   model.Key(model.KeyElements.PROPERTY, False, "myProperty", model.KeyType.IDSHORT),),
                                  model.Submodel)
        self.assertEqual(model.Identifier("urn:x-test:x", model.IdentifierType.IRI), ref.get_identifier())

        # People will do strange things ...
        ref3 = model.AASReference((model.Key(model.KeyElements.ASSET_ADMINISTRATION_SHELL, False, "urn:x-test-aas:x",
                                             model.KeyType.IRI),
                                   model.Key(model.KeyElements.SUBMODEL, False, "urn:x-test:x", model.KeyType.IRI),),
                                  model.Submodel)
        self.assertEqual(model.Identifier("urn:x-test:x", model.IdentifierType.IRI), ref2.get_identifier())

        ref4 = model.AASReference((model.Key(model.KeyElements.PROPERTY, False, "myProperty", model.KeyType.IDSHORT),),
                                  model.Property)
        with self.assertRaises(ValueError):
            ref4.get_identifier()

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
