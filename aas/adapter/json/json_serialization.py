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
Module for serializing Asset Administration Shell objects to the official JSON format

The module provides an custom JSONEncoder class `AASToJsonEncoder` to be used with the Python standard `json` module.
It contains a custom `default` function which converts PyAAS objects to simple python types for an automatical
JSON serialization. Additionally, there's the `write_aas_json_file()` function, that takes a complete ObjectStore and
writes all contained AAS objects into a JSON file.

This job is performed in an iterative approach: The `default()` function gets called for every object and checks if an
object is an PyAAS object. In this case, it calls a special function for the respective PyAAS class which converts the
object (but not the contained objects) into a simple Python dict, which is serializable. Any contained PyAAS objects
are included into the dict as they are to be converted later on. The special helper function
`abstract_classes_to_json()` is called by most of the conversion functions to handle all the attributes of abstract base
classes.
"""
import base64
import inspect
from typing import List
import json
from typing import Dict, IO
from ... import model


# ##########################################
# dicts to serialize enum values to json
# ##########################################

MODELING_KIND: Dict[model.ModelingKind, str] = {
    model.ModelingKind.TEMPLATE: 'Template',
    model.ModelingKind.INSTANCE: 'Instance'}

ASSET_KIND: Dict[model.AssetKind, str] = {
    model.AssetKind.TYPE: 'Type',
    model.AssetKind.INSTANCE: 'Instance'}

KEY_ELEMENTS: Dict[model.KeyElements, str] = {
    model.KeyElements.ASSET: 'Asset',
    model.KeyElements.ASSET_ADMINISTRATION_SHELL: 'AssetAdministrationShell',
    model.KeyElements.CONCEPT_DESCRIPTION: 'ConceptDescription',
    model.KeyElements.SUBMODEL: 'Submodel',
    model.KeyElements.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement',
    model.KeyElements.BASIC_EVENT: 'BasicEvent',
    model.KeyElements.BLOB: 'Blob',
    model.KeyElements.CAPABILITY: 'Capability',
    model.KeyElements.CONCEPT_DICTIONARY: 'ConceptDictionary',
    model.KeyElements.DATA_ELEMENT: 'DataElement',
    model.KeyElements.ENTITY: 'Entity',
    model.KeyElements.EVENT: 'Event',
    model.KeyElements.FILE: 'File',
    model.KeyElements.MULTI_LANGUAGE_PROPERTY: 'MultiLanguageProperty',
    model.KeyElements.OPERATION: 'Operation',
    model.KeyElements.PROPERTY: 'Property',
    model.KeyElements.RANGE: 'Range',
    model.KeyElements.REFERENCE_ELEMENT: 'ReferenceElement',
    model.KeyElements.RELATIONSHIP_ELEMENT: 'RelationshipElement',
    model.KeyElements.SUBMODEL_ELEMENT: 'SubmodelElement',
    model.KeyElements.SUBMODEL_ELEMENT_COLLECTION: 'SubmodelElementCollection',
    model.KeyElements.VIEW: 'View',
    model.KeyElements.GLOBAL_REFERENCE: 'GlobalReference',
    model.KeyElements.FRAGMENT_REFERENCE: 'FragmentReference'}

KEY_TYPES: Dict[model.KeyType, str] = {
    model.KeyType.CUSTOM: 'Custom',
    model.KeyType.IRDI: 'IRDI',
    model.KeyType.IRI: 'IRI',
    model.KeyType.IDSHORT: 'IdShort',
    model.KeyType.FRAGMENT_ID: 'FragmentId'}

IDENTIFIER_TYPES: Dict[model.IdentifierType, str] = {
    model.IdentifierType.CUSTOM: 'Custom',
    model.IdentifierType.IRDI: 'IRDI',
    model.IdentifierType.IRI: 'IRI'}

ENTITY_TYPES: Dict[model.EntityType, str] = {
    model.EntityType.CO_MANAGED_ENTITY: 'CoManagedEntity',
    model.EntityType.SELF_MANAGED_ENTITY: 'SelfManagedEntity'}


def abstract_classes_to_json(obj: object) -> Dict[str, object]:
    """
    transformation function to serialize abstract classes from model.base which are inherited by many classes

    :param obj: object which must be serialized
    :return: dict with the serialized attributes of the abstract classes this object inherits from
    """
    data = {}
    if isinstance(obj, model.Referable):
        data['idShort'] = obj.id_short
        if obj.category:
            data['category'] = obj.category
        if obj.description:
            data['description'] = lang_string_set_to_json(obj.description)
        try:
            ref_type = next(iter(t for t in inspect.getmro(type(obj)) if t in model.KEY_ELEMENTS_CLASSES))
        except StopIteration as e:
            raise TypeError("Object of type {} is Referable but does not inherit from a known AAS type"
                            .format(obj.__class__.__name__)) from e
        data['modelType'] = {'name': ref_type.__name__}
    if isinstance(obj, model.Identifiable):
        data['identification'] = obj.identification
        if obj.administration:
            data['administration'] = obj.administration
    if isinstance(obj, model.HasDataSpecification):
        if obj.data_specification:
            data['embeddedDataSpecification'] = list(obj.data_specification)
    if isinstance(obj, model.HasSemantics):
        if obj.semantic_id:
            data['semanticId'] = obj.semantic_id
    if isinstance(obj, model.HasKind):
        if obj.kind is model.ModelingKind.TEMPLATE:
            data['kind'] = MODELING_KIND[obj.kind]
    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            data['qualifiers'] = list(obj.qualifier)
    return data


# #############################################################
# transformation functions to serialize classes from model.base
# #############################################################

def lang_string_set_to_json(obj: model.LangStringSet) -> List[Dict[str, object]]:
    return [{'language': k, 'text': v}
            for k, v in obj.items()]


def key_to_json(obj: model.Key) -> Dict[str, object]:
    """
    serialization of an object from class Key to json

    :param obj: object of class Key
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'type': KEY_ELEMENTS[obj.type_],
                 'idType': KEY_TYPES[obj.id_type],
                 'value': obj.value,
                 'local': obj.local})
    return data


