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
Module for the creation of a object store with missing object attribute combination for testing the serialization

"""
from ... import model
from ._helper import AASDataChecker


def create_full_example() -> model.DictObjectStore:
    """
    creates an object store containing an example asset identification submodel, an example asset, an example submodel,
    an example concept description and an example asset administration shell

    :return: object store
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(create_example_asset())
    obj_store.add(create_example_submodel())
    obj_store.add(create_example_concept_description())
    obj_store.add(create_example_asset_administration_shell(create_example_concept_dictionary()))
    return obj_store


def create_example_asset() -> model.Asset:
    """
    creates an example asset which holds references to the example asset identification submodel

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
    creates an example submodel containing all kind of SubmodelElement objects

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
        min_=0,
        max_=100,
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
        value=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            local=True,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
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
        annotation={model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                                  local=True,
                                                  value='ExampleProperty',
                                                  id_type=model.KeyType.IDSHORT),),
                                       model.Property)},
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
    creates an example concept description

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
    creates an example concept dictionary containing an reference to the example concept description

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
    creates an example asset administration shell containing references to the example asset and example submodel

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
        security_=None,
        submodel_={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                 local=False,
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


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore, failsafe: bool = True) -> None:
    # separate different kind of objects
    assets = []
    submodels = []
    concept_descriptions = []
    shells = []
    for obj in obj_store:
        if isinstance(obj, model.Asset):
            assets.append(obj)
        elif isinstance(obj, model.AssetAdministrationShell):
            shells.append(obj)
        elif isinstance(obj, model.Submodel):
            submodels.append(obj)
        elif isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)
        else:
            if failsafe:
                raise KeyError()

    for asset in assets:
        if asset.identification.id == 'https://acplt.org/Test_Asset_Missing':
            check_example_asset(checker, asset)
        else:
            if failsafe:
                raise KeyError()

    for shell in shells:
        if shell.identification.id == 'https://acplt.org/Test_AssetAdministrationShell_Missing':
            check_example_asset_administration_shell(checker, shell)
        else:
            if failsafe:
                raise KeyError()

    for submodel in submodels:
        if submodel.identification.id == 'https://acplt.org/Test_Submodel_Missing':
            check_example_submodel(checker, submodel)
        else:
            if failsafe:
                raise KeyError()

    for cd in concept_descriptions:
        if cd.identification.id == 'https://acplt.org/Test_ConceptDescription_Missing':
            check_example_concept_description(checker, cd)
        else:
            if failsafe:
                raise KeyError()
