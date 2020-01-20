# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
Tests for the example concept description

Functions to test if an object is the same to the example concept description from example_concept_description.py
"""
import unittest
from typing import Optional

from aas import model
from aas.model.concept import IEC61360DataType, IEC61360LevelType
from aas.util import identification


class ExampleHelper(unittest.TestCase):
    def assert_example_iec61360_concept_description(self, cd: model.concept.IEC61360ConceptDescription) -> None:
        # Test attributes of concept description
        self.assertEqual('http://acplt.org/DataSpecifciations/Example/Identification', cd.identification.id)
        self.assertEqual(model.IdentifierType.IRI, cd.identification.id_type)
        self.assertEqual({'en-us': 'TestSpecification', 'de': 'Test Specification'}, cd.preferred_name)
        self.assertEqual(IEC61360DataType.REAL_MEASURE, cd.data_type)
        self.assertEqual({'en-us': 'This is a DataSpecification for testing purposes',
                          'de': 'Dies ist eine Data Specification für Testzwecke'}, cd.definition)
        self.assertEqual({'en-us': 'TestSpec', 'de': 'Test Spec'}, cd.short_name)
        self.assertEqual(1, len(cd.is_case_of))
        self.assertEqual(True, identification.find_reference_in_set(model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ReferenceElements/ConceptDescriptionX',
                      id_type=model.KeyType.IRDI),)), cd.is_case_of))
        self.assertEqual('TestSpec_01', cd.id_short)
        self.assertIsNone(cd.category)
        self.assertIsNone(cd.description)
        self.assertIsNone(cd.parent)
        self.assertEqual('0.9', cd.administration.version)  # type: ignore
        self.assertEqual('0', cd.administration.revision)  # type: ignore
        self.assertEqual('SpaceUnit', cd.unit)
        self.assertEqual(cd.unit_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Units/SpaceUnit',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual('http://acplt.org/DataSpec/ExampleDef', cd.source_of_definition)
        self.assertEqual('SU', cd.symbol)
        self.assertEqual('string', cd.value_format)
        self.assertEqual(2, len(cd.value_list))  # type: ignore
        reference_pair: model.ValueReferencePair
        for reference_pair in cd.value_list:  # type: ignore
            if reference_pair.value == 'exampleValue':
                self.assertIsInstance(reference_pair, model.ValueReferencePair)
                self.assertEqual('string', reference_pair.value_type)
                self.assertEqual(reference_pair.value_id, model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/ValueId/ExampleValueId',
                              id_type=model.KeyType.IRDI),)))
            elif reference_pair.value == 'exampleValue2':
                self.assertIsInstance(reference_pair, model.ValueReferencePair)
                self.assertEqual('string', reference_pair.value_type)
                self.assertEqual(reference_pair.value_id, model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/ValueId/ExampleValueId2',
                              id_type=model.KeyType.IRDI),)))
            else:
                raise KeyError()
        self.assertEqual('TEST', cd.value)
        self.assertIsNone(cd.value_id)
        self.assertEqual(2, len(cd.level_types))
        for leveltype in cd.level_types:  # type: ignore
            if leveltype == IEC61360LevelType.MIN:
                continue
            elif leveltype == IEC61360LevelType.MAX:
                continue
            else:
                raise KeyError()

    def assert_full_example(self, obj_store: model.DictObjectStore) -> None:
        # separate different kind of objects
        for obj in obj_store:
            if isinstance(obj, model.concept.IEC61360ConceptDescription):
                self.assert_example_iec61360_concept_description(obj)
            else:
                raise KeyError()