def administrative_information_to_json(obj: model.AdministrativeInformation) -> Dict[str, object]:
    """
    serialization of an object from class AdministrativeInformation to json

    :param obj: object of class AdministrativeInformation
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.version:
        data['version'] = obj.version
        if obj.revision:
            data['revision'] = obj.revision
    return data


def identifier_to_json(obj: model.Identifier) -> Dict[str, object]:
    """
    serialization of an object from class Identifier to json

    :param obj: object of class Identifier
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['id'] = obj.id
    data['idType'] = IDENTIFIER_TYPES[obj.id_type]
    return data


def reference_to_json(obj: model.Reference) -> Dict[str, object]:
    """
    serialization of an object from class Reference to json

    :param obj: object of class Reference
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['keys'] = list(obj.key)
    return data


def constraint_to_json(obj: model.Constraint) -> Dict[str, object]:  # TODO check if correct for each class
    """
    serialization of an object from class Constraint to json

    :param obj: object of class Constraint
    :return: dict with the serialized attributes of this object
    """
    CONSTRAINT_CLASSES = [model.Qualifier, model.Formula]
    try:
        const_type = next(iter(t for t in inspect.getmro(type(obj)) if t in CONSTRAINT_CLASSES))
    except StopIteration as e:
        raise TypeError("Object of type {} is a Constraint but does not inherit from a known AAS Constraint type"
                        .format(obj.__class__.__name__)) from e
    return {'modelType': {'name': const_type.__name__}}


def namespace_to_json(obj):  # not in specification yet
    """
    serialization of an object from class Namespace to json

    :param obj: object of class Namespace
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    return data


