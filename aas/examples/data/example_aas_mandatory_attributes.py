# Copyright 2020 PyI40AAS Contributors
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
Module for the creation of an object store with an example asset administration shell, related asset and example
submodels and a concept dictionary containing an example concept description. All objects only contain mandatory
attributes.

To get this object store use the function 'create_full_example'. If you want to get single example objects or want to
get more information use the other functions.
"""
import logging

from ... import model
from ._helper import AASDataChecker

logger = logging.getLogger(__name__)


def create_full_example() -> model.DictObjectStore:
    """
    creates an object store which is filled with an example asset, submodel, concept description and asset
    administration shell using the function of this module

    :return: object store
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
    creates an example submodel containing all kind of SubmodelElement objects where only mandatory attributes are set

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

    submodel_element_basic_event = model.BasicEvent(
        id_short='ExampleBasicEvent',
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
                          submodel_element_basic_event,
                          submodel_element_submodel_element_collection_ordered,
                          submodel_element_submodel_element_collection_unordered,
                          submodel_element_submodel_element_collection_unordered_2))
    return submodel


def create_example_empty_submodel() -> model.Submodel:
    """
    creates an example empty submodel where only the identification attribute is set

    :return: example submodel
    """
    return model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel2_Mandatory',
                                        id_type=model.IdentifierType.IRI))


def create_example_concept_description() -> model.ConceptDescription:
    """
    creates an example concept description where only the identification attribute is set

    :return: example concept description
    """
    concept_description = model.ConceptDescription(
        identification=model.Identifier(id_='https://acplt.org/Test_ConceptDescription_Mandatory',
                                        id_type=model.IdentifierType.IRI))
    return concept_description


def create_example_asset_administration_shell() -> \
        model.AssetAdministrationShell:
    """
    creates an example asset administration shell containing references to the example asset, the example submodels and
    including the example concept dictionary

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
    creates an example empty asset administration shell where only the reference to the asset and the identification
    attribute is set

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
