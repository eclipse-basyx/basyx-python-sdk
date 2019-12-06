
import unittest

from aas import model


class RegistriesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.aas1 = model.AssetAdministrationShell(model.AASReference([], model.Asset),
                                                   model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI))
        self.aas2 = model.AssetAdministrationShell(model.AASReference([], model.Asset),
                                                   model.Identifier("urn:x-test:aas2", model.IdentifierType.IRI))
        self.submodel1 = model.Submodel(model.Identifier("urn:x-test:submodel1", model.IdentifierType.IRI))
        self.submodel2 = model.Submodel(model.Identifier("urn:x-test:submodel2", model.IdentifierType.IRI))

    def test_store_retrieve(self) -> None:
        object_store: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        object_store.add(self.aas1)
        object_store.add(self.aas2)
        self.assertEqual(2, len(object_store))
        self.assertIs(self.aas1,
                      object_store.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        object_store.remove(self.aas1)
        with self.assertRaises(KeyError):
            object_store.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI))
        self.assertIs(self.aas2, object_store.pop())
        self.assertEqual(0, len(object_store))

    def test_registry_multiplexer(self) -> None:
        aas_object_store: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        aas_object_store.add(self.aas1)
        aas_object_store.add(self.aas2)
        submodel_object_store: model.DictObjectStore[model.Submodel] = model.DictObjectStore()
        submodel_object_store.add(self.submodel1)
        submodel_object_store.add(self.submodel2)

        multiplexer = model.RegistryMultiplexer([aas_object_store, submodel_object_store])
        self.assertIs(self.aas1,
                      multiplexer.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        self.assertIs(self.submodel1,
                      multiplexer.get_identifiable(model.Identifier("urn:x-test:submodel1", model.IdentifierType.IRI)))
        with self.assertRaises(KeyError):
            multiplexer.get_identifiable(model.Identifier("urn:x-test:submodel3", model.IdentifierType.IRI))
