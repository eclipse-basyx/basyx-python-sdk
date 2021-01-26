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
Module for the creation of an :class:`ObjectStore <aas.model.provider.DictObjectStore>` with an example asset
administration shell, related asset and example
submodels and a concept dictionary containing an example concept description

To get this object store use the function :meth:`~aas.examples.data.example_aas.create_full_example`.
If you want to get single example objects or want to get more information use the other functions.
"""
import logging

from ._helper import AASDataChecker
from ... import model

logger = logging.getLogger(__name__)


def create_full_example() -> model.DictObjectStore:
    """
    Creates an object store which is filled with an example :class:`~aas.model.aas.Asset`,
    :class:`~aas.model.submodel.Submodel`, :class:`~aas.model.concept.ConceptDescription` and
    :class:`~aas.model.aas.AssetAdministrationShell` using the functions of this module

    :return: :class:`~aas.model.provider.DictObjectStore`
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(create_example_asset_identification_submodel())
    obj_store.add(create_example_bill_of_material_submodel())
    obj_store.add(create_example_submodel())
    obj_store.add(create_example_concept_description())
    obj_store.add(create_example_asset_administration_shell())
    return obj_store


def create_example_asset_identification_submodel() -> model.Submodel:
    """
    Creates a :class:`~aas.model.submodel.Submodel` for the identification of the example :class:`~aas.model.aas.Asset`
    containing two :class:`~aas.model.submodel.Property` elements according to
    'Verwaltungssschale in der Praxis'
    https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/2019-verwaltungsschale-in-der-praxis.html

    :return: example asset identification submodel
    """
    qualifier = model.Qualifier(
        type_='http://acplt.org/Qualifier/ExampleQualifier',
        value_type=model.datatypes.Int,
        value=100,
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)))

    qualifier2 = model.Qualifier(
        type_='http://acplt.org/Qualifier/ExampleQualifier2',
        value_type=model.datatypes.Int,
        value=50,
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)))

    extension = model.Extension(
        name='ExampleExtension',
        value_type=model.datatypes.String,
        value="ExampleExtensionValue",
        refers_to=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                             value='http://acplt.org/RefersTo/ExampleRefersTo',
                                             id_type=model.KeyType.IRI),)))

    # Property-Element conform to 'Verwaltungssschale in der Praxis' page 41 ManufacturerName:
    # https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/2019-verwaltungsschale-in-der-praxis.html
    identification_submodel_element_manufacturer_name = model.Property(
        id_short='ManufacturerName',
        value_type=model.datatypes.String,
        value='ACPLT',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        category="PARAMETER",
        description={'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                              'responsible for the design, production, packaging and labeling of a product in '
                              'respect to its being brought into circulation.',
                     'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                           'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                           '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='0173-1#02-AAO677#002',
                                               id_type=model.KeyType.IRI),)),
        qualifier={qualifier, qualifier2},
        kind=model.ModelingKind.INSTANCE,
        extension={extension})

    # Property-Element conform to 'Verwaltungssschale in der Praxis' page 44 InstanceId:
    # https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/2019-verwaltungsschale-in-der-praxis.html
    identification_submodel_element_instance_id = model.Property(
        id_short='InstanceId',
        value_type=model.datatypes.String,
        value='978-8234-234-342',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        category="PARAMETER",
        description={'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                              'responsible for the design, production, packaging and labeling of a product in '
                              'respect to its being brought into circulation.',
                     'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                           'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                           '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://opcfoundation.org/UA/DI/1.1/DeviceType/Serialnumber',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    # asset identification submodel which will be included in the asset object
    identification_submodel = model.Submodel(
        identification=model.Identifier(id_='http://acplt.org/Submodels/Assets/TestAsset/Identification',
                                        id_type=model.IdentifierType.IRI),
        submodel_element=(identification_submodel_element_manufacturer_name,
                          identification_submodel_element_instance_id),
        id_short='Identification',
        category=None,
        description={'en-us': 'An example asset identification submodel for the test application',
                     'de': 'Ein Beispiel-Identifikations-Submodel für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9',
                                                       revision='0'),
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.SUBMODEL,
                                               value='http://acplt.org/SubmodelTemplates/AssetIdentification',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)
    return identification_submodel


def create_example_bill_of_material_submodel() -> model.Submodel:
    """
    creates a :class:`~aas.model.submodel.Submodel` for the bill of material of the example
    :class:`~aas.model.aas.Asset` containing two entities one co-managed and one
    self-managed

    :return: example bill of material submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String,
        value='exampleValue',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier={model.Formula(
            depends_on={model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                   value='http://acplt.org/ValueId/ExampleValueId',
                                                   id_type=model.KeyType.IRI),))}),
                   model.Formula()},
        kind=model.ModelingKind.INSTANCE)

    submodel_element_property2 = model.Property(
        id_short='ExampleProperty2',
        value_type=model.datatypes.String,
        value='exampleValue2',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    entity = model.Entity(
        id_short='ExampleEntity',
        entity_type=model.EntityType.SELF_MANAGED_ENTITY,
        statement={submodel_element_property, submodel_element_property2},
        global_asset_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                   value='http://acplt.org/TestAsset/',
                                                   id_type=model.KeyType.IRI),)),
        specific_asset_id=model.IdentifierKeyValuePair(key="TestKey",
                                                       value="TestValue",
                                                       external_subject_id=model.Reference((
                                                           model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                                     value='http://acplt.org/SpecificAssetId/',
                                                                     id_type=model.KeyType.IRI),))),
        category="PARAMETER",
        description={'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                              'responsible for the design, production, packaging and labeling of a product in '
                              'respect to its being brought into circulation.',
                     'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                           'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                           '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://opcfoundation.org/UA/DI/1.1/DeviceType/Serialnumber',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE
    )

    entity_2 = model.Entity(
        id_short='ExampleEntity2',
        entity_type=model.EntityType.CO_MANAGED_ENTITY,
        statement=(),
        global_asset_id=None,
        specific_asset_id=None,
        category="PARAMETER",
        description={'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                              'responsible for the design, production, packaging and labeling of a product in '
                              'respect to its being brought into circulation.',
                     'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                           'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                           '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://opcfoundation.org/UA/DI/1.1/DeviceType/Serialnumber',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE
    )

    # bill of material submodel which will be included in the asset object
    # bill of material submodel which will be included in the asset object
    bill_of_material = model.Submodel(
        identification=model.Identifier(id_='http://acplt.org/Submodels/Assets/TestAsset/BillOfMaterial',
                                        id_type=model.IdentifierType.IRI),
        submodel_element=(entity,
                          entity_2),
        id_short='BillOfMaterial',
        category=None,
        description={'en-us': 'An example bill of material submodel for the test application',
                     'de': 'Ein Beispiel-BillofMaterial-Submodel für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9'),
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.SUBMODEL,
                                               value='http://acplt.org/SubmodelTemplates/BillOfMaterial',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)
    return bill_of_material


def create_example_submodel() -> model.Submodel:
    """
    Creates an example :class:`~aas.model.submodel.Submodel` containing all kind of
    :class:`~aas.model.submodel.SubmodelElement` objects

    :return: example submodel
    """
    submodel_element_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String,
        value='exampleValue',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        display_name={'en-us': 'ExampleProperty',
                      'de': 'BeispielProperty'},
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_multi_language_property = model.MultiLanguageProperty(
        id_short='ExampleMultiLanguageProperty',
        value={'en-us': 'Example value of a MultiLanguageProperty element',
               'de': 'Beispielswert für ein MulitLanguageProperty-Element'},
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleMultiLanguageValueId',
                                            id_type=model.KeyType.IRI),)),
        category='CONSTANT',
        description={'en-us': 'Example MultiLanguageProperty object',
                     'de': 'Beispiel MulitLanguageProperty Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
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
                                               value='http://acplt.org/Files/ExampleFile',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_file_uri = model.File(
        id_short='ExampleFileURI',
        mime_type='application/pdf',
        value='https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details-of-the-Asset-'
              'Administration-Shell-Part1.pdf?__blob=publicationFile&v=5',
        category='CONSTANT',
        description={'en-us': 'Details of the Asset Administration Shell—An example for an external file reference',
                     'de': 'Details of the Asset Administration Shell – Ein Beispiel für eine extern referenzierte '
                           'Datei'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/Files/ExampleFile',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_reference_element = model.ReferenceElement(
        id_short='ExampleReferenceElement',
        value=model.Reference((model.Key(type_=model.KeyElements.PROPERTY,
                                         value='ExampleProperty',
                                         id_type=model.KeyType.IDSHORT),)),
        category='PARAMETER',
        description={'en-us': 'Example Reference Element object',
                     'de': 'Beispiel Reference Element Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_relationship_element = model.RelationshipElement(
        id_short='ExampleRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             value='ExampleProperty2',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property),
        category='PARAMETER',
        description={'en-us': 'Example RelationshipElement object',
                     'de': 'Beispiel RelationshipElement Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleRelationshipElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_annotated_relationship_element = model.AnnotatedRelationshipElement(
        id_short='ExampleAnnotatedRelationshipElement',
        first=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                            value='ExampleProperty',
                                            id_type=model.KeyType.IDSHORT),),
                                 model.Property),
        second=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                             value='ExampleProperty2',
                                             id_type=model.KeyType.IDSHORT),),
                                  model.Property),
        annotation={model.Property(id_short="ExampleAnnotatedProperty",
                                   value_type=model.datatypes.String,
                                   value='exampleValue',
                                   category="PARAMETER",
                                   parent=None),
                    model.Range(id_short="ExampleAnnotatedRange",
                                value_type=model.datatypes.Integer,
                                min=1,
                                max=5,
                                category="PARAMETER",
                                parent=None)
                    },
        category='PARAMETER',
        description={'en-us': 'Example AnnotatedRelationshipElement object',
                     'de': 'Beispiel AnnotatedRelationshipElement Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/RelationshipElements/'
                                                     'ExampleAnnotatedRelationshipElement',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    operation_variable_property = model.Property(
        id_short='ExampleProperty',
        value_type=model.datatypes.String,
        value='exampleValue',
        value_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                            value='http://acplt.org/ValueId/ExampleValueId',
                                            id_type=model.KeyType.IRI),)),
        display_name={'en-us': 'ExampleProperty',
                      'de': 'BeispielProperty'},
        category='CONSTANT',
        description={'en-us': 'Example Property object',
                     'de': 'Beispiel Property Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/Properties/ExampleProperty',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.TEMPLATE)
    submodel_element_operation_variable_input = model.OperationVariable(
        value=operation_variable_property)

    submodel_element_operation_variable_output = model.OperationVariable(
        value=operation_variable_property)

    submodel_element_operation_variable_in_output = model.OperationVariable(
        value=operation_variable_property)

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
                                               value='http://acplt.org/Capabilities/'
                                                     'ExampleCapability',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_basic_event = model.BasicEvent(
        id_short='ExampleBasicEvent',
        observed=model.AASReference((model.Key(type_=model.KeyElements.PROPERTY,
                                               value='ExampleProperty',
                                               id_type=model.KeyType.IDSHORT),),
                                    model.Property),
        category='PARAMETER',
        description={'en-us': 'Example BasicEvent object',
                     'de': 'Beispiel BasicEvent Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
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
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionOrdered',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel_element_submodel_element_collection_unordered = model.SubmodelElementCollectionUnordered(
        id_short='ExampleSubmodelCollectionUnordered',
        value=(submodel_element_blob,
               submodel_element_file,
               submodel_element_file_uri,
               submodel_element_reference_element),
        category='PARAMETER',
        description={'en-us': 'Example SubmodelElementCollectionUnordered object',
                     'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
        parent=None,
        semantic_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/SubmodelElementCollections/'
                                                     'ExampleSubmodelElementCollectionUnordered',
                                               id_type=model.KeyType.IRI),)),
        qualifier=None,
        kind=model.ModelingKind.INSTANCE)

    submodel = model.Submodel(
        identification=model.Identifier(id_='https://acplt.org/Test_Submodel',
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
        identification=model.Identifier(id_='https://acplt.org/Test_ConceptDescription',
                                        id_type=model.IdentifierType.IRI),
        is_case_of={model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                               value='http://acplt.org/DataSpecifications/'
                                                     'ConceptDescriptions/TestConceptDescription',
                                               id_type=model.KeyType.IRI),))},
        id_short='TestConceptDescription',
        category=None,
        description={'en-us': 'An example concept description  for the test application',
                     'de': 'Ein Beispiel-ConceptDescription für eine Test-Anwendung'},
        parent=None,
        administration=model.AdministrativeInformation(version='0.9',
                                                       revision='0'))
    return concept_description


def create_example_asset_administration_shell() -> \
        model.AssetAdministrationShell:
    """
    Creates an :class:`~aas.model.aas.AssetAdministrationShell` with references to an example
    :class:`~aas.model.aas.Asset` and :class:`~aas.model.submodel.Submodel` and includes a given
    :class:`~aas.model.concept.ConceptDictionary`

    :return: example :class:`~aas.model.aas.AssetAdministrationShell`
    """

    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.INSTANCE,
        global_asset_id=model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                   value='http://acplt.org/TestAsset/',
                                                   id_type=model.KeyType.IRI),)),
        specific_asset_id={model.IdentifierKeyValuePair(key="TestKey",
                                                        value="TestValue",
                                                        external_subject_id=model.Reference((
                                                            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                                      value='http://acplt.org/SpecificAssetId/',
                                                                      id_type=model.KeyType.IRI),))), },
        bill_of_material={model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                        value='http://acplt.org/Submodels/Assets/'
                                                              'TestAsset/BillOfMaterial',
                                                        id_type=model.KeyType.IRI),),
                                             model.Submodel), },
        default_thumbnail=None)

    asset_administration_shell = model.AssetAdministrationShell(
        asset_information=asset_information,
        identification=model.Identifier(id_='https://acplt.org/Test_AssetAdministrationShell',
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
                                                value='https://acplt.org/Test_Submodel',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel),
                  model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                value='http://acplt.org/Submodels/Assets/TestAsset/Identification',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel),
                  model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                value='http://acplt.org/Submodels/Assets/TestAsset/BillOfMaterial',
                                                id_type=model.KeyType.IRI),),
                                     model.Submodel),
                  },
        view=[],
        derived_from=model.AASReference((model.Key(type_=model.KeyElements.ASSET_ADMINISTRATION_SHELL,
                                                   value='https://acplt.org/TestAssetAdministrationShell2',
                                                   id_type=model.KeyType.IRI),),
                                        model.AssetAdministrationShell))
    return asset_administration_shell


##############################################################################
# check functions for checking if an given object is the same as the example #
##############################################################################
def check_example_asset_identification_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_asset_identification_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_example_bill_of_material_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_bill_of_material_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_example_concept_description(checker: AASDataChecker, concept_description: model.ConceptDescription) -> None:
    expected_concept_description = create_example_concept_description()
    checker.check_concept_description_equal(concept_description, expected_concept_description)


def check_example_asset_administration_shell(checker: AASDataChecker, shell: model.AssetAdministrationShell) -> None:
    expected_shell = create_example_asset_administration_shell()
    checker.check_asset_administration_shell_equal(shell, expected_shell)


def check_example_submodel(checker: AASDataChecker, submodel: model.Submodel) -> None:
    expected_submodel = create_example_submodel()
    checker.check_submodel_equal(submodel, expected_submodel)


def check_full_example(checker: AASDataChecker, obj_store: model.DictObjectStore) -> None:
    expected_data = create_full_example()
    checker.check_object_store(obj_store, expected_data)
