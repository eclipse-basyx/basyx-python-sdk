# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
Module for the creation of an :class:`ObjectStore <aas.model.provider.DictObjectStore>` with an example
:class:`~aas.model.aas.AssetAdministrationShell`, related :class:`~aas.model.aas.Asset` and example
:class:`Submodels <aas.model.submodel.Submodel>` and a :class:`~aas.model.concept.ConceptDictionary` containing an
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
    :class:`~aas.model.aas.Asset`, :class:`~aas.model.submodel.Submodel`, :class:`~aas.model.concept.ConceptDescription`
    and :class:`~aas.model.aas.AssetAdministrationShell` using the functions of this module

    :return: :class:`~aas.model.provider.DictObjectStore`
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(create_example_asset())
    obj_store.add(create_example_submodel())
    obj_store.add(create_example_empty_submodel())
    obj_store.add(create_example_concept_description())
    obj_store.add(create_example_asset_administration_shell(create_example_concept_dictionary()))
    obj_store.add(create_example_empty_asset_administration_shell())
    return obj_store


def create_example_asset() -> model.Asset:
    """
    Creates an example :class:`~aas.model.aas.Asset` where only the `kind` and `identification` attributes are set

    :return: example Asset
    """
    asset = model.Asset(
        kind=model.AssetKind.INSTANCE,
        identification=model.Identifier(id_='https://acplt.org/Test_Asset_Mandatory',
                                        id_type=model.IdentifierType.IRI))
    return asset


def create_example_submodel() -> model.Submodel:
    """
    Creates an example :class:`~aas.model.submodel.Submodel` containing all kind of
    :class:`~aas.model.submodel.SubmodelElement` objects where only mandatory attributes are set

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty')

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type=model.datatypes.Int)

    submodel_element_blob = model.Blob(
        id_short='ExampleBlob',
        mime_type='application/pdf')

    submodel_element_file = model.File(
        id_short='ExampleFile',
        mime_type='application/pdf')

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement')

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
                                  model.Property))

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
                                  model.Property))

    submodel_element_operation = model.Operation(
        id_short='ExampleOperation')

    submodel_element_capability = model.Capability(
        id_short='ExampleCapability')

    submodel_element_basic_event = model.BasicEvent(
        id_short='ExampleBasicEvent',
        observed=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                               local=True,
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
                          submodel_element_basic_event,
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


def create_example_concept_dictionary() -> model.ConceptDictionary:
    """
    creates an example :class:`~aas.model.concept.ConceptDictionary` where only the `id_short` attribute is set

    :return: example concept dictionary
    """
    concept_dictionary = model.ConceptDictionary(
        id_short='TestConceptDictionary')
    return concept_dictionary


def create_example_asset_administration_shell(concept_dictionary: model.ConceptDictionary) -> \
        model.AssetAdministrationShell:
    """
    Creates an example :class:`~aas.model.aas.AssetAdministrationShell` containing references to the example
    :class:`~aas.model.aas.Asset`, the example :class:`Submodels <aas.model.submodel.Submodel>` and
    including the example :class:`~aas.model.concept.ConceptDictionary`

    :return: example asset administration shell
    """
    asset_administration_shell = model.AssetAdministrationShell(
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value='https://acplt.org/Test_Asset_Mandatory',
                                            id_type=model.KeyType.IRI),),
                                 model.Asset),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell_Mandatory',
                                        id_type=model.IdentifierType.IRI),
        submodel={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                local=True,
                                                value='https://acplt.org/Test_Submodel_Mandatory',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel),
                  model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                local=True,
                                                value='https://acplt.org/Test_Submodel2_Mandatory',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel)},
        concept_dictionary=[concept_dictionary])
    return asset_administration_shell


def create_example_empty_asset_administration_shell() -> model.AssetAdministrationShell:
    """
    Creates an example empty :class:`~aas.model.aas.AssetAdministrationShell` where only the reference to the
    :class:`~aas.model.aas.Asset` and the identification
    attribute is set

    :return: example asset administration shell
    """
    asset_administration_shell = model.AssetAdministrationShell(
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value='https://acplt.org/Test_Asset_Mandatory',
                                            id_type=model.KeyType.IRI),),
                                 model.Asset),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell2_Mandatory',
                                        id_type=model.IdentifierType.IRI))
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
    example_data = create_full_example()
    checker.check_object_store(example_data, obj_store)
