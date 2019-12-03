
import unittest

from aas.util.identification import *


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
        with self.assertRaises(ValueError):
            generator = IRIGeneratorInGivenNamespace("")
        generator = IRIGeneratorInGivenNamespace("http://acplt.org/AAS")
        identification = generator.generate_id()
        self.assertEqual(identification.id, "http://acplt.org/AAS/1")
        for i in range(99):
            identification = generator.generate_id()
        self.assertEqual(identification.id, "http://acplt.org/AAS/100")
