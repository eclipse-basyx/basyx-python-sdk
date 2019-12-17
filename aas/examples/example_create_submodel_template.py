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
Module for the creation of an example submodel template containing all kind of submodel elements where the kind is
always TEMPLATE.

"""
from aas import model


def create_example_submodel_template() -> model.Submodel:
    """
    creates an example submodel template containing all kind of SubmodelElement objects where the kind is always
    TEMPLATE

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type='string',
        value=None,
        value_id=None,  # TODO
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRDI)]),
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
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/MultiLanguageProperties/'
                                                     'ExampleMultiLanguageProperty',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type='int',
        min_=None,
        max_='100',
        category='PARAMETER',
        description={'en-us': 'Example Range object',
                     'de': 'Beispiel Range Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Ranges/ExampleRange',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_range_2 = model.Range(
        id_short='ExampleRange2',
        value_type='int',
        min_='0',
        max_=None,
        category='PARAMETER',
        description={'en-us': 'Example Range object',
                     'de': 'Beispiel Range Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Ranges/ExampleRange',
                                               id_type=model.KeyType.IRDI)]),
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
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Blobs/ExampleBlob',
                                               id_type=model.KeyType.IRDI)]),
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
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Files/ExampleFile',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement',
        value=None,
        category='PARAMETER',
        description={'en-us': 'Example Reference Element object',
                     'de': 'Beispiel Reference Element Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_relationship_element = model.RelationshipElement(
        id_short='ExampleRelationshipElement',
        first=model.AASReference([model.Key(type_=model.KeyElements.PROPERTY,
                                            local=True,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT)],
                                 model.Property),
        second=model.AASReference([model.Key(type_=model.KeyElements.PROPERTY,
                                             local=True,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT)],
                                  model.Property),
        category='PARAMETER',
        description={'en-us': 'Example RelationshipElement object',
                     'de': 'Beispiel RelationshipElement Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleRelationshipElement',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_annotated_relationship_element = model.AnnotatedRelationshipElement(
        id_short='ExampleAnnotatedRelationshipElement',
        first=model.AASReference([model.Key(type_=model.KeyElements.PROPERTY,
                                            local=True,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT)],
                                 model.Property),
        second=model.AASReference([model.Key(type_=model.KeyElements.PROPERTY,
                                             local=True,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT)],
                                  model.Property),
        annotation=None,
        category='PARAMETER',
        description={'en-us': 'Example AnnotatedRelationshipElement object',
                     'de': 'Beispiel AnnotatedRelationshipElement Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleAnnotatedRelationshipElement',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_operation_variable_input = model.OperationVariable(
        id_short='ExampleInputOperationVariable',
        value=submodel_element_property,
        category='PARAMETER',
        description={'en-us': 'Example ExampleInputOperationVariable object',
                     'de': 'Beispiel ExampleInputOperationVariable Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Operations/'
                                                     'ExampleInputOperationVariable',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_operation_variable_output = model.OperationVariable(
        id_short='ExampleOutputOperationVariable',
        value=submodel_element_property,
        category='PARAMETER',
        description={'en-us': 'Example OutputOperationVariable object',
                     'de': 'Beispiel OutputOperationVariable Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Operations/'
                                                     'ExampleOutputOperationVariable',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_operation_variable_in_output = model.OperationVariable(
        id_short='ExampleInOutputOperationVariable',
        value=submodel_element_property,
        category='PARAMETER',
        description={'en-us': 'Example InOutputOperationVariable object',
                     'de': 'Beispiel InOutputOperationVariable Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Operations/'
                                                     'ExampleInOutputOperationVariable',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_operation = model.Operation(
        id_short='ExampleOperation',
        input_variable={submodel_element_operation_variable_input},
        output_variable={submodel_element_operation_variable_output},
        in_output_variable={submodel_element_operation_variable_in_output},
        category='PARAMETER',
        description={'en-us': 'Example Operation object',
                     'de': 'Beispiel Operation Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Operations/'
                                                     'ExampleOperation',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_capability = model.Capability(
        id_short='ExampleCapability',
        category='PARAMETER',
        description={'en-us': 'Example Capability object',
                     'de': 'Beispiel Capability Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Capabilities/'
                                                     'ExampleCapability',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_basic_event = model.BasicEvent(
        id_short='ExampleBasicEvent',
        observed=model.AASReference([model.Key(type_=model.KeyElements.PROPERTY,
                                               local=True,
                                               value='ExampleProperty',
                                               id_type=model.KeyType.IDSHORT)],
                                    model.Property),
        category='PARAMETER',
        description={'en-us': 'Example BasicEvent object',
                     'de': 'Beispiel BasicEvent Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Events/'
                                                     'ExampleBasicEvent',
                                               id_type=model.KeyType.IRDI)]),
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
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionOrdered',
                                               id_type=model.KeyType.IRDI)]),
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
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionUnordered',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel_element_submodel_element_collection_unordered_2 = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered2',
        value=(),
        category='PARAMETER',
        description={'en-us': 'Example SubmodelElementCollectionUnordered object',
                     'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
        parent=None,
        data_specification=None,
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionUnordered',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)

    submodel = model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel',
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
        data_specification={model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                       local=False,
                                                       value='http://acplt.org/DataSpecifications/AssetTypes/'
                                                             'TestAsset',
                                                       id_type=model.KeyType.IRDI)])},
        semantic_id=model.Reference([model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/SubmodelTemplates/'
                                                     'ExampleSubmodel',
                                               id_type=model.KeyType.IRDI)]),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)
    return submodel
