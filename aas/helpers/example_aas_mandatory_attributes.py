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
Module for the creation of an object store with an example asset administration shell, related asset and example
submodels and a concept dictionary containing an example concept description. All objects only contain mandatory
attributes.

To get this object store use the function 'create_full_example'. If you want to get single example objects or want to
get more information use the other functions.
"""
from .. import model


def create_full_example() -> model.DictObjectStore:
    """
    creates an object store which is filled with an example asset, submodel, concept description and asset
    administration shell using the function of this module

    :return: object store
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
    creates an example asset where only the kind and identification attributes are set

    :return: example asset
    """
    asset = model.Asset(
        kind=model.AssetKind.INSTANCE,
        identification=model.Identifier(id_='https://acplt.org/Test_Asset',
                                        id_type=model.IdentifierType.IRI))
    return asset


def create_example_submodel() -> model.Submodel:
    """
    creates an example submodel containing all kind of SubmodelElement objects where only mandatory attributes are set

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type='string')

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty')

    submodel_element_range = model.Range(
        id_short='ExampleRange',
        value_type='int')

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
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel',
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
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel2',
                                        id_type=model.IdentifierType.IRI))


def create_example_concept_description() -> model.ConceptDescription:
    """
    creates an example concept description where only the identification attribute is set

    :return: example concept description
    """
    concept_description = model.ConceptDescription(
        identification=model.Identifier(id_='https://acplt.org/Test_ConceptDescription',
                                        id_type=model.IdentifierType.IRI))
    return concept_description


def create_example_concept_dictionary() -> model.ConceptDictionary:
    """
    creates an example concept dictionary where only the id_short attribute is set

    :return: example concept dictionary
    """
    concept_dictionary = model.ConceptDictionary(
        id_short='TestConceptDictionary')
    return concept_dictionary


def create_example_asset_administration_shell(concept_dictionary: model.ConceptDictionary) -> \
        model.AssetAdministrationShell:
    """
    creates an example asset administration shell containing references to the example asset, the example submodels and
    including the example concept dictionary

    :return: example asset administration shell
    """
    asset_administration_shell = model.AssetAdministrationShell(
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value='https://acplt.org/Test_Asset',
                                            id_type=model.KeyType.IRDI),),
                                 model.Asset),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell',
                                        id_type=model.IdentifierType.IRI),
        submodel_={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                 local=False,
                                                 value='https://acplt.org/Test_Submodel',
                                                 id_type=model.KeyType.IRDI),),
                                      model.Submodel),
                   model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                 local=False,
                                                 value='https://acplt.org/Test_Submodel2',
                                                 id_type=model.KeyType.IRDI),),
                                      model.Submodel)},
        concept_dictionary=[concept_dictionary])
    return asset_administration_shell


def create_example_empty_asset_administration_shell() -> model.AssetAdministrationShell:
    """
    creates an example empty asset administration shell where only the reference to the asset and the identification
    attribute is set

    :return: example asset administration shell
    """
    asset_administration_shell = model.AssetAdministrationShell(
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value='https://acplt.org/Test_Asset',
                                            id_type=model.KeyType.IRDI),),
                                 model.Asset),
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell2',
                                        id_type=model.IdentifierType.IRI))
    return asset_administration_shell
