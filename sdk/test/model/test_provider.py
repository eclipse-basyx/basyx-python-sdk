# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from basyx.aas import model


class ProvidersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.aas1 = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/TestAsset1/"), "urn:x-test:aas1")
        self.aas2 = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/TestAsset2/"), "urn:x-test:aas2")
        self.submodel1 = model.Submodel("urn:x-test:submodel1")
        self.submodel2 = model.Submodel("urn:x-test:submodel2")

    def test_store_retrieve(self) -> None:
        identifiable_store: model.DictIdentifiableStore[model.AssetAdministrationShell] = model.DictIdentifiableStore()
        identifiable_store.add(self.aas1)
        identifiable_store.add(self.aas2)
        self.assertIn(self.aas1, identifiable_store)
        property = model.Property('test', model.datatypes.String)
        self.assertFalse(property in identifiable_store)
        aas3 = model.AssetAdministrationShell(model.AssetInformation(global_asset_id="http://example.org/TestAsset/"),
                                              "urn:x-test:aas1")
        with self.assertRaises(KeyError) as cm:
            identifiable_store.add(aas3)
        self.assertEqual("'Identifiable object with same id urn:x-test:aas1 is already "
                         "stored in this store'", str(cm.exception))
        self.assertEqual(2, len(identifiable_store))
        self.assertIs(self.aas1,
                      identifiable_store.get_item("urn:x-test:aas1"))
        self.assertIs(self.aas1,
                      identifiable_store.get("urn:x-test:aas1"))
        identifiable_store.discard(self.aas1)
        identifiable_store.discard(self.aas1)
        with self.assertRaises(KeyError) as cm:
            identifiable_store.get_item("urn:x-test:aas1")
        self.assertIsNone(identifiable_store.get("urn:x-test:aas1"))
        self.assertEqual("'urn:x-test:aas1'", str(cm.exception))
        self.assertIs(self.aas2, identifiable_store.pop())
        self.assertEqual(0, len(identifiable_store))

    def test_store_update(self) -> None:
        identifiable_store1: model.DictIdentifiableStore[model.AssetAdministrationShell] = model.DictIdentifiableStore()
        identifiable_store1.add(self.aas1)
        identifiable_store2: model.DictIdentifiableStore[model.AssetAdministrationShell] = model.DictIdentifiableStore()
        identifiable_store2.add(self.aas2)
        identifiable_store1.update(identifiable_store2)
        self.assertIsInstance(identifiable_store1, model.DictIdentifiableStore)
        self.assertIn(self.aas2, identifiable_store1)

    def test_provider_multiplexer(self) -> None:
        aas_identifiable_store: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        aas_identifiable_store.add(self.aas1)
        aas_identifiable_store.add(self.aas2)
        submodel_identifiable_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        submodel_identifiable_store.add(self.submodel1)
        submodel_identifiable_store.add(self.submodel2)

        multiplexer: model.ObjectProviderMultiplexer[model.Identifier, model.Identifiable] = (
            model.ObjectProviderMultiplexer([aas_identifiable_store, submodel_identifiable_store])
        )
        self.assertIs(self.aas1, multiplexer.get_item("urn:x-test:aas1"))
        self.assertIs(self.submodel1, multiplexer.get_item("urn:x-test:submodel1"))
        with self.assertRaises(KeyError) as cm:
            multiplexer.get_item("urn:x-test:submodel3")
        self.assertEqual("'Key could not be found in any of the 2 consulted registries.'", str(cm.exception))
