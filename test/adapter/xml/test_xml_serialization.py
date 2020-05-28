# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import io
import unittest

from lxml import etree  # type: ignore

from aas import model
from aas.adapter.xml import write_aas_xml_file, xml_serialization, XML_SCHEMA_FILE

from aas.examples.data import example_aas_missing_attributes, example_submodel_template, \
    example_aas_mandatory_attributes, example_aas, example_concept_description


class XMLSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property("test_id_short",
                                     model.datatypes.String,
                                     category="PARAMETER",
                                     description={"en-us": "Germany", "de": "Deutschland"})
        xml_data = xml_serialization.property_to_xml(test_object,  xml_serialization.NS_AAS+"test_object")
        # todo: is this a correct way to test it?

    def test_random_object_serialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, True, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert (submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel_={submodel_reference})

        test_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        test_data.add(test_aas)
        test_data.add(submodel)

        test_file = io.BytesIO()
        write_aas_xml_file(file=test_file, data=test_data)


class XMLSerializationSchemaTest(unittest.TestCase):
    def test_random_object_serialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, True, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier, semantic_id=model.Reference((),))
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel_={submodel_reference})

        # serialize object to xml
        test_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        test_data.add(test_aas)
        test_data.add(submodel)

        test_file = io.BytesIO()
        write_aas_xml_file(file=test_file, data=test_data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        test_file.seek(0)
        root = etree.parse(test_file, parser=parser)

    def test_full_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        root = etree.parse(file, parser=parser)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        root = etree.parse(file, parser=parser)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        root = etree.parse(file, parser=parser)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        root = etree.parse(file, parser=parser)

    def test_concept_description(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_concept_description.create_iec61360_concept_description())
        file = io.BytesIO()
        write_aas_xml_file(file=file, data=data)

        # load schema
        aas_schema = etree.XMLSchema(file=XML_SCHEMA_FILE)

        # validate serialization against schema
        parser = etree.XMLParser(schema=aas_schema)
        file.seek(0)
        root = etree.parse(file, parser=parser)
