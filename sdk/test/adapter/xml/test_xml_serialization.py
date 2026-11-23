# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import io
import os
import unittest

from basyx.aas import model
from basyx.aas.adapter.xml import write_aas_xml_file, xml_serialization
from basyx.aas.examples.data import (
    example_aas,
    example_aas_mandatory_attributes,
    example_aas_missing_attributes,
    example_submodel_template,
)
from lxml import etree

from test._helper.test_helpers import REQUIRE_SCHEMAS

XML_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "../schemas/aasXMLSchema.xsd")


class XMLSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property(
            "test_id_short",
            model.datatypes.String,
            category="PARAMETER",
            description=model.MultiLanguageTextType(
                {"en-US": "Germany", "de": "Deutschland"}
            ),
        )
        xml_serialization.property_to_xml(
            test_object, xml_serialization.NS_AAS + "test_object"
        )
        # todo: is this a correct way to test it?

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="Test"),
            aas_identifier,
            submodel={submodel_reference},
        )

        test_data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        test_data.add(test_aas)
        test_data.add(submodel)

        test_file = io.BytesIO()
        write_aas_xml_file(file=test_file, data=test_data)

    def test_submodel_list_elements_idShort_ok(self) -> None:
        """Verify, that adding SE to a SML does not mess with their idShorts in any serialization"""
        prop1 = model.Property(id_short=None, value_type=model.datatypes.String, value="WithoutIdShort")
        prop2 = model.Property(id_short="exampleIdShort", value_type=model.datatypes.String, value="WithIdShort")
        sml = model.SubmodelElementList(
            id_short="exampleList",
            type_value_list_element=model.Property,
            value_type_list_element=model.datatypes.String,
            value=[prop1, prop2],
        )

        xml1 = xml_serialization.object_to_xml_element(prop1)
        xml2 = xml_serialization.object_to_xml_element(prop2)
        xml_sml = xml_serialization.object_to_xml_element(sml)

        self.assertIsNone(xml1.find(xml_serialization.NS_AAS + "idShort"))
        self.assertEqual("exampleIdShort", xml2.findtext(xml_serialization.NS_AAS + "idShort"))

        sml_items = xml_sml.find(xml_serialization.NS_AAS + "value")
        assert sml_items is not None
        self.assertIsNone(
            sml_items[0].find(xml_serialization.NS_AAS + "idShort")
        )
        self.assertEqual(
            "exampleIdShort",
            sml_items[1].findtext(xml_serialization.NS_AAS + "idShort"),
        )


class XMLSerializationSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(XML_SCHEMA_FILE):
            if REQUIRE_SCHEMAS:
                raise RuntimeError(
                    f"REQUIRE_SCHEMA_TESTS is set, but the XSD schema does not exist at {XML_SCHEMA_FILE}"
                )
            raise unittest.SkipTest(
                f"XSD schema does not exist at {XML_SCHEMA_FILE}, skipping test"
            )

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(
            submodel_identifier,
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        model.KeyTypes.GLOBAL_REFERENCE,
                        "http://example.org/TestSemanticId",
                    ),
                )
            ),
        )
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="Test"),
            aas_identifier,
            submodel={submodel_reference},
        )
        # serialize object to xml
        test_data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        test_data.add(test_aas)
        test_data.add(submodel)

        test_file = io.BytesIO()
        write_aas_xml_file(file=test_file, data=test_data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        test_file.seek(0)
        etree.parse(test_file, parser=parser)

    def test_full_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        etree.parse(file, parser=parser)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        etree.parse(file, parser=parser)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        etree.parse(file, parser=parser)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data, pretty_print=True)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        etree.parse(file, parser=parser)

    def test_concept_description(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_aas.create_example_concept_description())
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        etree.parse(file, parser=parser)
