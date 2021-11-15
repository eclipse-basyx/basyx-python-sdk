# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
Module for the creation of an example :class:`~aas.model.submodel.Submodel` template containing all kind of
:class:`SubmodelElements <aas.model.submodel.SubmodelElement>` where the kind is
always `TEMPLATE`.
"""
import logging

from ... import model
from ._helper import AASDataChecker

logger = logging.getLogger(__name__)


def create_example_submodel_template() -> model.Submodel:
    """
    Creates an example :class:`~aas.model.submodel.Submodel` template containing all kind of
    :class:`~aas.model.submodel.SubmodelElement` objects where the kind is always
    `TEMPLATE`

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String,
        value=None,
        value_id=None,  # TODO
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty',
        value=None,
        value_id=None,  # TODO
        category='CONSTANT',
        description={'en-us': 'Example MultiLanguageProperty object',
                     'de': 'Beispiel MulitLanguageProperty Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/MultiLanguageProperties/'
                                                     'ExampleMultiLanguageProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type=model.datatypes.Int,
        min=None,
        max=100,
        category='PARAMETER',
        description={'en-us': 'Example Range object',
                     'de': 'Beispiel Range Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Ranges/ExampleRange',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range_2 = model.Range(
        id_short='ExampleRange2',
        value_type=model.datatypes.Int,
        min=0,
        max=None,
        category='PARAMETER',
        description={'en-us': 'Example Range object',
                     'de': 'Beispiel Range Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Ranges/ExampleRange',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_blob = model.Blob(
        id_short='ExampleBlob',
        mime_type='application/pdf',
        value=None,
        category='PARAMETER',
        description={'en-us': 'Example Blob object',
                     'de': 'Beispiel Blob Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Blobs/ExampleBlob',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_file = model.File(
        id_short='ExampleFile',
        mime_type='application/pdf',
        value=None,
        category='PARAMETER',
        description={'en-us': 'Example File object',
                     'de': 'Beispiel File Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Files/ExampleFile',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement',
        value=None,
        category='PARAMETER',
        description={'en-us': 'Example Reference Element object',
                     'de': 'Beispiel Reference Element Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_relationship_element = model.RelationshipElement(
        id_short='ExampleRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            local=True,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             local=True,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property),
        category='PARAMETER',
        description={'en-us': 'Example RelationshipElement object',
                     'de': 'Beispiel RelationshipElement Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleRelationshipElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_annotated_relationship_element = model.AnnotatedRelationshipElement(
        id_short='ExampleAnnotatedRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            local=True,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             local=True,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property),
        annotation=None,
        category='PARAMETER',
        description={'en-us': 'Example AnnotatedRelationshipElement object',
                     'de': 'Beispiel AnnotatedRelationshipElement Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleAnnotatedRelationshipElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_operation_variable_input = model.OperationVariable(
        value=submodel_element_property)

    submodel_element_operation_variable_output = model.OperationVariable(
        value=submodel_element_property)

    submodel_element_operation_variable_in_output = model.OperationVariable(
        value=submodel_element_property)

    submodel_element_operation = model.Operation(
        id_short='ExampleOperation',
        input_variable=[submodel_element_operation_variable_input],
        output_variable=[submodel_element_operation_variable_output],
        in_output_variable=[submodel_element_operation_variable_in_output],
        category='PARAMETER',
        description={'en-us': 'Example Operation object',
                     'de': 'Beispiel Operation Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Operations/'
                                                     'ExampleOperation',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_capability = model.Capability(
        id_short='ExampleCapability',
        category='PARAMETER',
        description={'en-us': 'Example Capability object',
                     'de': 'Beispiel Capability Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Capabilities/'
                                                     'ExampleCapability',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_basic_event = model.BasicEvent(
        id_short='ExampleBasicEvent',
        observed=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                               local=True,
                                               value='ExampleProperty',
                                               id_type=model.KeyType.IDSHORT),),
                                    model.Property),
        category='PARAMETER',
        description={'en-us': 'Example BasicEvent object',
                     'de': 'Beispiel BasicEvent Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Events/'
                                                     'ExampleBasicEvent',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection_ordered = model.SubmodelElementCollectionOrdered(
        id_short='ExampleSubmodelCollectionOrdered',
        value=(submodel_element_property,
               submodel_element_multi_language_property,
               submodel_element_range,
               submodel_element_range_2),
        category='PARAMETER',
        description={'en-us': 'Example SubmodelElementCollectionOrdered object',
                     'de': 'Beispiel SubmodelElementCollectionOrdered Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionOrdered',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection_unordered = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered',
        value=(submodel_element_blob,
               submodel_element_file,
               submodel_element_reference_element),
        category='PARAMETER',
        description={'en-us': 'Example SubmodelElementCollectionUnordered object',
                     'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionUnordered',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection_unordered_2 = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered2',
        value=(),
        category='PARAMETER',
        description={'en-us': 'Example SubmodelElementCollectionUnordered object',
                     'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionUnordered',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel = model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel_Template',
                                        id_type=model.IdentifierType.IRI),
        submodel_element=(submodel_element_relationship_element,
                          submodel_element_annotated_relationship_element,
                          submodel_element_operation,
                          submodel_element_capability,
                          submodel_element_basic_event,
                          submodel_element_submodel_element_collection_ordered,
                          submodel_element_submodel_element_collection_unordered,
                          submodel_element_submodel_element_collection_unordered_2),
        id_short='TestSubmodel',
        category=None,
        description={'en-us': 'An example submodel for the test application',
                     'de': 'Ein Beispiel-Teilmodell für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9',
                                                       revision='0'),
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelTemplates/'
                                                     'ExampleSubmodel',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)
    return submodel


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_submodel_template()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    example_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    example_data.add(create_example_submodel_template())
    checker.check_object_store(example_data, obj_store)
