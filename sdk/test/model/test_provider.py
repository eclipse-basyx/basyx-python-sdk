# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from basyx.aas import model


class ProvidersTest(unittest.TestCase):
    _STORE_CLASSES = (model.DictIdentifiableStore, model.SetIdentifiableStore)

    def setUp(self) -> None:
        self.aas1 = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/TestAsset1/"), "urn:x-test:aas1")
        self.aas2 = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/TestAsset2/"), "urn:x-test:aas2")
        self.submodel1 = model.Submodel("urn:x-test:submodel1")
        self.submodel2 = model.Submodel("urn:x-test:submodel2")

    def test_store_retrieve(self) -> None:
        for store_class in self._STORE_CLASSES:
            with self.subTest(store=store_class.__name__):
                store: model.AbstractObjectStore[model.Identifier, model.Identifiable] = store_class([self.aas1])
                store.add(self.aas2)

                store.add(self.aas1)
                self.assertEqual(2, len(store))

                self.assertIn(self.aas1, store)
                self.assertIn("urn:x-test:aas1", store)
                self.assertNotIn("urn:x-test:missing", store)
                property = model.Property('test', model.datatypes.String)
                self.assertFalse(property in store)
                aas3 = model.AssetAdministrationShell(
                    model.AssetInformation(global_asset_id="http://example.org/TestAsset/"), "urn:x-test:aas1")
                with self.assertRaises(KeyError) as cm:
                    store.add(aas3)
                self.assertEqual("'Identifiable object with same id urn:x-test:aas1 is already "
                                 "stored in this store'", str(cm.exception))
                self.assertEqual(2, len(store))
                self.assertIs(self.aas1, store.get_item("urn:x-test:aas1"))
                self.assertIs(self.aas1, store.get("urn:x-test:aas1"))
                store.discard(self.aas1)
                store.discard(self.aas1)
                with self.assertRaises(KeyError) as cm:
                    store.get_item("urn:x-test:aas1")
                self.assertIsNone(store.get("urn:x-test:aas1"))
                self.assertEqual("'urn:x-test:aas1'", str(cm.exception))
                self.assertIs(self.aas2, store.pop())
                self.assertEqual(0, len(store))

    def test_store_update(self) -> None:
        for store_class in self._STORE_CLASSES:
            with self.subTest(store=store_class.__name__):
                store1: model.AbstractObjectStore[model.Identifier, model.Identifiable] = store_class()
                store1.add(self.aas1)
                store2: model.AbstractObjectStore[model.Identifier, model.Identifiable] = store_class()
                store2.add(self.aas2)
                store1.update(store2)
                self.assertIsInstance(store1, store_class)
                self.assertIn(self.aas2, store1)

    def test_store_sync(self) -> None:
        for store_class in self._STORE_CLASSES:
            with self.subTest(store=store_class.__name__):
                store: model.AbstractObjectStore[model.Identifier, model.Identifiable] = store_class()
                self.assertEqual(store.sync([self.aas1, self.aas2], overwrite=False), (2, 0, 0))
                self.assertIn(self.aas1, store)
                self.assertIn(self.aas2, store)

                self.assertEqual(store.sync([self.aas1], overwrite=False), (0, 0, 1))

                self.assertEqual(store.sync([self.aas1], overwrite=True), (0, 1, 0))
                self.assertIn(self.aas1, store)

                self.assertEqual(store.sync([self.aas1, self.submodel1], overwrite=True), (1, 1, 0))

                self.assertEqual(store.sync([self.aas1, self.submodel2], overwrite=False), (1, 0, 1))

                self.assertEqual(store.sync([], overwrite=False), (0, 0, 0))

    def test_store_remove(self) -> None:
        for store_class in self._STORE_CLASSES:
            with self.subTest(store=store_class.__name__):
                store: model.AbstractObjectStore[model.Identifier, model.Identifiable] = store_class()
                store.add(self.aas1)
                store.remove(self.aas1)
                self.assertEqual(0, len(store))
                with self.assertRaises(KeyError):
                    store.remove(self.aas1)

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
