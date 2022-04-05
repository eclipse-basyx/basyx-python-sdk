# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
Module for the creation of an :class:`ObjectStore <aas.model.provider.DictObjectStore>` with an example
:class:`~aas.model.aas.AssetAdministrationShell` and example :class:`Submodels <aas.model.submodel.Submodel>`
and a :class:`~aas.model.concept.ConceptDictionary` containing an
example :class:`~aas.model.concept.ConceptDescription`. All objects only contain mandatory
attributes.

To get this object store use the function
:meth:`~aas.examples.data.example_aas_mandatory_attributes.create_full_example`. If you want to get single example
objects or want to get more information use the other functions.
"""
import logging

from ... import model
from ._helper import AASDataChecker

logger = logging.getLogger(__name__)


def create_full_example() -> model.DictObjectStore:
    """
    Creates an :class:`~.aas.model.provider.DictObjectStore` which is filled with an example
    :class:`~aas.model.submodel.Submodel`, :class:`~aas.model.concept.ConceptDescription`
    and :class:`~aas.model.aas.AssetAdministrationShell` using the functions of this module

    :return: :class:`~aas.model.provider.DictObjectStore`
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(create_example_submodel())
    obj_store.add(create_example_empty_submodel())
    obj_store.add(create_example_concept_description())
    obj_store.add(create_example_asset_administration_shell())
    obj_store.add(create_example_empty_asset_administration_shell())
    return obj_store


def create_example_submodel() -> model.Submodel:
    """
    Creates an example :class:`~aas.model.submodel.Submodel` containing all kind of
    :class:`~aas.model.submodel.SubmodelElement` objects where only mandatory attributes are set

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        category="PARAMETER",
        value_type=model.datatypes.String)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        category="PARAMETER",
        id_short='ExampleMultiLanguageProperty')

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        category="PARAMETER",
        value_type=model.datatypes.Int)

    submodel_element_blob = model.Blob(
        id_short='ExampleBlob',
        mime_type='application/pdf')

    submodel_element_file = model.File(
        id_short='ExampleFile',
        mime_type='application/pdf')

    submodel_element_reference_element = model.ReferenceElement(
        category="PARAMETER",
        id_short='ExampleReferenceElement')

    submodel_element_relationship_element = model.RelationshipElement(
        id_short='ExampleRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property))

    submodel_element_annotated_relationship_element = model.AnnotatedRelationshipElement(
        id_short='ExampleAnnotatedRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             value='ExampleProperty',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property))

    submodel_element_operation = model.Operation(
        id_short='ExampleOperation')

    submodel_element_capability = model.Capability(
        id_short='ExampleCapability')

    submodel_element_basic_event_element = model.BasicEventElement(
        id_short='ExampleBasicEventElement',
        observed=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                               value='ExampleProperty',
                                               id_type=model.KeyType.IDSHORT),),
                                    model.Property))

    submodel_element_submodel_element_collection_ordered = model.SubmodelElementCollectionOrdered(
        id_short='ExampleSubmodelCollectionOrdered',
        value=(submodel_element_property,
               submodel_element_multi_language_property,
               submodel_element_range))

    submodel_element_submodel_element_collection_unordered = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered',
        value=(submodel_element_blob,
               submodel_element_file,
               submodel_element_reference_element))

    submodel_element_submodel_element_collection_unordered_2 = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered2',
        value=())

    submodel = model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel_Mandatory',
                                        id_type=model.IdentifierType.IRI),
        submodel_element=(submodel_element_relationship_element,
                          submodel_element_annotated_relationship_element,
                          submodel_element_operation,
                          submodel_element_capability,
                          submodel_element_basic_event_element,
                          submodel_element_submodel_element_collection_ordered,
                          submodel_element_submodel_element_collection_unordered,
                          submodel_element_submodel_element_collection_unordered_2))
    return submodel


def create_example_empty_submodel() -> model.Submodel:
    """
    Creates an example empty :class:`~aas.model.submodel.Submodel` where only the identification attribute is set

    :return: example submodel
    """
    return model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel2_Mandatory',
                                        id_type=model.IdentifierType.IRI))


def create_example_concept_description() -> model.ConceptDescription:
    """
    Creates an example :class:`~aas.model.concept.ConceptDescription` where only the identification attribute is set

    :return: example concept description
    """
    concept_description = model.ConceptDescription(
        identification=model.Identifier(id_='https://acplt.org/Test_ConceptDescription_Mandatory',
                                        id_type=model.IdentifierType.IRI))
    return concept_description


def create_example_asset_administration_shell() -> \
        model.AssetAdministrationShell:
    """
    Creates an example :class:`~aas.model.aas.AssetAdministrationShell` containing references to the example,
    the example :class:`~Submodels <aas.model.submodel.Submodel>`.

    :return: example asset administration shell
    """
    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.INSTANCE,
        global_asset_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                   value='http://acplt.org/Test_Asset_Mandatory/',
                                                   id_type=model.KeyType.IRI),)))

    asset_administration_shell = model.AssetAdministrationShell(
        asset_information=asset_information,
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell_Mandatory',
                                        id_type=model.IdentifierType.IRI),
        submodel={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                value='https://acplt.org/Test_Submodel_Mandatory',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel),
                  model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                value='https://acplt.org/Test_Submodel2_Mandatory',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel)},)
    return asset_administration_shell


def create_example_empty_asset_administration_shell() -> model.AssetAdministrationShell:
    """
    Creates an example empty :class:`~aas.model.aas.AssetAdministrationShell` with just
    an empty :class:`~aas.model.aas.AssetInformation` and an :class:`~aas.model.base.Identifier`

    :return: example asset administration shell
    """
    asset_administration_shell = model.AssetAdministrationShell(
        asset_information=model.AssetInformation(),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell2_Mandatory',
                                        id_type=model.IdentifierType.IRI))
    return asset_administration_shell


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_concept_description(checker: AASDataChecker, concept_description: model.ConceptDescription) -> None:
    expected_concept_description = create_example_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def check_example_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) -> None:
    expected_shell = create_example_asset_administration_shell()
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def check_example_empty_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) \
        -> None:
    expected_shell = create_example_empty_asset_administration_shell()
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def check_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_example_empty_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_empty_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    expected_data = create_full_example()
    checker.check_object_store(obj_store, expected_data)
