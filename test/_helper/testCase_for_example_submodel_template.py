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
Tests for the example submodel template

Functions to test if an object is the same to the example submodel template from example_submodel_template.py
"""
import unittest
from typing import Optional

from aas import model
from aas.util import identification


class ExampleHelper(unittest.TestCase):
    def assert_example_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('https://acplt.org/Test_Submodel', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(8, len(submodel.submodel_element))
        self.assertEqual('TestSubmodel', submodel.id_short)
        self.assertIsNone(submodel.category)
        self.assertEqual({'en-us': 'An example submodel for the test application',
                          'de': 'Ein Beispiel-Teilmodell für eine Test-Anwendung'}, submodel.description)
        self.assertIsNone(submodel.parent)
        self.assertEqual('0.9', submodel.administration.version)  # type: ignore
        self.assertEqual('0', submodel.administration.revision)  # type: ignore
        self.assertEqual(submodel.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelTemplates/ExampleSubmodel',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(submodel.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, submodel.kind)

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
        self.assertEqual('PARAMETER', rel_element.category)
        self.assertEqual({'en-us': 'Example RelationshipElement object', 'de': 'Beispiel RelationshipElement Element'},
                         rel_element.description)
        self.assertIs(rel_element.parent, submodel)
        self.assertEqual(rel_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/RelationshipElements/ExampleRelationshipElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(rel_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, rel_element.kind)

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
        self.assertEqual(0, len(rel_element_annotated.annotation))
        self.assertEqual('PARAMETER', rel_element_annotated.category)
        self.assertEqual({'en-us': 'Example AnnotatedRelationshipElement object',
                          'de': 'Beispiel AnnotatedRelationshipElement Element'}, rel_element_annotated.description)
        self.assertIs(rel_element_annotated.parent, submodel)
        self.assertEqual(rel_element_annotated.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/RelationshipElements/ExampleAnnotatedRelationshipElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(rel_element_annotated.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, rel_element_annotated.kind)

        # test attributes of operation element ExampleOperation
        operation_element: model.Operation = submodel.get_referable('ExampleOperation')  # type: ignore
        self.assertIsInstance(operation_element, model.Operation)
        self.assertEqual('ExampleOperation', operation_element.id_short)
        self.assertEqual(1, len(operation_element.input_variable))
        self.assertEqual(1, len(operation_element.output_variable))
        self.assertEqual(1, len(operation_element.in_output_variable))
        self.assertEqual('PARAMETER', operation_element.category)
        self.assertEqual({'en-us': 'Example Operation object',
                          'de': 'Beispiel Operation Element'}, operation_element.description)
        self.assertIs(operation_element.parent, submodel)
        self.assertEqual(operation_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Operations/ExampleOperation',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(operation_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, operation_element.kind)

        # test attributes of capability element ExampleCapability
        capability_element: model.Capability = submodel.get_referable('ExampleCapability')  # type: ignore
        self.assertIsInstance(capability_element, model.Capability)
        self.assertEqual('ExampleCapability', capability_element.id_short)
        self.assertEqual('PARAMETER', capability_element.category)
        self.assertEqual({'en-us': 'Example Capability object',
                          'de': 'Beispiel Capability Element'}, capability_element.description)
        self.assertIs(capability_element.parent, submodel)
        self.assertEqual(capability_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Capabilities/ExampleCapability',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(capability_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, capability_element.kind)

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
        self.assertEqual('PARAMETER', basic_event_element.category)
        self.assertEqual({'en-us': 'Example BasicEvent object',
                          'de': 'Beispiel BasicEvent Element'}, basic_event_element.description)
        self.assertIs(basic_event_element.parent, submodel)
        self.assertEqual(basic_event_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Events/ExampleBasicEvent',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(basic_event_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, basic_event_element.kind)

        # test attributes of ordered collection element ExampleSubmodelCollectionOrdered
        ordered_collection: model.SubmodelElementCollectionOrdered =\
            submodel.get_referable('ExampleSubmodelCollectionOrdered')  # type: ignore
        self.assertIsInstance(ordered_collection, model.SubmodelElementCollectionOrdered)
        self.assertEqual('ExampleSubmodelCollectionOrdered', ordered_collection.id_short)
        self.assertEqual(4, len(ordered_collection.value))
        self.assertEqual('PARAMETER', ordered_collection.category)
        self.assertEqual({'en-us': 'Example SubmodelElementCollectionOrdered object',
                          'de': 'Beispiel SubmodelElementCollectionOrdered Element'}, ordered_collection.description)
        self.assertIs(ordered_collection.parent, submodel)
        self.assertEqual(ordered_collection.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelElementCollections/ExampleSubmodelElementCollectionOrdered',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(ordered_collection.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, ordered_collection.kind)

        # test attributes of elements of ExampleSubmodelCollectionOrdered
        # test attributes of property ExampleProperty
        example_property: model.Property = ordered_collection.get_referable('ExampleProperty')  # type: ignore
        self.assertIsInstance(example_property, model.Property)
        self.assertEqual('ExampleProperty', example_property.id_short)
        self.assertEqual('string', example_property.value_type)
        self.assertIsNone(example_property.value)
        self.assertIsNone(example_property.value_id)
        self.assertEqual('CONSTANT', example_property.category)
        self.assertEqual({'en-us': 'Example Property object', 'de': 'Beispiel Property Element'},
                         example_property.description)
        self.assertIs(example_property.parent, ordered_collection)
        self.assertEqual(example_property.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Properties/ExampleProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_property.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, example_property.kind)

        # test attributes of multi language property ExampleMultiLanguageProperty
        example_ml_property: model.MultiLanguageProperty = \
            ordered_collection.get_referable('ExampleMultiLanguageProperty')  # type: ignore
        self.assertIsInstance(example_ml_property, model.MultiLanguageProperty)
        self.assertEqual('ExampleMultiLanguageProperty', example_ml_property.id_short)
        self.assertIsNone(example_ml_property.value)
        self.assertIsNone(example_ml_property.value_id)
        self.assertEqual('CONSTANT', example_ml_property.category)
        self.assertEqual({'en-us': 'Example MultiLanguageProperty object',
                          'de': 'Beispiel MulitLanguageProperty Element'},
                         example_ml_property.description)
        self.assertIs(example_ml_property.parent, ordered_collection)
        self.assertEqual(example_ml_property.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/MultiLanguageProperties/ExampleMultiLanguageProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_ml_property.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, example_ml_property.kind)

        # test attributes of range ExampleRange
        range_element: model.Range = ordered_collection.get_referable('ExampleRange')  # type: ignore
        self.assertIsInstance(range_element, model.Range)
        self.assertEqual('ExampleRange', range_element.id_short)
        self.assertEqual('int', range_element.value_type)
        self.assertIsNone(range_element.min_)
        self.assertEqual('100', range_element.max_)
        self.assertEqual('PARAMETER', range_element.category)
        self.assertEqual({'en-us': 'Example Range object', 'de': 'Beispiel Range Element'},
                         range_element.description)
        self.assertIs(range_element.parent, ordered_collection)
        self.assertEqual(range_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Ranges/ExampleRange',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(range_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, range_element.kind)

        # test attributes of range ExampleRange2
        range_element2: model.Range = ordered_collection.get_referable('ExampleRange2')  # type: ignore
        self.assertIsInstance(range_element2, model.Range)
        self.assertEqual('ExampleRange2', range_element2.id_short)
        self.assertEqual('int', range_element2.value_type)
        self.assertEqual('0', range_element2.min_)
        self.assertIsNone(range_element2.max_)
        self.assertEqual('PARAMETER', range_element2.category)
        self.assertEqual({'en-us': 'Example Range object', 'de': 'Beispiel Range Element'},
                         range_element2.description)
        self.assertIs(range_element2.parent, ordered_collection)
        self.assertEqual(range_element2.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Ranges/ExampleRange',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(range_element2.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, range_element2.kind)

        # test attributes of unordered collection element ExampleSubmodelCollectionUnordered
        unordered_collection: model.SubmodelElementCollectionUnordered = \
            submodel.get_referable('ExampleSubmodelCollectionUnordered')  # type: ignore
        self.assertIsInstance(unordered_collection, model.SubmodelElementCollectionUnordered)
        self.assertEqual('ExampleSubmodelCollectionUnordered', unordered_collection.id_short)
        self.assertEqual(3, len(unordered_collection.value))
        self.assertEqual('PARAMETER', unordered_collection.category)
        self.assertEqual({'en-us': 'Example SubmodelElementCollectionUnordered object',
                          'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
                         unordered_collection.description)
        self.assertIs(unordered_collection.parent, submodel)
        self.assertEqual(unordered_collection.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelElementCollections/ExampleSubmodelElementCollectionUnordered',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(unordered_collection.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, unordered_collection.kind)

        # test attributes of blob ExampleBlob
        blob_element: model.Blob = unordered_collection.get_referable('ExampleBlob')  # type: ignore
        self.assertIsInstance(blob_element, model.Blob)
        self.assertEqual('ExampleBlob', blob_element.id_short)
        self.assertEqual('application/pdf', blob_element.mime_type)
        self.assertIsNone(blob_element.value)
        self.assertEqual('PARAMETER', blob_element.category)
        self.assertEqual({'en-us': 'Example Blob object', 'de': 'Beispiel Blob Element'},
                         blob_element.description)
        self.assertIs(blob_element.parent, unordered_collection)
        self.assertEqual(blob_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Blobs/ExampleBlob',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(blob_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, blob_element.kind)

        # test attributes of file ExampleFile
        file_element: model.File = unordered_collection.get_referable('ExampleFile')  # type: ignore
        self.assertIsInstance(file_element, model.File)
        self.assertEqual('ExampleFile', file_element.id_short)
        self.assertEqual('application/pdf', file_element.mime_type)
        self.assertIsNone(file_element.value)
        self.assertEqual('PARAMETER', file_element.category)
        self.assertEqual({'en-us': 'Example File object', 'de': 'Beispiel File Element'},
                         file_element.description)
        self.assertIs(file_element.parent, unordered_collection)
        self.assertEqual(file_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Files/ExampleFile',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(file_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, file_element.kind)

        # test attributes of reference element ExampleFile
        ref_element: model.ReferenceElement = \
            unordered_collection.get_referable('ExampleReferenceElement')  # type: ignore
        self.assertIsInstance(ref_element, model.ReferenceElement)
        self.assertEqual('ExampleReferenceElement', ref_element.id_short)
        self.assertIsNone(ref_element.value)
        self.assertEqual('PARAMETER', ref_element.category)
        self.assertEqual({'en-us': 'Example Reference Element object', 'de': 'Beispiel Reference Element Element'},
                         ref_element.description)
        self.assertIs(ref_element.parent, unordered_collection)
        self.assertEqual(ref_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(ref_element.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, ref_element.kind)

        # test attributes of unordered collection element ExampleSubmodelCollectionUnordered2
        unordered_collection2: model.SubmodelElementCollectionUnordered = \
            submodel.get_referable('ExampleSubmodelCollectionUnordered2')  # type: ignore
        self.assertIsInstance(unordered_collection2, model.SubmodelElementCollectionUnordered)
        self.assertEqual('ExampleSubmodelCollectionUnordered2', unordered_collection2.id_short)
        self.assertEqual(0, len(unordered_collection2.value))
        self.assertEqual('PARAMETER', unordered_collection2.category)
        self.assertEqual({'en-us': 'Example SubmodelElementCollectionUnordered object',
                          'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
                         unordered_collection2.description)
        self.assertIs(unordered_collection2.parent, submodel)
        self.assertEqual(unordered_collection2.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelElementCollections/ExampleSubmodelElementCollectionUnordered',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(unordered_collection2.qualifier))
        self.assertEqual(model.ModelingKind.TEMPLATE, unordered_collection2.kind)

    def assert_full_example(self, obj_store: model.DictObjectStore) -> None:
        # separate different kind of objects
        for obj in obj_store:
            if isinstance(obj, model.Submodel):
                self.assert_example_submodel(obj)
            else:
                raise KeyError()
