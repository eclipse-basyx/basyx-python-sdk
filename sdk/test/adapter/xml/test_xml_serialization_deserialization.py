# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import io
import unittest

from basyx.aas import model
from basyx.aas.adapter.xml import (
    XMLConstructables,
    read_aas_xml_element,
    read_aas_xml_file,
    write_aas_xml_element,
    write_aas_xml_file,
)
from basyx.aas.examples.data import (
    create_example,
    example_aas,
    example_aas_mandatory_attributes,
    example_aas_missing_attributes,
    example_submodel_template,
)
from basyx.aas.examples.data._helper import AASDataChecker


def _serialize_and_deserialize(
    data: model.DictIdentifiableStore,
) -> model.DictIdentifiableStore:
    file = io.BytesIO()
    write_aas_xml_file(file=file, data=data)

    # try deserializing the xml document into a DictIdentifiableStore of AAS objects with help of the xml module
    file.seek(0)
    return read_aas_xml_file(file, failsafe=False)


class XMLSerializationDeserializationTest(unittest.TestCase):
    def test_example_serialization_deserialization(self) -> None:
        identifiable_store = _serialize_and_deserialize(
            example_aas.create_full_example()
        )
        checker = AASDataChecker(raise_immediately=True)
        example_aas.check_full_example(checker, identifiable_store)

    def test_example_mandatory_attributes_serialization_deserialization(self) -> None:
        identifiable_store = _serialize_and_deserialize(
            example_aas_mandatory_attributes.create_full_example()
        )
        checker = AASDataChecker(raise_immediately=True)
        example_aas_mandatory_attributes.check_full_example(checker, identifiable_store)

    def test_example_missing_attributes_serialization_deserialization(self) -> None:
        identifiable_store = _serialize_and_deserialize(
            example_aas_missing_attributes.create_full_example()
        )
        checker = AASDataChecker(raise_immediately=True)
        example_aas_missing_attributes.check_full_example(checker, identifiable_store)

    def test_example_submodel_template_serialization_deserialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_submodel_template.create_example_submodel_template())
        identifiable_store = _serialize_and_deserialize(data)
        checker = AASDataChecker(raise_immediately=True)
        example_submodel_template.check_full_example(checker, identifiable_store)

    def test_example_all_examples_serialization_deserialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = create_example()
        identifiable_store = _serialize_and_deserialize(data)
        checker = AASDataChecker(raise_immediately=True)
        checker.check_identifiable_store(identifiable_store, data)


class XMLSerializationDeserializationSingleObjectTest(unittest.TestCase):
    def test_submodel_serialization_deserialization(self) -> None:
        submodel: model.Submodel = (
            example_submodel_template.create_example_submodel_template()
        )
        bytes_io = io.BytesIO()
        write_aas_xml_element(bytes_io, submodel)
        bytes_io.seek(0)
        submodel2: model.Submodel = read_aas_xml_element(
            bytes_io,  # type: ignore[assignment]
            XMLConstructables.SUBMODEL,
            failsafe=False,
        )
        checker = AASDataChecker(raise_immediately=True)
        checker.check_submodel_equal(submodel2, submodel)


class XMLSerializationDeserializationFalsyValueTest(unittest.TestCase):
    def test_falsy_extension_and_qualifier_values(self) -> None:
        for value_type, value in ((model.datatypes.Int, 0),
                                  (model.datatypes.Decimal, model.datatypes.Decimal("0")),
                                  (model.datatypes.Boolean, False)):
            with self.subTest(value_type=value_type):
                submodel = model.Submodel(
                    "https://example.org/falsy",
                    extension=[model.Extension("e", value_type=value_type, value=value)],
                    qualifier=[model.Qualifier("q", value_type=value_type, value=value)],
                )
                read = _serialize_and_deserialize(model.DictIdentifiableStore([submodel])).get_item(
                    "https://example.org/falsy")
                assert isinstance(read, model.Submodel)
                self.assertEqual(value, read.get_extension_by_name("e").value)
                self.assertEqual(value, read.get_qualifier_by_type("q").value)
