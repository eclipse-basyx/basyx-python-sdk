# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Module for the creation of an :class:`ObjectStore <aas.model.provider.DictObjectStore>` with missing object attribute
combination for testing the serialization
"""
import logging

from ... import model
from ._helper import AASDataChecker

logger = logging.getLogger(__name__)


def create_full_example() -> model.DictObjectStore:
    """
    Creates an :class:`~aas.model.provider.DictObjectStore` containing an example asset identification
    :class:`~aas.model.submodel.Submodel`, an example :class:`~aas.model.aas.Asset`, an example
    :class:`~aas.model.submodel.Submodel`,
    an example :class:`~aas.model.concept.ConceptDescription` and an example
    :class:`~aas.model.aas.AssetAdministrationShell`

    :return: :class:`aas.model.provider.DictObjectStore`
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(create_example_asset())
    obj_store.add(create_example_submodel())
    obj_store.add(create_example_concept_description())
    obj_store.add(create_example_asset_administration_shell(create_example_concept_dictionary()))
    return obj_store


def create_example_asset() -> model.Asset:
    """
    Creates an example :class:`~aas.model.aas.Asset` which holds references to the example asset identification submodel

    :return: example asset
    """
    asset = model.Asset(
        kind=model.AssetKind.INSTANCE,
        identification=model.Identifier(id_='https://acplt.org/Test_Asset_Missing',
                                        id_type=model.IdentifierType.IRI),
        id_short='Test_Asset',
        category=None,
        description={'en-us': 'An example asset for the test application',
                     'de': 'Ein Beispiel-Asset für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(),
        asset_identification_model=None,
        bill_of_material=None)
    return asset


def create_example_submodel() -> model.Submodel:
    """
    Creates an example :class:`~aas.model.submodel.Submodel` containing all kind of
    :class:`~aas.model.submodel.SubmodelElement`  objects

    :return: example submodel
    """
    qualifier = model.Qualifier(
        type_='http://acplt.org/Qualifier/ExampleQualifier',
        value_type=model.datatypes.String)

    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String,
        value='exampleValue',
        value_id=None,  # TODO
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier={qualifier},
        kind=model.ModelingKind.INSTANCE)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty',
        value={'en-us': 'Example value of a MultiLanguageProperty element',
               'de': 'Beispielswert für ein MulitLanguageProperty-Element'},
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
        kind=model.ModelingKind.INSTANCE)

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type=model.datatypes.Int,
        min=0,
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
        kind=model.ModelingKind.INSTANCE)

    submodel_element_blob = model.Blob(
        id_short='ExampleBlob',
        mime_type='application/pdf',
        value=bytearray(b'\x01\x02\x03\x04\x05'),
        category='PARAMETER',
        description={'en-us': 'Example Blob object',
                     'de': 'Beispiel Blob Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Blobs/ExampleBlob',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_file = model.File(
        id_short='ExampleFile',
        mime_type='application/pdf',
        value='/TestFile.pdf',
        category='PARAMETER',
        description={'en-us': 'Example File object',
                     'de': 'Beispiel File Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/Files/ExampleFile',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement',
        value=model.Reference((model.Key(type_=model.KeyElements.PROPERTY,
                                         local=True,
                                         value='ExampleProperty',
                                         id_type=model.KeyType.IDSHORT),)),
        category='PARAMETER',
        description={'en-us': 'Example Reference Element object',
                     'de': 'Beispiel Reference Element Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               local=False,
                                               value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

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
        kind=model.ModelingKind.INSTANCE)

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
        annotation={model.Property(id_short="ExampleAnnotatedProperty",
                                   value_type=model.datatypes.String,
                                   value='exampleValue',
                                   parent=None),
                    model.Range(id_short="ExampleAnnotatedRange",
                                value_type=model.datatypes.Integer,
                                min=1,
                                max=5,
                                parent=None)
                    },
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
        kind=model.ModelingKind.INSTANCE)

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
        kind=model.ModelingKind.INSTANCE)

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
        kind=model.ModelingKind.INSTANCE)

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
        kind=model.ModelingKind.INSTANCE)

    submodel_element_submodel_element_collection_ordered = model.SubmodelElementCollectionOrdered(
        id_short='ExampleSubmodelCollectionOrdered',
        value=(submodel_element_property,
               submodel_element_multi_language_property,
               submodel_element_range),
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
        kind=model.ModelingKind.INSTANCE)

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
        kind=model.ModelingKind.INSTANCE)

    submodel = model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel_Missing',
                                        id_type=model.IdentifierType.IRI),
        submodel_element=(submodel_element_relationship_element,
                          submodel_element_annotated_relationship_element,
                          submodel_element_operation,
                          submodel_element_capability,
                          submodel_element_basic_event,
                          submodel_element_submodel_element_collection_ordered,
                          submodel_element_submodel_element_collection_unordered),
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
        kind=model.ModelingKind.INSTANCE)
    return submodel


