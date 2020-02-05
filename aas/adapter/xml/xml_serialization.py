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
Module for serializing Asset Administration Shell data to the official XML format

How to use:
- For generating an XML-File from a model.registry.AbstractObjectStore, check out the function "write_aas_xml_file".
- For serializing any object to an xml.etree.ElementTree.Element, that fits the XML specification from 'Details of the
  Asset Administration Shell', chapter 5.4, check out "aas_object_to_xml"
"""

import xml.etree.ElementTree as ElTree
from typing import Dict, IO, Optional
import base64

from aas import model


# ##############################################################
# functions to manipulate ElTree.Elements more effectively
# ##############################################################

# Namespace definition
NS_AAS = "{http://www.admin-shell.io/aas/2/0}"
NS_ABAC = "{http://www.admin-shell.io/aas/abac/2/0}"
NS_AAS_COMMON = "{http://www.admin-shell.io/aas_common/2/0}"
NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
NS_IEC = "{http://www.admin-shell.io/IEC61360/2/0}"


def generate_element(name: str,
                     text: Optional[str] = None,
                     attributes: Optional[Dict] = None) -> ElTree.Element:
    """
    generate an ElementTree.Element object

    :param name: namespace+tag_name of the element
    :param text: Text of the element. Default is None
    :param attributes: Attributes of the elements in form of a dict {"attribute_name": "attribute_content"}
    :return: ElementTree.Element object
    """
    et_element = ElTree.Element(name)
    if text:
        et_element.text = text
    if attributes:
        for attribute in attributes:
            et_element.set(attribute, attributes[attribute])
    return et_element


def boolean_to_xml(obj: bool) -> str:
    """
    serialize a boolean to XML

    :param obj: boolean
    :return: string in the XML accepted form
    """
    if obj is True:
        return "true"
    else:
        return "false"


def generate_parent(namespace: str, tag: str, obj: object) -> ElTree.Element:
    """
    generates a parent element from its tag-name and object. Inserts abstract classes

    :param namespace: namespace of the resulting element
    :param tag: tag of the resulting element
    :param obj: model object
    :return: ElementTree that includes the serialized abstract classes
    """
    return abstract_classes_to_xml(generate_element(name=namespace+tag), namespace, obj)


# ##############################################################
# dicts to serialize enum classes to xml
# ##############################################################


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


# ##############################################################
# transformation functions to serialize abstract classes from model.base
# ##############################################################


def abstract_classes_to_xml(elm: ElTree.Element, namespace: str, obj: object) -> ElTree.Element:
    """
    transformation function to serialize abstract classes from model.base which are inherited by many classes.

    If the object obj is inheriting from an abstract class, this function adds the serialized information of those
    abstract classes to the given parent element

    :param elm: parent element that the abstract classes should be serialized for
    :param namespace: namespace of the children elements
    :param obj: an object of the AAS
    :return: parent element with the serialized information from the abstract classes
    """
    if isinstance(obj, model.Referable):
        elm.append(generate_element(name=namespace+"idShort", text=obj.id_short))
        if obj.category:
            elm.append(generate_element(name=namespace+"category", text=obj.category))
        if obj.description:
            elm.append(lang_string_set_to_xml(obj.description, namespace=namespace, tag="description"))
    if isinstance(obj, model.Identifiable):
        elm.append(generate_element(name=namespace+"identification",
                                    text=obj.identification.id,
                                    attributes={"idType": IDENTIFIER_TYPES[obj.identification.id_type]}))
        if obj.administration:
            et_administration = generate_element(name=namespace+"administration")
            if obj.administration.version:
                et_administration.append(generate_element(name=namespace+"version", text=obj.administration.version))
                if obj.administration.revision:
                    et_administration.append(generate_element(name=namespace+"revision",
                                                              text=obj.administration.revision))
            elm.append(et_administration)
    if isinstance(obj, model.HasSemantics):
        if obj.semantic_id:
            elm.append(reference_to_xml(obj.semantic_id, namespace=namespace, tag="semanticId"))
    if isinstance(obj, model.HasKind):
        if obj.kind is model.ModelingKind.TEMPLATE:
            elm.append(generate_element(name=namespace+"kind", text="Template"))
        else:
            # then modeling-kind is Instance
            elm.append(generate_element(name=namespace+"kind", text="Instance"))
    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            et_qualifiers = generate_element(name=namespace+"qualifier", text=None)
            for qualifier in obj.qualifier:
                pass
                # et_qualifiers.append(qualifier_to_xml(qualifier, namespace, tag="qualifiers"))
                # TODO: obj.qualifier is Set[Constraint] not qualifier
                # todo: seems like the XSD-schema messed up the plural "s"?
                # todo: formula and qualifier seem not to be implemented yet
    return elm


# ##############################################################
# transformation functions to serialize classes from model.base
# ##############################################################


def lang_string_set_to_xml(obj: model.LangStringSet, namespace: str, tag: str) -> ElTree.Element:
    """
    serialization of objects of class LangStringSet to XML

    :param obj: object of class LangStringSet
    :param namespace: namespace of the element
    :param tag: tag of the returned element
    :return: serialized ElementTree object
    """
    et_lss = generate_element(name=namespace+tag)
    for language in obj:
        et_lss.append(generate_element(name=namespace+"langString",
                                       text=obj[language],
                                       attributes={"lang": language}))
    return et_lss


def administrative_information_to_xml(obj: model.AdministrativeInformation,
                                      namespace: str,
                                      tag: str = "administration") -> ElTree.Element:
    """
    serialization of objects of class AdministrativeInformation to XML

    :param obj: object of class AdministrativeInformation
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element. default is "administration"
    :return: serialized ElementTree object
    """
    et_administration = generate_parent(namespace, tag, obj)
    if obj.version:
        et_administration.append(generate_element(name=namespace+"version", text=obj.version))
        if obj.revision:
            et_administration.append(generate_element(name=namespace+"revision", text=obj.revision))
    return et_administration


def identifier_to_xml(obj: model.Identifier, namespace: str, tag: str = "identifier") -> ElTree.Element:
    """
    serialization of objects of class Identifier to XML

    :param obj: object of class Identifier
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element. default is "identifier"
    :return: serialized ElementTree object
    """
    et_identifier = generate_parent(namespace, tag, obj)
    et_identifier.append(generate_element(name=namespace+"id", text=obj.id))
    et_identifier.append(generate_element(name=namespace+"idType", text=IDENTIFIER_TYPES[obj.id_type]))
    return et_identifier


def reference_to_xml(obj: model.Reference, namespace: str, tag: str) -> ElTree.Element:
    """
    serialization of objects of class Reference to XML

    :param obj: object of class Reference
    :param namespace: namespace of the returned element
    :param tag: tag of the returned element
    :return: serialized ElementTree
    """
    et_reference = generate_element(name=namespace+tag)
    et_keys = generate_element(name=namespace+"keys")
    for aas_key in obj.key:
        et_keys.append(generate_element(name=namespace + "key",
                                        text=aas_key.value,
                                        attributes={"idType": KEY_TYPES[aas_key.id_type],
                                                    "local": boolean_to_xml(aas_key.local),
                                                    "type": KEY_ELEMENTS[aas_key.type_]}))
    et_reference.append(et_keys)
    return et_reference


def formula_to_xml(obj: model.Formula, namespace: str, tag: str = "formula") -> ElTree.Element:
    """
    serialization of objects of class Formula to XML

    :param obj: object of class Formula
    :param namespace: namespace of the serialized element
    :param tag: tag of the ElementTree object, default is "formula"
    :return: serialized ElementTree object
    """
    et_formula = generate_parent(namespace, tag, obj)
    if obj.depends_on:
        et_depends_on = generate_element(name=namespace+"dependsOnRefs", text=None)
        for aas_reference in obj.depends_on:
            et_depends_on.append(reference_to_xml(aas_reference, namespace, "reference"))
        et_formula.append(et_depends_on)
    return et_formula


def qualifier_to_xml(obj: model.Qualifier, namespace: str, tag: str = "qualifier") -> ElTree.Element:
    """
    serialization of objects of class Qualifier to XML

    :param obj: object of class Qualifier
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized ElementTree object, default is "qualifier"
    :return: serialized ElementTreeObject
    """
    et_qualifier = generate_parent(namespace, tag, obj)
    if obj.value:
        et_qualifier.append(generate_element(namespace+"value", text=obj.value))
    if obj.value_id:
        et_qualifier.append(reference_to_xml(obj.value_id, namespace, "valueId"))
    et_qualifier.append(generate_element(namespace+"valueType", text=obj.value_type))
    et_qualifier.append(generate_element(namespace+"type", text=obj.type_))
    return et_qualifier


def value_reference_pair_to_xml(obj: model.ValueReferencePair,
                                namespace: str,
                                tag: str = "valueReferencePair") -> ElTree.Element:
    """
    serialization of objects of class ValueReferencePair to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization
          check namespace and tag

    :param obj: object of class ValueReferencePair
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "valueReferencePair"
    :return: serialized ElementTree object
    """
    et_vrp = generate_parent(namespace, tag, obj)
    et_vrp.append(generate_element(namespace+"value", text=obj.value))
    et_vrp.append(reference_to_xml(obj.value_id, namespace, "valueId"))
    return et_vrp


def value_list_to_xml(obj: model.ValueList,
                      namespace: str,
                      tag: str = "valueList") -> ElTree.Element:
    """
    serialization of objects of class ValueList to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueList
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "valueList"
    :return: serialized ElementTree object
    """
    et_value_list = generate_parent(namespace, tag, obj)
    for aas_reference_pair in obj:
        et_value_list.append(value_reference_pair_to_xml(aas_reference_pair, namespace))
    return et_value_list


# ##############################################################
# transformation functions to serialize classes from model.aas
# ##############################################################


def view_to_xml(obj: model.View, namespace: str, tag: str = "view") -> ElTree.Element:
    """
    serialization of objects of class View to XML

    :param obj: object of class View
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the ElementTree object. default is "view"
    :return: serialized ElementTree object
    """
    et_view = generate_parent(namespace, tag, obj)
    if obj.contained_element:
        et_contained_elements = generate_element(name=namespace+"containedElements")
        for contained_element in obj.contained_element:
            et_contained_elements.append(reference_to_xml(contained_element, namespace, "containedElementRef"))
        et_view.append(et_contained_elements)
    return et_view


def asset_to_xml(obj: model.Asset, namespace: str, tag: str = "asset") -> ElTree.Element:
    """
    serialization of objects of class Asset to XML

    :param obj: object of class Asset
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the ElementTree object. default is "asset"
    :return: serialized ElementTree object
    """
    et_asset = generate_parent(namespace, tag, obj)
    et_asset.append(generate_element(name=namespace+"kind", text=ASSET_KIND[obj.kind]))
    if obj.asset_identification_model:
        et_asset.append(reference_to_xml(obj.asset_identification_model, namespace, "assetIdentificationModelRef"))
    if obj.bill_of_material:
        et_asset.append(reference_to_xml(obj.bill_of_material, namespace, "billOfMaterialRef"))
    return et_asset


def concept_description_to_xml(obj: model.ConceptDescription,
                               namespace: str,
                               tag: str = "conceptDescription") -> ElTree.Element:
    """
    serialization of objects of class ConceptDescription to XML

    :param obj: object of class ConceptDescription
    :param namespace: namespace of the serialized element
    :param tag: tag of the ElementTree object. default is "conceptDescription"
    :return: serialized ElementTree object
    """
    et_concept_description = generate_parent(namespace, tag, obj)
    if obj.is_case_of:
        for reference in obj.is_case_of:
            et_concept_description.append(reference_to_xml(reference, namespace, "isCaseOf"))
    return et_concept_description


def concept_dictionary_to_xml(obj: model.ConceptDictionary,
                              namespace: str,
                              tag: str = "conceptDictionary") -> ElTree.Element:
    """
    serialization of objects of class ConceptDictionary to XML

    :param obj: object of class ConceptDictionary
    :param namespace: namespace of the serialized element
    :param tag: tag of the ElementTree object. default is "conceptDictionary"
    :return: serialized ElementTree object
    """
    et_concept_dictionary = generate_parent(namespace, tag, obj)
    if obj.concept_description:
        et_concept_descriptions_refs = generate_element(namespace+"conceptDescriptionRefs")
        for reference in obj.concept_description:
            et_concept_descriptions_refs.append(reference_to_xml(reference, namespace, "conceptDescriptionRef"))
        et_concept_dictionary.append(et_concept_descriptions_refs)
    return et_concept_dictionary


def asset_administration_shell_to_xml(obj: model.AssetAdministrationShell,
                                      namespace: str,
                                      tag: str = "assetAdministrationShell") -> ElTree.Element:
    """
    serialization of objects of class AssetAdministrationShell to XML

    :param obj: object of class AssetAdministrationShell
    :param namespace: namespace of the serialized element
    :param tag: tag of the ElementTree object. default is "assetAdministrationShell"
    :return: serialized ElementTree object
    """
    et_aas = generate_parent(namespace, tag, obj)
    et_aas.append(reference_to_xml(obj.asset, namespace=namespace, tag="assetRef"))
    if obj.derived_from:
        et_aas.append(reference_to_xml(obj.derived_from, namespace=namespace, tag="derivedFrom"))
    if obj.submodel_:
        et_submodels = generate_element(namespace+"submodelRefs")
        for reference in obj.submodel_:
            et_submodels.append(reference_to_xml(reference, namespace=namespace, tag="submodelRef"))
        et_aas.append(et_submodels)
    if obj.view:
        et_views = generate_element(namespace+"views")
        for view in obj.view:
            et_views.append(view_to_xml(view, namespace, "view"))
        et_aas.append(et_views)
    if obj.concept_dictionary:
        et_concept_dictionaries = generate_element(namespace+"conceptDictionaries")
        for concept_dictionary in obj.concept_dictionary:
            et_concept_dictionaries.append(concept_dictionary_to_xml(concept_dictionary,
                                                                     namespace,
                                                                     "conceptDictionary"))
        et_aas.append(et_concept_dictionaries)
    if obj.security_:
        et_aas.append(security_to_xml(obj.security_, namespace=NS_ABAC, tag="security"))
    return et_aas


# ##############################################################
# transformation functions to serialize classes from model.security
# ##############################################################


def security_to_xml(obj: model.Security,
                    namespace: str,
                    tag: str = "security") -> ElTree.Element:
    """
    serialization of objects of class Security to XML

    todo: This is not yet implemented

    :param obj: object of class Security
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional). Default is "security"
    :return: serialized ElementTree object
    """
    return generate_parent(namespace, tag, obj)


# ##############################################################
# transformation functions to serialize classes from model.submodel
# ##############################################################


def submodel_element_to_xml(obj: model.SubmodelElement,
                            namespace: str,
                            tag: str = "submodelElement") -> ElTree.Element:
    """
    serialization of objects of class SubmodelElement to XML

    todo: this seems to miss in the json implementation? Because it consists only of inherited parameters?
    todo: this seems to be different in the schema and in our implementation

    :param obj: object of class SubmodelElement
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "submodelElement"
    :return: serialized ElementTree object
    """
    return generate_parent(namespace, tag, obj)


def submodel_to_xml(obj: model.Submodel,
                    namespace: str,
                    tag: str = "submodel") -> ElTree.Element:
    """
    serialization of objects of class Submodel to XML

    :param obj: object of class Submodel
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional). Default is "submodel"
    :return: serialized ElementTree object
    """
    et_submodel = generate_parent(namespace, tag, obj)
    if obj.submodel_element:
        et_submodel_elements = generate_element(namespace+"submodelElements")
        for submodel_element in obj.submodel_element:
            et_submodel_elements.append(submodel_element_to_xml(submodel_element, namespace))
        et_submodel.append(et_submodel_elements)
    return et_submodel


def data_element_to_xml(obj: model.DataElement,
                        namespace: str,
                        tag: str = "dataElement") -> ElTree.Element:
    """
    serialization of objects of class DataElement to XML

    :param obj: object of class DataElement
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "dataElement"
    :return: serialized ElementTree object
    """
    return generate_parent(namespace, tag, obj)


def property_to_xml(obj: model.Property,
                    namespace: str,
                    tag: str = "property") -> ElTree.Element:
    """
    serialization of objects of class Property to XML

    :param obj: object of class Property
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "property"
    :return: serialized ElementTree object
    """
    et_property = generate_parent(namespace, tag, obj)
    et_property.append(generate_element(namespace+"valueType", text=obj.value_type))
    if obj.value:
        et_property.append(generate_element(namespace+"value", text=obj.value))
    if obj.value_id:
        et_property.append(reference_to_xml(obj.value_id, namespace, "valueId"))
    return et_property


def multi_language_property_to_xml(obj: model.MultiLanguageProperty,
                                   namespace: str,
                                   tag: str = "multiLanguageProperty") -> ElTree.Element:
    """
    serialization of objects of class MultiLanguageProperty to XML

    :param obj: object of class MultiLanguageProperty
    :param namespace: namespace of the element
    :param tag: tag of the serialized element (optional), default is "multiLanguageProperty"
    :return: serialized ElementTree object
    """
    et_multi_language_property = generate_parent(namespace, tag, obj)
    if obj.value:
        et_multi_language_property.append(lang_string_set_to_xml(obj.value, namespace=namespace, tag="value"))
    if obj.value_id:
        et_multi_language_property.append(reference_to_xml(obj.value_id, namespace, "valueId"))
    return et_multi_language_property


def range_to_xml(obj: model.Range,
                 namespace: str,
                 tag: str = "range") -> ElTree.Element:
    """
    serialization of objects of class Range to XML

    :param obj: object of class Range
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the serialized element (optional), default is "range
    :return: serialized ElementTree object
    """
    et_range = generate_parent(namespace, tag, obj)
    et_range.append(generate_element(name=namespace+"valueType", text=obj.value_type))
    if obj.min_:
        et_range.append(generate_element(name=namespace+"min", text=obj.min_))
    if obj.max_:
        et_range.append(generate_element(name=namespace+"max", text=obj.max_))
    return et_range


def blob_to_xml(obj: model.Blob,
                namespace: str,
                tag: str = "blob") -> ElTree.Element:
    """
    serialization of objects of class Blob to XML

    :param obj: object of class Blob
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "blob"
    :return: serialized ElementTree object
    """
    et_blob = generate_parent(namespace, tag, obj)
    et_blob.append(generate_element(namespace+"mimeType", text=obj.mime_type))
    et_value = ElTree.Element(namespace+"value")
    if obj.value is not None:
        et_value.text = base64.b64encode(obj.value).decode()
    et_blob.append(et_value)
    return et_blob


def file_to_xml(obj: model.File,
                namespace: str,
                tag: str = "file") -> ElTree.Element:
    """
    serialization of objects of class File to XML

    :param obj: object of class File
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "file"
    :return: serialized ElementTree object
    """
    et_file = generate_parent(namespace, tag, obj)
    et_file.append(generate_element(namespace+"value", text=obj.value))
    et_file.append(generate_element(namespace+"mimeType", text=obj.mime_type))
    return et_file


def reference_element_to_xml(obj: model.ReferenceElement,
                             namespace: str,
                             tag: str = "referenceElement") -> ElTree.Element:
    """
    serialization of objects of class ReferenceElement to XMl

    :param obj: object of class ReferenceElement
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the serialized element (optional), default is "referenceElement"
    :return: serialized ElementTree object
    """
    et_reference_element = generate_parent(namespace, tag, obj)
    if obj.value:
        et_reference_element.append(reference_to_xml(obj.value, namespace, "value"))
    return et_reference_element


def submodel_element_collection_to_xml(obj: model.SubmodelElementCollection,
                                       namespace: str,
                                       tag: str = "submodelElementCollection") -> ElTree.Element:
    """
    serialization of objects of class SubmodelElementCollection to XML

    Note that we do not have parameter "allowDuplicates" in out implementation

    :param obj: object of class SubmodelElementCollection
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the serialized element (optional), default is "submodelElementCollection"
    :return: serialized ElementTree object
    """
    et_submodel_element_collection = generate_parent(namespace, tag, obj)
    if obj.value:
        et_value = generate_element(namespace+"value")
        for submodel_element in obj.value:
            et_value.append(submodel_element_to_xml(submodel_element, namespace))
        et_submodel_element_collection.append(et_value)
    et_submodel_element_collection.append(generate_element(namespace+"ordered", text=boolean_to_xml(obj.ordered)))
    return et_submodel_element_collection


def relationship_element_to_xml(obj: model.RelationshipElement,
                                namespace: str,
                                tag: str = "relationshipElement") -> ElTree.Element:
    """
    serialization of objects of class RelationshipElement to XML

    :param obj: object of class RelationshipElement
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "relationshipElement"
    :return: serialized ELementTree object
    """
    et_relationship_element = generate_parent(namespace, tag, obj)
    et_relationship_element.append(reference_to_xml(obj.first, namespace, "first"))
    et_relationship_element.append(reference_to_xml(obj.second, namespace, "second"))
    return et_relationship_element


def annotated_relationship_element_to_xml(obj: model.AnnotatedRelationshipElement,
                                          namespace: str,
                                          tag: str = "annotatedRelationshipElement") -> ElTree.Element:
    """
    serialization of objects of class AnnotatedRelationshipElement to XML

    todo: in the schema, annotatedRelationshipElement is of type relationshipElement_t, so there is no way to store
        the annotations in the schema

    :param obj: object of class AnnotatedRelationshipElement
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "annotatedRelationshipElement
    :return: serialized ElementTree object
    """
    et_annotated_relationship_element = relationship_element_to_xml(obj, namespace, tag)
    if obj.annotation:
        et_annotations = generate_element(name=""+"annotations")
        for ref in obj.annotation:
            et_annotations.append(reference_to_xml(ref, namespace="", tag="annotation"))
        et_annotated_relationship_element.append(et_annotations)
    return et_annotated_relationship_element


def operation_variable_to_xml(obj: model.OperationVariable,
                              namespace: str,
                              tag: str = "operationVariable") -> ElTree.Element:
    """
    serialization of objects of class OperationVariable to XML

    :param obj: object of class OperationVariable
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "operationVariable"
    :return: serialized ElementTree object
    """
    et_operation_variable = generate_parent(namespace, tag, obj)
    et_operation_variable.append(submodel_element_to_xml(obj.value, namespace, "value"))
    return et_operation_variable


def operation_to_xml(obj: model.Operation,
                     namespace: str,
                     tag: str = "operation") -> ElTree.Element:
    """
    serialization of objects of class Operation to XML

    :param obj: object of class Operation
    :param namespace: namespace of the serialized element
    :param tag: namespace+tag of the serialized element (optional), default is "operation"
    :return: serialized ElementTree object
    """
    et_operation = generate_parent(namespace, tag, obj)
    if obj.input_variable:
        et_input_variable = generate_element(namespace+"inputVariable")
        for input_ov in obj.input_variable:
            et_input_variable.append(operation_variable_to_xml(input_ov, namespace, "operationVariable"))
        et_operation.append(et_input_variable)
    if obj.output_variable:
        et_output_variable = generate_element(namespace+"outputVariable")
        for output_ov in obj.output_variable:
            et_output_variable.append(operation_variable_to_xml(output_ov, namespace, "operationVariable"))
        et_operation.append(et_output_variable)
    if obj.in_output_variable:
        et_in_output_variable = generate_element(namespace+"inoutputVariable")
        for in_out_ov in obj.in_output_variable:
            et_in_output_variable.append(operation_variable_to_xml(in_out_ov, namespace, "operationVariable"))
        et_operation.append(et_in_output_variable)
    return et_operation


def capability_to_xml(obj: model.Capability,
                      namespace: str,
                      tag: str = "capability") -> ElTree.Element:
    """
    serialization of objects of class Capability to XML

    todo: in the schema, a capability is a string

    :param obj: object of class Capability
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element, default is "capability"
    :return: serialized ElementTree object
    """
    et_capability = generate_parent(namespace, tag, obj)
    return et_capability


def entity_to_xml(obj: model.Entity,
                  namespace: str,
                  tag: str = "entity") -> ElTree.Element:
    """
    serialization of objects of class Entity to XML

    :param obj: object of class Entity
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "entity"
    :return: serialized ElementTree object
    """
    et_entity = generate_parent(namespace, tag, obj)
    et_entity.append(submodel_element_to_xml(obj.statement, namespace, tag="statements"))
    et_entity.append(generate_element(namespace+"entityType", text=ENTITY_TYPES[obj.entity_type]))
    if obj.asset:
        et_entity.append(reference_to_xml(obj.asset, namespace, "assetRef"))
    return et_entity


def basic_event_to_xml(obj: model.BasicEvent,
                       namespace: str,
                       tag: str = "basicEvent") -> ElTree.Element:
    """
    serialization of objects of class BasicEvent to XML

    :param obj: object of class BasicEvent
    :param namespace: namespace of the serialized element
    :param tag: tag of the serialized element (optional), default is "basicEvent"
    :return: serialized ElementTree object
    """
    et_basic_event = generate_parent(namespace, tag, obj)
    et_basic_event.append(reference_to_xml(obj.observed, namespace, "observed"))
    return et_basic_event


# ##############################################################
# general functions
# ##############################################################


def write_aas_xml_file(file: IO,
                       data: model.AbstractObjectStore) -> None:
    """
    Write a set of AAS objects to an Asset Administration Shell XML file according to 'Details of the Asset
    Administration Shell', chapter 5.4

    :param file: A file-like object to write the XML-serialized data to
    :param data: ObjectStore which contains different objects of the AAS meta model which should be serialized to an
                 XML file
    """
    # separate different kind of objects
    assets = []
    asset_administration_shells = []
    submodels = []
    concept_descriptions = []
    for obj in data:
        if isinstance(obj, model.Asset):
            assets.append(obj)
        if isinstance(obj, model.AssetAdministrationShell):
            asset_administration_shells.append(obj)
        if isinstance(obj, model.Submodel):
            submodels.append(obj)
        if isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)

    # serialize objects to XML
    ElTree.register_namespace("aas", "http://www.admin-shell.io/aas/2/0")
    ElTree.register_namespace("abac", "http://www.admin-shell.io/aas/abac/2/0")
    ElTree.register_namespace("aas_common", "http://www.admin-shell.io/aas_common/2/0")
    ElTree.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    ElTree.register_namespace("IEC", "http://www.admin-shell.io/IEC61360/2/0")
    root = ElTree.Element("aasenv")
    # since it seems impossible to specify the xsi:schemaLocation, I am adding it per hand
    root.set("xsi:schemaLocation", "http://www.admin-shell.io/aas/1/0 AAS.xsd "
                                   "http://www.admin-shell.io/IEC61360/1/0IEC61360.xsd ")

    et_asset_administration_shells = ElTree.Element(NS_AAS + "assetAdministrationShells")
    for aas_obj in asset_administration_shells:
        et_asset_administration_shells.append(asset_administration_shell_to_xml(aas_obj, namespace=NS_AAS))
    et_assets = generate_element(NS_AAS + "assets")
    for ass_obj in assets:
        et_assets.append(asset_to_xml(ass_obj, namespace=NS_AAS))
    et_submodels = ElTree.Element(NS_AAS + "submodels")
    for sub_obj in submodels:
        et_submodels.append(submodel_to_xml(sub_obj, namespace=NS_AAS))
    et_concept_descriptions = ElTree.Element(NS_AAS + "conceptDescriptions")
    for con_obj in concept_descriptions:
        et_concept_descriptions.append(concept_description_to_xml(con_obj, namespace=NS_AAS))
    root.insert(0, et_concept_descriptions)
    root.insert(0, et_submodels)
    root.insert(0, et_assets)
    root.insert(0, et_asset_administration_shells)

    tree = ElTree.ElementTree(root)
    tree.write(file, encoding="UTF-8", xml_declaration=True, method="xml")
