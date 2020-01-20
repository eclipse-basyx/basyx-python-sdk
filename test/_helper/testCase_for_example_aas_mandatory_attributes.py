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
Tests for the example aas mandatory attributes

Functions to test if an object is the same to the example aas mandatory attributes from
example_aas_mandatory_attributes.py
"""
import unittest
from typing import Optional

from aas import model
from aas.util import identification


class ExampleHelper(unittest.TestCase):
    def assert_example_asset(self, asset: model.Asset) -> None:
        # Test attributes of Asset
        self.assertEqual(model.AssetKind.INSTANCE, asset.kind)
        self.assertEqual('https://acplt.org/Test_Asset', asset.identification.id)
        self.assertEqual(model.IdentifierType.IRI, asset.identification.id_type)

    def assert_example_concept_description(self, concept_description: model.ConceptDescription) -> None:
        # Test attributes of ConceptDescription
        self.assertEqual('https://acplt.org/Test_ConceptDescription', concept_description.identification.id)
        self.assertEqual(model.IdentifierType.IRI, concept_description.identification.id_type)

    def assert_example_concept_dictionary(self, concept_dictionary: model.ConceptDictionary,
                                          shell: Optional[model.AssetAdministrationShell] = None) -> None:
        # Test attributes of ConceptDictionary
        self.assertEqual('TestConceptDictionary', concept_dictionary.id_short)
        if shell:
            self.assertEqual(concept_dictionary.parent, shell)
        else:
            self.assertIsNone(concept_dictionary.parent)

    def assert_example_asset_administration_shell(self, shell: model.AssetAdministrationShell) -> None:
        # Test attributes of AssetAdministrationShell
        self.assertEqual(shell.asset, model.AASReference((
            model.Key(type_=model.KeyElements.ASSET,
                      local=False,
                      value='https://acplt.org/Test_Asset',
                      id_type=model.KeyType.IRDI),),
            model.Asset))
        self.assertEqual('https://acplt.org/Test_AssetAdministrationShell', shell.identification.id)
        self.assertEqual(model.IdentifierType.IRI, shell.identification.id_type)
        self.assertEqual(2, len(shell.submodel_))
        self.assertEqual(True, identification.find_reference_in_set(model.AASReference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='https://acplt.org/Test_Submodel',
                      id_type=model.KeyType.IRDI),),
            model.Submodel),
            shell.submodel_))
        self.assertEqual(True, identification.find_reference_in_set(model.AASReference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='https://acplt.org/Test_Submodel2',
                      id_type=model.KeyType.IRDI),),
            model.Submodel),
            shell.submodel_))
        self.assertEqual(1, len(shell.concept_dictionary))
        cd: model.ConceptDictionary = shell.concept_dictionary.get_referable('TestConceptDictionary')  # type: ignore
        self.assert_example_concept_dictionary(cd, shell)

    def assert_example_empty_asset_administration_shell(self, shell: model.AssetAdministrationShell) -> None:
        # Test attributes of AssetAdministrationShell
        self.assertEqual(shell.asset, model.AASReference((
            model.Key(type_=model.KeyElements.ASSET,
                      local=False,
                      value='https://acplt.org/Test_Asset',
                      id_type=model.KeyType.IRDI),),
            model.Asset))
        self.assertEqual('https://acplt.org/Test_AssetAdministrationShell2', shell.identification.id)
        self.assertEqual(model.IdentifierType.IRI, shell.identification.id_type)
        self.assertEqual(0, len(shell.submodel_))
        self.assertEqual(0, len(shell.concept_dictionary))

    def assert_example_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('https://acplt.org/Test_Submodel', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(8, len(submodel.submodel_element))

        # test attributes of relationship element ExampleRelationshipElement
        rel_element: model.RelationshipElement = submodel.get_referable('ExampleRelationshipElement')  # type: ignore
        self.assertIsInstance(rel_element, model.RelationshipElement)
        self.assertEqual('ExampleRelationshipElement', rel_element.id_short)
        self.assertEqual(rel_element.first, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual(rel_element.second, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))

        # test attributes of annotated relationship element ExampleAnnotatedRelationshipElement
        rel_element_annotated: model.AnnotatedRelationshipElement = \
            submodel.get_referable('ExampleAnnotatedRelationshipElement')  # type: ignore
        self.assertIsInstance(rel_element_annotated, model.RelationshipElement)
        self.assertEqual('ExampleAnnotatedRelationshipElement', rel_element_annotated.id_short)
        self.assertEqual(rel_element_annotated.first, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual(rel_element_annotated.second, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))

        # test attributes of operation element ExampleOperation
        operation_element: model.Operation = submodel.get_referable('ExampleOperation')  # type: ignore
        self.assertIsInstance(operation_element, model.Operation)
        self.assertEqual('ExampleOperation', operation_element.id_short)

        # test attributes of capability element ExampleCapability
        capability_element: model.Capability = submodel.get_referable('ExampleCapability')  # type: ignore
        self.assertIsInstance(capability_element, model.Capability)
        self.assertEqual('ExampleCapability', capability_element.id_short)

        # test attributes of basic event element ExampleBasicEvent
        basic_event_element: model.BasicEvent = submodel.get_referable('ExampleBasicEvent')  # type: ignore
        self.assertIsInstance(basic_event_element, model.BasicEvent)
        self.assertEqual('ExampleBasicEvent', basic_event_element.id_short)
        self.assertEqual(basic_event_element.observed, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))

        # test attributes of ordered collection element ExampleSubmodelCollectionOrdered
        ordered_collection: model.SubmodelElementCollectionOrdered =\
            submodel.get_referable('ExampleSubmodelCollectionOrdered')  # type: ignore
        self.assertIsInstance(ordered_collection, model.SubmodelElementCollectionOrdered)
        self.assertEqual('ExampleSubmodelCollectionOrdered', ordered_collection.id_short)
        self.assertEqual(3, len(ordered_collection.value))

        # test attributes of elements of ExampleSubmodelCollectionOrdered
        # test attributes of property ExampleProperty
        example_property: model.Property = ordered_collection.get_referable('ExampleProperty')  # type: ignore
        self.assertIsInstance(example_property, model.Property)
        self.assertEqual('ExampleProperty', example_property.id_short)
        self.assertEqual('string', example_property.value_type)

        # test attributes of multi language property ExampleMultiLanguageProperty
        example_ml_property: model.MultiLanguageProperty = \
            ordered_collection.get_referable('ExampleMultiLanguageProperty')  # type: ignore
        self.assertIsInstance(example_ml_property, model.MultiLanguageProperty)
        self.assertEqual('ExampleMultiLanguageProperty', example_ml_property.id_short)

        # test attributes of range ExampleRange
        range_element: model.Range = ordered_collection.get_referable('ExampleRange')  # type: ignore
        self.assertIsInstance(range_element, model.Range)
        self.assertEqual('ExampleRange', range_element.id_short)
        self.assertEqual('int', range_element.value_type)

        # test attributes of unordered collection element ExampleSubmodelCollectionUnordered
        unordered_collection: model.SubmodelElementCollectionUnordered = \
            submodel.get_referable('ExampleSubmodelCollectionUnordered')  # type: ignore
        self.assertIsInstance(unordered_collection, model.SubmodelElementCollectionUnordered)
        self.assertEqual('ExampleSubmodelCollectionUnordered', unordered_collection.id_short)
        self.assertEqual(3, len(unordered_collection.value))

        # test attributes of blob ExampleBlob
        blob_element: model.Blob = unordered_collection.get_referable('ExampleBlob')  # type: ignore
        self.assertIsInstance(blob_element, model.Blob)
        self.assertEqual('ExampleBlob', blob_element.id_short)
        self.assertEqual('application/pdf', blob_element.mime_type)

        # test attributes of file ExampleFile
        file_element: model.File = unordered_collection.get_referable('ExampleFile')  # type: ignore
        self.assertIsInstance(file_element, model.File)
        self.assertEqual('ExampleFile', file_element.id_short)
        self.assertEqual('application/pdf', file_element.mime_type)

        # test attributes of reference element ExampleFile
        ref_element: model.ReferenceElement = \
            unordered_collection.get_referable('ExampleReferenceElement')  # type: ignore
        self.assertIsInstance(ref_element, model.ReferenceElement)
        self.assertEqual('ExampleReferenceElement', ref_element.id_short)

        # test attributes of empty collection element ExampleSubmodelCollectionUnordered2
        ordered_collection2: model.SubmodelElementCollectionOrdered = \
            submodel.get_referable('ExampleSubmodelCollectionUnordered2')  # type: ignore
        self.assertIsInstance(ordered_collection2, model.SubmodelElementCollectionUnordered)
        self.assertEqual('ExampleSubmodelCollectionUnordered2', ordered_collection2.id_short)
        self.assertEqual(0, len(ordered_collection2.value))

    def assert_example_empty_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('https://acplt.org/Test_Submodel2', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(0, len(submodel.submodel_element))

    def assert_full_example(self, obj_store: model.DictObjectStore) -> None:
        # separate different kind of objects
        submodels = []
        shells = []
        for obj in obj_store:
            if isinstance(obj, model.Asset):
                self.assert_example_asset(obj)
            elif isinstance(obj, model.AssetAdministrationShell):
                shells.append(obj)
            elif isinstance(obj, model.Submodel):
                submodels.append(obj)
            elif isinstance(obj, model.ConceptDescription):
                self.assert_example_concept_description(obj)
            else:
                raise KeyError()

        for submodel in submodels:
            if submodel.identification.id == 'https://acplt.org/Test_Submodel':
                self.assert_example_submodel(submodel)
            elif submodel.identification.id == 'https://acplt.org/Test_Submodel2':
                self.assert_example_empty_submodel(submodel)
            else:
                raise KeyError()

        for shell in shells:
            if shell.identification.id == 'https://acplt.org/Test_AssetAdministrationShell':
                self.assert_example_asset_administration_shell(shell)
            elif shell.identification.id == 'https://acplt.org/Test_AssetAdministrationShell2':
                self.assert_example_empty_asset_administration_shell(shell)
            else:
                raise KeyError()