def create_example_concept_description() -> model.ConceptDescription:
    """
    Creates an example :class:`~aas.model.concept.ConceptDescription`

    :return: example concept description
    """
    concept_description = model.ConceptDescription(
        identification=model.Identifier(id_='https://acplt.org/Test_ConceptDescription_Missing',
                                        id_type=model.IdentifierType.IRI),
        is_case_of=None,
        id_short='TestConceptDescription',
        category=None,
        description={'en-us': 'An example concept description  for the test application',
                     'de': 'Ein Beispiel-ConceptDescription für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9',
                                                       revision='0'))
    return concept_description


def create_example_concept_dictionary() -> model.ConceptDictionary:
    """
    Creates an example :class:`~aas.model.concept.ConceptDictionary` containing an :class:`~aas.model.base.AASReference`
    to the example :class:`~aas.model.concept.ConceptDescription`

    :return: example concept dictionary
    """
    concept_dictionary = model.ConceptDictionary(
        id_short='TestConceptDictionary',
        category=None,
        description={'en-us': 'An example concept dictionary for the test application',
                     'de': 'Ein Beispiel-ConceptDictionary für eine Test-Anwendung'},
        parent=None,
        concept_description={model.AASReference((model.Key(type_=model.KeyElements.CONCEPT_DESCRIPTION,
                                                           local=False,
                                                           value='https://acplt.org/Test_ConceptDescription_Missing',
                                                           id_type=model.KeyType.IRI),),
                                                model.ConceptDescription)})
    return concept_dictionary


def create_example_asset_administration_shell(concept_dictionary: model.ConceptDictionary) -> \
        model.AssetAdministrationShell:
    """
    Creates an example :class:`~aas.model.aas.AssetAdministrationShell` containing references to the example
    :class:`~aas.model.Asset` and example :class:`~aas.model.submodel.Submodel`

    :return: example asset administration shell
    """
    view = model.View(
        id_short='ExampleView',
        contained_element={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                         local=False,
                                                         value='https://acplt.org/Test_Submodel_Missing',
                                                         id_type=model.KeyType.IRI),),
                                              model.Submodel)})
    view_2 = model.View(
        id_short='ExampleView2')

    asset_administration_shell = model.AssetAdministrationShell(
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value='https://acplt.org/Test_Asset_Missing',
                                            id_type=model.KeyType.IRI),),
                                 model.Asset),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell_Missing',
                                        id_type=model.IdentifierType.IRI),
        id_short='TestAssetAdministrationShell',
        category=None,
        description={'en-us': 'An Example Asset Administration Shell for the test application',
                     'de': 'Ein Beispiel-Verwaltungsschale für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9',
                                                       revision='0'),
        security=None,
        submodel={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                local=True,
                                                value='https://acplt.org/Test_Submodel_Missing',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel)},
        concept_dictionary=[concept_dictionary],
        view=[view, view_2],
        derived_from=None)
    return asset_administration_shell


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_asset(checker: AASDataChecker, asset: model.Asset) -> None:
    expected_asset = create_example_asset()
    checker.check_asset_equal(asset, expected_asset)


def check_example_concept_description(checker: AASDataChecker, concept_description: model.ConceptDescription) -> None:
    expected_concept_description = create_example_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def check_example_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) -> None:
    example_cd = create_example_concept_dictionary()
    expected_shell = create_example_asset_administration_shell(example_cd)
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def check_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    example_data = create_full_example()
    checker.check_object_store(example_data, obj_store)
