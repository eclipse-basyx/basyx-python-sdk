# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0

import io
import json
import unittest

from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder, write_aas_json_file, read_aas_json_file

from basyx.aas.examples.data import example_concept_description, example_aas_missing_attributes, example_aas, \
    example_aas_mandatory_attributes, example_submodel_template, create_example
from basyx.aas.examples.data._helper import AASDataChecker


class JsonSerializationDeserializationTest(unittest.TestCase):
    def test_random_object_serialization_deserialization(self) -> None:
        asset_key = (model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM),)
        asset_reference = model.AASReference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = (model.Key(model.KeyElements.SUBMODEL, True, "SM1", model.KeyType.CUSTOM),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.AASReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel={submodel_reference})

        # serialize object to json
        json_data = json.dumps({
                'assetAdministrationShells': [test_aas],
                'submodels': [submodel],
                'assets': [],
                'conceptDescriptions': [],
            }, cls=AASToJsonEncoder)
        json_data_new = json.loads(json_data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        json_object_store = read_aas_json_file(io.StringIO(json_data), failsafe=False)

    def test_example_serialization_deserialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        example_aas.check_full_example(checker, json_object_store)


class JsonSerializationDeserializationTest2(unittest.TestCase):
    def test_example_mandatory_attributes_serialization_deserialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        example_aas_mandatory_attributes.check_full_example(checker, json_object_store)


class JsonSerializationDeserializationTest3(unittest.TestCase):
    def test_example_missing_attributes_serialization_deserialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)
        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        example_aas_missing_attributes.check_full_example(checker, json_object_store)


class JsonSerializationDeserializationTest4(unittest.TestCase):
    def test_example_submodel_template_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)
        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        example_submodel_template.check_full_example(checker, json_object_store)


class JsonSerializationDeserializationTest5(unittest.TestCase):
    def test_example_iec61360_concept_description_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_concept_description.create_iec61360_concept_description())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)
        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        example_concept_description.check_full_example(checker, json_object_store)


class JsonSerializationDeserializationTest6(unittest.TestCase):
    def test_example_all_examples_serialization_deserialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = create_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)
        # try deserializing the json string into a DictObjectStore of AAS objects with help of the json module
        file.seek(0)
        json_object_store = read_aas_json_file(file, failsafe=False)
        checker = AASDataChecker(raise_immediately=True)
        checker.check_object_store(json_object_store, data)
