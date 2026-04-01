import unittest

from app import model
from app.model.provider import DictDescriptorStore


class DictDescriptorStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_endpoint = model.Endpoint(
            interface="AAS-3.0", protocol_information=model.ProtocolInformation(href="https://example.org/")
        )
        self.aasd1 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self.aasd2 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/2", endpoints=[self.mock_endpoint]
        )
        self.sd1 = model.SubmodelDescriptor(
            id_="https://example.org/SubmodelDescriptor/1", endpoints=[self.mock_endpoint]
        )
        self.sd2 = model.SubmodelDescriptor(
            id_="https://example.org/SubmodelDescriptor/2", endpoints=[self.mock_endpoint]
        )

    def test_store_retrieve(self) -> None:
        descriptor_store: DictDescriptorStore = DictDescriptorStore()
        descriptor_store.add(self.aasd1)
        descriptor_store.add(self.aasd2)
        self.assertIn(self.aasd1, descriptor_store)
        self.assertFalse(self.sd1 in descriptor_store)

        aasd3 = model.AssetAdministrationShellDescriptor(
            id_="https://example.org/AASDescriptor/1", endpoints=[self.mock_endpoint]
        )
        with self.assertRaises(KeyError) as cm:
            descriptor_store.add(aasd3)
        self.assertEqual(
            "'Descriptor object with same id https://example.org/AASDescriptor/1 is already " "stored in this store'",
            str(cm.exception),
        )
        self.assertEqual(2, len(descriptor_store))
        self.assertIs(self.aasd1, descriptor_store.get("https://example.org/AASDescriptor/1"))

        descriptor_store.discard(self.aasd1)
        with self.assertRaises(KeyError) as cm:
            descriptor_store.get_item("https://example.org/AASDescriptor/1")
        self.assertIsNone(descriptor_store.get("https://example.org/AASDescriptor/1"))
        self.assertEqual("'https://example.org/AASDescriptor/1'", str(cm.exception))
        self.assertIs(self.aasd2, descriptor_store.pop())
        self.assertEqual(0, len(descriptor_store))

    def test_store_update(self) -> None:
        descriptor_store1: DictDescriptorStore = DictDescriptorStore()
        descriptor_store2: DictDescriptorStore = DictDescriptorStore()
        descriptor_store1.add(self.sd1)
        descriptor_store2.add(self.sd2)
        descriptor_store1.update(descriptor_store2)
        self.assertIsInstance(descriptor_store1, DictDescriptorStore)
        self.assertIn(self.sd2, descriptor_store1)