def formula_to_json(obj: model.Formula) -> Dict[str, object]:
    """
    serialization of an object from class Formula to json

    :param obj: object of class Formula
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update(constraint_to_json(obj))
    if obj.depends_on:
        data['dependsOn'] = list(obj.depends_on)
    return data


def qualifier_to_json(obj: model.Qualifier) -> Dict[str, object]:
    """
    serialization of an object from class Qualifier to json

    :param obj: object of class Qualifier
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update(constraint_to_json(obj))
    if obj.value:
        data['value'] = obj.value
    if obj.value_id:
        data['valueId'] = obj.value_id
    data['valueType'] = obj.value_type
    data['type'] = obj.type_
    return data


def value_reference_pair_to_json(obj):
    """
    serialization of an object from class ValueReferencePair to json

    :param obj: object of class ValueReferencePair
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'value': obj.value,
                 'valueId': obj.valueId,
                 'valueType': obj.value_type})
    return data


def value_list_to_json(obj):
    """
    serialization of an object from class ValueList to json

    :param obj: object of class ValueList
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['valueReferencePairTypes'] = obj.value_reference_pair_type
    return data


# ############################################################
# transformation functions to serialize classes from model.aas
# ############################################################

def view_to_json(obj: model.View) -> Dict[str, object]:
    """
    serialization of an object from class View to json

    :param obj: object of class View
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.contained_element:
        data['containedElements'] = list(obj.contained_element)
    return data


def asset_to_json(obj: model.Asset) -> Dict[str, object]:
    """
    serialization of an object from class Asset to json

    :param obj: object of class Asset
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['kind'] = ASSET_KIND[obj.kind]
    if obj.asset_identification_model:
        data['assetIdentificationModel'] = obj.asset_identification_model
    if obj.bill_of_material:
        data['billOfMaterial'] = obj.bill_of_material
    return data


def concept_description_to_json(obj: model.ConceptDescription) -> Dict[str, object]:
    """
    serialization of an object from class ConceptDescription to json

    :param obj: object of class ConceptDescription
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.is_case_of:
        data['isCaseOf'] = list(obj.is_case_of)
    return data


def concept_dictionary_to_json(obj: model.ConceptDictionary) -> Dict[str, object]:
    """
    serialization of an object from class ConceptDictionary to json

    :param obj: object of class ConceptDictionary
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.concept_description:
        data['conceptDescriptions'] = list(obj.concept_description)
    return data


def asset_administration_shell_to_json(obj: model.AssetAdministrationShell) -> Dict[str, object]:
    """
    serialization of an object from class AssetAdministrationShell to json

    :param obj: object of class AssetAdministrationShell
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update(namespace_to_json(obj))
    if obj.derived_from:
        data["derivedFrom"] = obj.derived_from
    data["asset"] = obj.asset
    if obj.submodel_:
        data["submodels"] = list(obj.submodel_)
    if obj.view:
        data["views"] = list(obj.view)
    if obj.concept_dictionary:
        data["conceptDictionaries"] = list(obj.concept_dictionary)
    if obj.security_:
        data["security"] = obj.security_
    return data


# #################################################################
# transformation functions to serialize classes from model.security
# #################################################################


def security_to_json(obj: model.Security) -> Dict[str, object]:  # has no attributes in our implementation
    """
    serialization of an object from class Security to json

    :param obj: object of class Security
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    return data


# #################################################################
# transformation functions to serialize classes from model.submodel
# #################################################################

def submodel_to_json(obj: model.Submodel) -> Dict[str, object]:  # TODO make kind optional
    """
    serialization of an object from class Submodel to json

    :param obj: object of class Submodel
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.submodel_element != set():
        data['submodelElements'] = list(obj.submodel_element)
    return data


def data_element_to_json(obj: model.DataElement) -> Dict[str, object]:  # no attributes in specification yet
    """
    serialization of an object from class DataElement to json

    :param obj: object of class DataElement
    :return: dict with the serialized attributes of this object
    """
    return {}


def property_to_json(obj: model.Property) -> Dict[str, object]:
    """
    serialization of an object from class Property to json

    :param obj: object of class Property
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['value'] = obj.value
    if obj.value_id:
        data['valueId'] = obj.value_id
    data['valueType'] = obj.value_type
    return data


