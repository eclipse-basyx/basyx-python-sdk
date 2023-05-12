# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Module for the creation of an example :class:`~aas.model.submodel.Submodel` template containing all kind of
:class:`SubmodelElements <aas.model.submodel.SubmodelElement>` where the kind is
always `TEMPLATE`.
"""
import datetime
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
        description=model.LangStringSet({'en-US': 'Example Property object',
                                         'de': 'Beispiel Property Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Properties/ExampleProperty'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty',
        value=None,
        value_id=None,  # TODO
        category='CONSTANT',
        description=model.LangStringSet({'en-US': 'Example MultiLanguageProperty object',
                                         'de': 'Beispiel MulitLanguageProperty Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/MultiLanguageProperties/'
                                                           'ExampleMultiLanguageProperty'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type=model.datatypes.Int,
        min=None,
        max=100,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example Range object',
                                         'de': 'Beispiel Range Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Ranges/ExampleRange'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range_2 = model.Range(
        id_short='ExampleRange2',
        value_type=model.datatypes.Int,
        min=0,
        max=None,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example Range object',
                                         'de': 'Beispiel Range Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Ranges/ExampleRange'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_blob = model.Blob(
        id_short='ExampleBlob',
        content_type=model.ContentType('application/pdf'),
        value=None,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example Blob object',
                                         'de': 'Beispiel Blob Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Blobs/ExampleBlob'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_file = model.File(
        id_short='ExampleFile',
        content_type=model.ContentType('application/pdf'),
        value=None,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example File object',
                                         'de': 'Beispiel File Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Files/ExampleFile'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement',
        value=None,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example Reference Element object',
                                         'de': 'Beispiel Reference Element Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/ReferenceElements/ExampleReferenceElement'
                                                     ),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_relationship_element = model.RelationshipElement(
        id_short='ExampleRelationshipElement',
        first=model.ModelReference((model.Key(type_=model.KeyTypes.SUBMODEL, value='http://acplt.org/Test_Submodel'),
                                    model.Key(type_=model.KeyTypes.PROPERTY,
                                              value='ExampleProperty'),),
                                   model.Property),
        second=model.ModelReference((model.Key(type_=model.KeyTypes.SUBMODEL, value='http://acplt.org/Test_Submodel'),
                                     model.Key(type_=model.KeyTypes.PROPERTY,
                                               value='ExampleProperty'),),
                                    model.Property),
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example RelationshipElement object',
                                         'de': 'Beispiel RelationshipElement Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/RelationshipElements/'
                                                           'ExampleRelationshipElement'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_annotated_relationship_element = model.AnnotatedRelationshipElement(
        id_short='ExampleAnnotatedRelationshipElement',
        first=model.ModelReference((model.Key(type_=model.KeyTypes.SUBMODEL, value='http://acplt.org/Test_Submodel'),
                                    model.Key(type_=model.KeyTypes.PROPERTY,
                                              value='ExampleProperty'),),
                                   model.Property),
        second=model.ModelReference((model.Key(type_=model.KeyTypes.SUBMODEL, value='http://acplt.org/Test_Submodel'),
                                     model.Key(type_=model.KeyTypes.PROPERTY,
                                               value='ExampleProperty'),),
                                    model.Property),
        annotation=(),
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example AnnotatedRelationshipElement object',
                                         'de': 'Beispiel AnnotatedRelationshipElement Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/RelationshipElements/'
                                                           'ExampleAnnotatedRelationshipElement'),)),
        qualifier=(),
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
        description=model.LangStringSet({'en-US': 'Example Operation object',
                                         'de': 'Beispiel Operation Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Operations/'
                                                           'ExampleOperation'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_capability = model.Capability(
        id_short='ExampleCapability',
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example Capability object',
                                         'de': 'Beispiel Capability Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Capabilities/'
                                                           'ExampleCapability'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_basic_event_element = model.BasicEventElement(
        id_short='ExampleBasicEventElement',
        observed=model.ModelReference((model.Key(type_=model.KeyTypes.SUBMODEL, value='http://acplt.org/Test_Submodel'),
                                       model.Key(type_=model.KeyTypes.PROPERTY,
                                                 value='ExampleProperty'),),
                                      model.Property),
        direction=model.Direction.OUTPUT,
        state=model.StateOfEvent.ON,
        message_topic='ExampleTopic',
        message_broker=model.ModelReference((model.Key(model.KeyTypes.SUBMODEL,
                                                       "http://acplt.org/ExampleMessageBroker"),),
                                            model.Submodel),
        last_update=model.datatypes.DateTime(2022, 11, 12, 23, 50, 23, 123456, datetime.timezone.utc),
        min_interval=model.datatypes.Duration(microseconds=1),
        max_interval=model.datatypes.Duration(years=1, months=2, days=3, hours=4, minutes=5, seconds=6,
                                              microseconds=123456),
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example BasicEventElement object',
                                         'de': 'Beispiel BasicEventElement Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/Events/ExampleBasicEventElement'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection = model.SubmodelElementCollection(
        id_short='ExampleSubmodelCollection',
        value=(
               submodel_element_property,
               submodel_element_multi_language_property,
               submodel_element_range,
               submodel_element_range_2,
               submodel_element_blob,
               submodel_element_file,
               submodel_element_reference_element),
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example SubmodelElementCollection object',
                                         'de': 'Beispiel SubmodelElementCollection Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/SubmodelElementCollections/'
                                                           'ExampleSubmodelElementCollection'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection_2 = model.SubmodelElementCollection(
        id_short='ExampleSubmodelCollection2',
        value=(),
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example SubmodelElementCollection object',
                                         'de': 'Beispiel SubmodelElementCollection Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/SubmodelElementCollections/'
                                                           'ExampleSubmodelElementCollection'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_list = model.SubmodelElementList(
        id_short='ExampleSubmodelList',
        type_value_list_element=model.SubmodelElementCollection,
        value=(submodel_element_submodel_element_collection, submodel_element_submodel_element_collection_2),
        semantic_id_list_element=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                       value='http://acplt.org/SubmodelElementCollections/'
                                                                  'ExampleSubmodelElementCollection'),)),
        order_relevant=False,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example SubmodelElementList object',
                                         'de': 'Beispiel SubmodelElementList Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/SubmodelElementLists/'
                                                           'ExampleSubmodelElementList'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_list_2 = model.SubmodelElementList(
        id_short='ExampleSubmodelList2',
        type_value_list_element=model.Capability,
        value=(),
        semantic_id_list_element=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                       value='http://acplt.org/SubmodelElementCollections/'
                                                                  'ExampleSubmodelElementCollection'),)),
        order_relevant=False,
        category='PARAMETER',
        description=model.LangStringSet({'en-US': 'Example SubmodelElementList object',
                                         'de': 'Beispiel SubmodelElementList Element'}),
        parent=None,
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/SubmodelElementLists/'
                                                           'ExampleSubmodelElementList'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)

    submodel = model.Submodel(
        id_=model.Identifier('https://acplt.org/Test_Submodel_Template'),
        submodel_element=(submodel_element_relationship_element,
                          submodel_element_annotated_relationship_element,
                          submodel_element_operation,
                          submodel_element_capability,
                          submodel_element_basic_event_element,
                          submodel_element_submodel_element_list,
                          submodel_element_submodel_element_list_2),
        id_short='TestSubmodel',
        category=None,
        description=model.LangStringSet({'en-US': 'An example submodel for the test application',
                                         'de': 'Ein Beispiel-Teilmodell für eine Test-Anwendung'}),
        parent=None,
        administration=model.AdministrativeInformation(version=model.datatypes.VersionType('1'),
                                                       revision=model.datatypes.RevisionType('1')),
        semantic_id=model.GlobalReference((model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                     value='http://acplt.org/SubmodelTemplates/'
                                                           'ExampleSubmodel'),)),
        qualifier=(),
        kind=model.ModelingKind.TEMPLATE)
    return submodel


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_submodel_template()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    expected_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    expected_data.add(create_example_submodel_template())
    checker.check_object_store(obj_store, expected_data)
