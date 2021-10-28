# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0

import unittest

from aas import model


class ProvidersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.aas1 = model.AssetAdministrationShell(model.AssetInformation(),
                                                   model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI))
        self.aas2 = model.AssetAdministrationShell(model.AssetInformation(),
                                                   model.Identifier("urn:x-test:aas2", model.IdentifierType.IRI))
        self.submodel1 = model.Submodel(model.Identifier("urn:x-test:submodel1", model.IdentifierType.IRI))
        self.submodel2 = model.Submodel(model.Identifier("urn:x-test:submodel2", model.IdentifierType.IRI))

    def test_store_retrieve(self) -> None:
        object_store: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        object_store.add(self.aas1)
        object_store.add(self.aas2)
        self.assertIn(self.aas1, object_store)
        property = model.Property('test', model.datatypes.String)
        self.assertFalse(property in object_store)
        aas3 = model.AssetAdministrationShell(model.AssetInformation(),
                                              model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI))
        with self.assertRaises(KeyError) as cm:
            object_store.add(aas3)
        self.assertEqual("'Identifiable object with same identification Identifier(IRI=urn:x-test:aas1) is already "
                         "stored in this store'", str(cm.exception))
        self.assertEqual(2, len(object_store))
        self.assertIs(self.aas1,
                      object_store.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        self.assertIs(self.aas1,
                      object_store.get(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        object_store.discard(self.aas1)
        object_store.discard(self.aas1)
        with self.assertRaises(KeyError) as cm:
            object_store.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI))
        self.assertIsNone(object_store.get(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        self.assertEqual("Identifier(IRI=urn:x-test:aas1)", str(cm.exception))
        self.assertIs(self.aas2, object_store.pop())
        self.assertEqual(0, len(object_store))

    def test_store_update(self) -> None:
        object_store1: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        object_store1.add(self.aas1)
        object_store2: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        object_store2.add(self.aas2)
        object_store1.update(object_store2)
        self.assertIsInstance(object_store1, model.DictObjectStore)
        self.assertIn(self.aas2, object_store1)

    def test_provider_multiplexer(self) -> None:
        aas_object_store: model.DictObjectStore[model.AssetAdministrationShell] = model.DictObjectStore()
        aas_object_store.add(self.aas1)
        aas_object_store.add(self.aas2)
        submodel_object_store: model.DictObjectStore[model.Submodel] = model.DictObjectStore()
        submodel_object_store.add(self.submodel1)
        submodel_object_store.add(self.submodel2)

        multiplexer = model.ObjectProviderMultiplexer([aas_object_store, submodel_object_store])
        self.assertIs(self.aas1,
                      multiplexer.get_identifiable(model.Identifier("urn:x-test:aas1", model.IdentifierType.IRI)))
        self.assertIs(self.submodel1,
                      multiplexer.get_identifiable(model.Identifier("urn:x-test:submodel1", model.IdentifierType.IRI)))
        with self.assertRaises(KeyError) as cm:
            multiplexer.get_identifiable(model.Identifier("urn:x-test:submodel3", model.IdentifierType.IRI))
        self.assertEqual("'Identifier could not be found in any of the 2 consulted registries.'", str(cm.exception))