def multi_language_property_to_json(obj: model.MultiLanguageProperty) -> Dict[str, object]:
    """
    serialization of an object from class MultiLanguageProperty to json

    :param obj: object of class MultiLanguageProperty
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = lang_string_set_to_json(obj.value)
    if obj.value_id:
        data['valueId'] = obj.value_id
    return data


def range_to_json(obj: model.Range) -> Dict[str, object]:
    """
    serialization of an object from class Range to json

    :param obj: object of class Range
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'valueType': obj.value_type, 'min': obj.min_, 'max': obj.max_})
    return data


def blob_to_json(obj: model.Blob) -> Dict[str, object]:
    """
    serialization of an object from class Blob to json

    :param obj: object of class Blob
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['mimeType'] = obj.mime_type
    if obj.value is not None:
        data['value'] = base64.b64encode(obj.value).decode()
    return data


def file_to_json(obj: model.File) -> Dict[str, object]:
    """
    serialization of an object from class File to json

    :param obj: object of class File
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'value': obj.value, 'mimeType': obj.mime_type})
    return data


def reference_element_to_json(obj: model.ReferenceElement) -> Dict[str, object]:
    """
    serialization of an object from class Reference to json

    :param obj: object of class Reference
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = obj.value
    return data


def submodel_element_collection_to_json(obj: model.SubmodelElementCollection) -> Dict[str, object]:
    """
    serialization of an object from class SubmodelElementCollectionOrdered and SubmodelElementCollectionUnordered to
    json

    :param obj: object of class SubmodelElementCollectionOrdered and SubmodelElementCollectionUnordered
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = list(obj.value)
    data['ordered'] = obj.ordered
    return data


def relationship_element_to_json(obj: model.RelationshipElement) -> Dict[str, object]:
    """
    serialization of an object from class RelationshipElement to json

    :param obj: object of class RelationshipElement
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'first': obj.first, 'second': obj.second})
    return data


def annotated_relationship_element_to_json(obj: model.AnnotatedRelationshipElement) -> Dict[str, object]:
    """
    serialization of an object from class AnnotatedRelationshipElement to json

    :param obj: object of class AnnotatedRelationshipElement
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data.update({'first': obj.first, 'second': obj.second})
    if obj.annotation:
        data['annotation'] = list(obj.annotation)
    return data


def operation_variable_to_json(obj: model.OperationVariable) -> Dict[str, object]:
    """
    serialization of an object from class OperationVariable to json

    :param obj: object of class OperationVariable
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['value'] = obj.value
    return data


def operation_to_json(obj: model.Operation) -> Dict[str, object]:
    """
    serialization of an object from class Operation to json

    :param obj: object of class Operation
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.input_variable:
        data['inputVariable'] = list(obj.input_variable)
    if obj.output_variable:
        data['outputVariable'] = list(obj.output_variable)
    if obj.in_output_variable:
        data['inoutputVariable'] = list(obj.in_output_variable)
    return data


def capability_to_json(obj: model.Capability) -> Dict[str, object]:  # no attributes in specification yet
    """
    serialization of an object from class Capability to json

    :param obj: object of class Capability
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    return data


def entity_to_json(obj: model.Entity) -> Dict[str, object]:
    """
    serialization of an object from class Entity to json

    :param obj: object of class Entity
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    if obj.statement:
        data['statements'] = list(obj.statement)
    data['entityType'] = ENTITY_TYPES[obj.entity_type]
    if obj.asset:
        data['asset'] = obj.asset
    return data


def event_to_json(obj: model.Event) -> Dict[str, object]:  # no attributes in specification yet
    """
    serialization of an object from class Event to json

    :param obj: object of class Event
    :return: dict with the serialized attributes of this object
    """
    return {}


