
import unittest

from aas.util.identification import *
from aas import model


class IdentifierGeneratorTest(unittest.TestCase):
    def test_generate_uuid_identifier(self):
        generator = UUIDGenerator()
        identification = generator.generate_id()
        self.assertRegex(identification.id,
                         r"urn:uuid:[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}")
        ids = set()
        for i in range(100):
            identification = generator.generate_id()
            self.assertNotIn(identification, ids)
            ids.add(identification)

    def test_generate_iri_identifier(self):
        registry = model.DictObjectStore()

        # Check expected Errors when Namespaces are not valid
        with self.assertRaises(ValueError):
            generator = NamespaceIRIGenerator("", registry)
        with self.assertRaises(ValueError):
            generator = NamespaceIRIGenerator("http", registry)

        generator = NamespaceIRIGenerator("http://acplt.org/AAS/", registry)
        self.assertEqual("http://acplt.org/AAS/", generator.namespace)

        identification = generator.generate_id()
        self.assertEqual(identification.id, "http://acplt.org/AAS/0000")
        registry.add(model.Submodel(identification))

        for i in range(10):
            identification = generator.generate_id()
            self.assertNotIn(identification, registry)
            registry.add(model.Submodel(identification))
        self.assertEqual(identification.id, "http://acplt.org/AAS/0010")

        identification = generator.generate_id("Spülmaschine")
        self.assertEqual(identification.id, "http://acplt.org/AAS/Spülmaschine")
        registry.add(model.Submodel(identification))

        for i in range(10):
            identification = generator.generate_id("Spülmaschine")
            self.assertNotIn(identification, registry)
            self.assertNotEqual(identification.id, "http://acplt.org/AAS/Spülmaschine")