def basic_event_to_json(obj: model.BasicEvent) -> Dict[str, object]:
    """
    serialization of an object from class BasicEvent to json

    :param obj: object of class BasicEvent
    :return: dict with the serialized attributes of this object
    """
    data = abstract_classes_to_json(obj)
    data['observed'] = obj.observed
    return data


class AASToJsonEncoder(json.JSONEncoder):
    """
    Custom JSONDecoder class to use the `json` module for serializing Asset Administration Shell data into the
    official JSON format

    The class overrides the `default()` method to transform PyAAS objects into dicts that may be serialized by the
    standard encode method. Typical usage:

        json_string = json.dumps(data, cls=AASToJsonEncoder)
    """

    def default(self, obj: object) -> object:
        if isinstance(obj, model.AssetAdministrationShell):
            return asset_administration_shell_to_json(obj)
        if isinstance(obj, model.Identifier):
            return identifier_to_json(obj)
        if isinstance(obj, model.AdministrativeInformation):
            return administrative_information_to_json(obj)
        if isinstance(obj, model.Reference):
            return reference_to_json(obj)
        if isinstance(obj, model.Key):
            return key_to_json(obj)
        if isinstance(obj, model.Asset):
            return asset_to_json(obj)
        if isinstance(obj, model.Submodel):
            return submodel_to_json(obj)
        if isinstance(obj, model.Operation):
            return operation_to_json(obj)
        if isinstance(obj, model.OperationVariable):
            return operation_variable_to_json(obj)
        if isinstance(obj, model.Capability):
            return capability_to_json(obj)
        if isinstance(obj, model.BasicEvent):
            return basic_event_to_json(obj)
        if isinstance(obj, model.Entity):
            return entity_to_json(obj)
        if isinstance(obj, model.View):
            return view_to_json(obj)
        if isinstance(obj, model.ConceptDictionary):
            return concept_dictionary_to_json(obj)
        if isinstance(obj, model.ConceptDescription):
            return concept_description_to_json(obj)
        if isinstance(obj, model.Property):
            return property_to_json(obj)
        if isinstance(obj, model.Range):
            return range_to_json(obj)
        if isinstance(obj, model.MultiLanguageProperty):
            return multi_language_property_to_json(obj)
        if isinstance(obj, model.File):
            return file_to_json(obj)
        if isinstance(obj, model.Blob):
            return blob_to_json(obj)
        if isinstance(obj, model.ReferenceElement):
            return reference_element_to_json(obj)
        if isinstance(obj, model.SubmodelElementCollection):
            return submodel_element_collection_to_json(obj)
        if isinstance(obj, model.AnnotatedRelationshipElement):
            return annotated_relationship_element_to_json(obj)
        if isinstance(obj, model.RelationshipElement):
            return relationship_element_to_json(obj)
        if isinstance(obj, model.Qualifier):
            return qualifier_to_json(obj)
        if isinstance(obj, model.Formula):
            return formula_to_json(obj)
        return super().default(obj)


def write_aas_json_file(file: IO, data: model.AbstractObjectStore, **kwargs) -> None:
    """
    Write a set of AAS objects to an Asset Adminstration Shell JSON file according to 'Details of the Asset
    Administration Shell', chapter 5.5

    :param file: A file-like object to write the JSON-serialized data to
    :param data: ObjectStore which contains different objects of the AAS meta model which should be serialized to a
                 JSON file
    :param kwargs: Additional keyword arguments to be passed to json.dump()
    """
    # separate different kind of objects
    assets = []
    asset_administation_shells = []
    submodels = []
    concept_descriptions = []
    for obj in data:
        if isinstance(obj, model.Asset):
            assets.append(obj)
        if isinstance(obj, model.AssetAdministrationShell):
            asset_administation_shells.append(obj)
        if isinstance(obj, model.Submodel):
            submodels.append(obj)
        if isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)

    # serialize object to json
    json.dump({
        'assetAdministrationShells': asset_administation_shells,
        'submodels': submodels,
        'assets': assets,
        'conceptDescriptions': concept_descriptions,
    }, file, cls=AASToJsonEncoder, **kwargs)
