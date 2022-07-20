# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
.. _adapter.xml.xml_serialization:

Module for serializing Asset Administration Shell data to the official XML format

How to use:

- For generating an XML-File from a :class:`~aas.model.provider.AbstractObjectStore`, check out the function
  :meth:`~aas.adapter.xml.xml_serialization.write_aas_xml_file`.
- For serializing any object to an XML fragment, that fits the XML specification from 'Details of the
  Asset Administration Shell', chapter 5.4, check out `<your_object_class_name_here>_to_xml()`. These functions return
  an :class:`xml.etree.ElementTree.Element` object to be serialized into XML.
"""

from lxml import etree  # type: ignore
from typing import Dict, IO, Optional
import base64

from basyx.aas import model
from .. import _generic


# ##############################################################
# functions to manipulate etree.Elements more effectively
# ##############################################################

# Namespace definition
NS_AAS = "{http://www.admin-shell.io/aas/3/0}"
NS_ABAC = "{http://www.admin-shell.io/aas/abac/3/0}"
NS_AAS_COMMON = "{http://www.admin-shell.io/aas_common/3/0}"
NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
NS_XS = "{http://www.w3.org/2001/XMLSchema}"
NS_IEC = "{http://www.admin-shell.io/IEC61360/3/0}"
NS_MAP = {"aas": "http://www.admin-shell.io/aas/3/0",
          "abac": "http://www.admin-shell.io/aas/abac/3/0",
          "aas_common": "http://www.admin-shell.io/aas_common/3/0",
          "xsi": "http://www.w3.org/2001/XMLSchema-instance",
          "IEC": "http://www.admin-shell.io/IEC61360/3/0",
          "xs": "http://www.w3.org/2001/XMLSchema"}


def _generate_element(name: str,
                      text: Optional[str] = None,
                      attributes: Optional[Dict] = None) -> etree.Element:
    """
    generate an ElementTree.Element object

    :param name: namespace+tag_name of the element
    :param text: Text of the element. Default is None
    :param attributes: Attributes of the elements in form of a dict {"attribute_name": "attribute_content"}
    :return: ElementTree.Element object
    """
    et_element = etree.Element(name)
    if text:
        et_element.text = text
    if attributes:
        for key, value in attributes.items():
            et_element.set(key, value)
    return et_element


def boolean_to_xml(obj: bool) -> str:
    """
    Serialize a boolean to XML

    :param obj: Boolean (`True`, `False`)
    :return: String in the XML accepted form (`'true'`, `'false'`)
    """
    if obj:
        return "true"
    else:
        return "false"


# ##############################################################
# transformation functions to serialize abstract classes from model.base
# ##############################################################


def abstract_classes_to_xml(tag: str, obj: object) -> etree.Element:
    """
    Generates an XML element and adds attributes of abstract base classes of `obj`.

    If the object obj is inheriting from any abstract AAS class, this function adds all the serialized information of
    those abstract classes to the generated element.

    :param tag: Tag of the element
    :param obj: An object of the AAS
    :return: Parent element with the serialized information from the abstract classes
    """
    elm = _generate_element(tag)
    if isinstance(obj, model.HasExtension):
        if obj.extension:
            et_extension = _generate_element(NS_AAS + "extensions")
            for extension in obj.extension:
                if isinstance(extension, model.Extension):
                    et_extension.append(extension_to_xml(extension, tag=NS_AAS + "extension"))
            elm.append(et_extension)
    if isinstance(obj, model.Referable):
        elm.append(_generate_element(name=NS_AAS + "idShort", text=obj.id_short))
        if obj.display_name:
            elm.append(lang_string_set_to_xml(obj.display_name, tag=NS_AAS + "displayName"))
        if obj.category:
            elm.append(_generate_element(name=NS_AAS + "category", text=obj.category))
        if obj.description:
            elm.append(lang_string_set_to_xml(obj.description, tag=NS_AAS + "description"))
    if isinstance(obj, model.Identifiable):
        if obj.administration:
            elm.append(administrative_information_to_xml(obj.administration))
        elm.append(_generate_element(name=NS_AAS + "id", text=obj.id))
    if isinstance(obj, model.HasKind):
        if obj.kind is model.ModelingKind.TEMPLATE:
            elm.append(_generate_element(name=NS_AAS + "kind", text="Template"))
        else:
            # then modeling-kind is Instance
            elm.append(_generate_element(name=NS_AAS + "kind", text="Instance"))
    if isinstance(obj, model.HasSemantics):
        if obj.semantic_id:
            elm.append(reference_to_xml(obj.semantic_id, tag=NS_AAS+"semanticId"))
    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            et_qualifier = _generate_element(NS_AAS + "qualifiers")
            for qualifier in obj.qualifier:

                if isinstance(qualifier, model.Qualifier):
                    et_qualifier.append(qualifier_to_xml(qualifier, tag=NS_AAS+"qualifier"))
            elm.append(et_qualifier)
    return elm


# ##############################################################
# transformation functions to serialize classes from model.base
# ##############################################################


def _value_to_xml(value: model.ValueDataType,
                  value_type: model.DataTypeDef,
                  tag: str = NS_AAS+"value") -> etree.Element:
    """
    Serialization of objects of class ValueDataType to XML

    :param value: model.ValueDataType object
    :param value_type: Corresponding model.DataTypeDef
    :param tag: tag of the serialized ValueDataType object
    :return: Serialized ElementTree.Element object
    """
    # todo: add "{NS_XSI+"type": "xs:"+model.datatypes.XSD_TYPE_NAMES[value_type]}" as attribute, if the schema allows
    #  it
    return _generate_element(tag,
                             text=model.datatypes.xsd_repr(value))


def lang_string_set_to_xml(obj: model.LangStringSet, tag: str) -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.LangStringSet` to XML

    :param obj: Object of class :class:`~aas.model.base.LangStringSet`
    :param tag: Namespace+Tag name of the returned XML element.
    :return: Serialized ElementTree object
    """
    et_lss = _generate_element(name=tag)
    for language in obj:
        et_lss.append(_generate_element(name=NS_AAS + "langString",
                                        text=obj[language],
                                        attributes={"lang": language}))
    return et_lss


def administrative_information_to_xml(obj: model.AdministrativeInformation,
                                      tag: str = NS_AAS+"administration") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.AdministrativeInformation` to XML

    :param obj: Object of class :class:`~aas.model.base.AdministrativeInformation`
    :param tag: Namespace+Tag of the serialized element. Default is "aas:administration"
    :return: Serialized ElementTree object
    """
    et_administration = _generate_element(tag)
    if obj.revision:
        et_administration.append(_generate_element(name=NS_AAS + "revision", text=obj.revision))
    if obj.version:
        et_administration.append(_generate_element(name=NS_AAS + "version", text=obj.version))
    return et_administration


def data_element_to_xml(obj: model.DataElement) -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.DataElement` to XML

    :param obj: Object of class :class:`~aas.model.submodel.DataElement`
    :return: Serialized ElementTree element
    """
    if isinstance(obj, model.MultiLanguageProperty):
        return multi_language_property_to_xml(obj)
    if isinstance(obj, model.Property):
        return property_to_xml(obj)
    if isinstance(obj, model.Range):
        return range_to_xml(obj)
    if isinstance(obj, model.Blob):
        return blob_to_xml(obj)
    if isinstance(obj, model.File):
        return file_to_xml(obj)
    if isinstance(obj, model.ReferenceElement):
        return reference_element_to_xml(obj)


def reference_to_xml(obj: model.Reference, tag: str = NS_AAS+"reference") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.Reference` to XML

    :param obj: Object of class :class:`~aas.model.base.Reference`
    :param tag: Namespace+Tag of the returned element. Default is "aas:reference"
    :return: Serialized ElementTree
    """
    et_reference = _generate_element(tag, attributes={"type": _generic.REFERENCE_TYPES[obj.__class__]})
    et_keys = _generate_element(name=NS_AAS + "keys")
    for aas_key in obj.key:
        et_keys.append(_generate_element(name=NS_AAS + "key",
                                         text=aas_key.value,
                                         attributes={"type": _generic.KEY_TYPES[aas_key.type]}))
    et_reference.append(et_keys)
    if obj.referred_semantic_id is not None:
        et_reference.append(reference_to_xml(obj.referred_semantic_id, NS_AAS + "referredSemanticId"))
    return et_reference


def qualifier_to_xml(obj: model.Qualifier, tag: str = NS_AAS+"qualifier") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.Qualifier` to XML

    :param obj: Object of class :class:`~aas.model.base.Qualifier`
    :param tag: Namespace+Tag of the serialized ElementTree object. Default is "aas:qualifier"
    :return: Serialized ElementTreeObject
    """
    et_qualifier = abstract_classes_to_xml(tag, obj)
    if obj.value_id:
        et_qualifier.append(reference_to_xml(obj.value_id, NS_AAS+"valueId"))
    if obj.value:
        et_qualifier.append(_value_to_xml(obj.value, obj.value_type))
    et_qualifier.append(_generate_element(NS_AAS + "type", text=obj.type))
    et_qualifier.append(_generate_element(NS_AAS + "valueType", text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    return et_qualifier


def extension_to_xml(obj: model.Extension, tag: str = NS_AAS+"extension") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.Extension` to XML

    :param obj: Object of class :class:`~aas.model.base.Extension`
    :param tag: Namespace+Tag of the serialized ElementTree object. Default is "aas:extension"
    :return: Serialized ElementTreeObject
    """
    et_extension = abstract_classes_to_xml(tag, obj)
    et_extension.append(_generate_element(NS_AAS + "name", text=obj.name))
    if obj.value_type:
        et_extension.append(_generate_element(NS_AAS + "valueType",
                                              text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    if obj.value:
        et_extension.append(_value_to_xml(obj.value, obj.value_type))  # type: ignore # (value_type could be None)
    for refers_to in obj.refers_to:
        et_extension.append(reference_to_xml(refers_to, NS_AAS+"refersTo"))

    return et_extension


def value_reference_pair_to_xml(obj: model.ValueReferencePair,
                                tag: str = NS_AAS+"valueReferencePair") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.ValueReferencePair` to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization
          check namespace, tag and correct serialization

    :param obj: Object of class :class:`~aas.model.base.ValueReferencePair`
    :param tag: Namespace+Tag of the serialized element. Default is "aas:valueReferencePair"
    :return: Serialized ElementTree object
    """
    et_vrp = _generate_element(tag)
    et_vrp.append(_value_to_xml(obj.value, obj.value_type))
    et_vrp.append(reference_to_xml(obj.value_id, "valueId"))
    return et_vrp


def value_list_to_xml(obj: model.ValueList,
                      tag: str = NS_AAS+"valueList") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.ValueList` to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: Object of class :class:`~aas.model.base.ValueList`
    :param tag: Namespace+Tag of the serialized element. Default is "aas:valueList"
    :return: Serialized ElementTree object
    """
    et_value_list = _generate_element(tag)
    for aas_reference_pair in obj:
        et_value_list.append(value_reference_pair_to_xml(aas_reference_pair, "valueReferencePair"))
    return et_value_list


# ##############################################################
# transformation functions to serialize classes from model.aas
# ##############################################################


def specific_asset_id_to_xml(obj: model.SpecificAssetId, tag: str = NS_AAS + "specifidAssetId") \
        -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.SpecificAssetId` to XML

    :param obj: Object of class :class:`~aas.model.base.SpecificAssetId`
    :param tag: Namespace+Tag of the ElementTree object. Default is "aas:identifierKeyValuePair"
    :return: Serialized ElementTree object
    """
    et_asset_information = abstract_classes_to_xml(tag, obj)
    et_asset_information.append(reference_to_xml(obj.external_subject_id, NS_AAS + "externalSubjectId"))
    et_asset_information.append(_generate_element(name=NS_AAS + "name", text=obj.name))
    et_asset_information.append(_generate_element(name=NS_AAS + "value", text=obj.value))

    return et_asset_information


def asset_information_to_xml(obj: model.AssetInformation, tag: str = NS_AAS+"assetInformation") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.aas.AssetInformation` to XML

    :param obj: Object of class :class:`~aas.model.aas.AssetInformation`
    :param tag: Namespace+Tag of the ElementTree object. Default is "aas:assetInformation"
    :return: Serialized ElementTree object
    """
    et_asset_information = abstract_classes_to_xml(tag, obj)
    if obj.default_thumbnail:
        et_asset_information.append(resource_to_xml(obj.default_thumbnail, NS_AAS+"defaultThumbNail"))
    if obj.global_asset_id:
        et_asset_information.append(reference_to_xml(obj.global_asset_id, NS_AAS + "globalAssetId"))
    et_asset_information.append(_generate_element(name=NS_AAS + "assetKind", text=_generic.ASSET_KIND[obj.asset_kind]))
    et_specific_asset_id = _generate_element(name=NS_AAS + "specificAssetIds")
    if obj.specific_asset_id:
        for specific_asset_id in obj.specific_asset_id:
            et_specific_asset_id.append(specific_asset_id_to_xml(specific_asset_id, NS_AAS + "specificAssetId"))
    et_asset_information.append(et_specific_asset_id)

    return et_asset_information


def concept_description_to_xml(obj: model.ConceptDescription,
                               tag: str = NS_AAS+"conceptDescription") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.concept.ConceptDescription` to XML

    :param obj: Object of class :class:`~aas.model.concept.ConceptDescription`
    :param tag: Namespace+Tag of the ElementTree object. Default is "aas:conceptDescription"
    :return: Serialized ElementTree object
    """
    et_concept_description = abstract_classes_to_xml(tag, obj)
    if isinstance(obj, model.concept.IEC61360ConceptDescription):
        et_embedded_data_specification = _generate_element(NS_AAS+"embeddedDataSpecification")
        et_data_spec_content = _generate_element(NS_AAS+"dataSpecificationContent")
        et_data_spec_content.append(_iec61360_concept_description_to_xml(obj))
        et_embedded_data_specification.append(et_data_spec_content)
        et_concept_description.append(et_embedded_data_specification)
        et_embedded_data_specification.append(reference_to_xml(model.GlobalReference(
            (model.Key(
                model.KeyTypes.GLOBAL_REFERENCE,
                "http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0"
            ),)), NS_AAS+"dataSpecification"))
    if obj.is_case_of:
        for reference in obj.is_case_of:
            et_concept_description.append(reference_to_xml(reference, NS_AAS+"isCaseOf"))
    return et_concept_description


def _iec61360_concept_description_to_xml(obj: model.concept.IEC61360ConceptDescription,
                                         tag: str = NS_AAS+"dataSpecificationIEC61360") -> etree.Element:
    """
    Add the 'embeddedDataSpecifications' attribute to IEC61360ConceptDescription's JSON representation.

    `IEC61360ConceptDescription` is not a distinct class according DotAAS, but instead is built by referencing
    "DataSpecificationIEC61360" as dataSpecification. However, we implemented it as an explicit class, inheriting from
    ConceptDescription, but we want to generate compliant XML documents. So, we fake the XML structure of an object
    with dataSpecifications.

    :param obj: model.concept.IEC61360ConceptDescription object
    :param tag: name of the serialized lss_tag
    :return: serialized ElementTree object
    """

    def _iec_value_reference_pair_to_xml(vrp: model.ValueReferencePair,
                                         vrp_tag: str = NS_IEC + "valueReferencePair") -> etree.Element:
        """
        serialization of objects of class ValueReferencePair to XML

        :param vrp: object of class ValueReferencePair
        :param vrp_tag: vl_tag of the serialized element, default is "valueReferencePair"
        :return: serialized ElementTree object
        """
        et_vrp = _generate_element(vrp_tag)
        et_vrp.append(reference_to_xml(vrp.value_id, NS_IEC + "valueId"))
        et_vrp.append(_value_to_xml(vrp.value, vrp.value_type, tag=NS_IEC+"value"))
        return et_vrp

    def _iec_value_list_to_xml(vl: model.ValueList,
                               vl_tag: str = NS_IEC + "valueList") -> etree.Element:
        """
        serialization of objects of class ValueList to XML

        :param vl: object of class ValueList
        :param vl_tag: vl_tag of the serialized element, default is "valueList"
        :return: serialized ElementTree object
        """
        et_value_list = _generate_element(vl_tag)
        for aas_reference_pair in vl:
            et_value_list.append(_iec_value_reference_pair_to_xml(aas_reference_pair, NS_IEC+"valueReferencePair"))
        return et_value_list

    et_iec = _generate_element(tag)
    et_iec.append(lang_string_set_to_xml(obj.preferred_name, NS_IEC + "preferredName"))
    if obj.short_name:
        et_iec.append(lang_string_set_to_xml(obj.short_name, NS_IEC + "shortName"))
    if obj.unit:
        et_iec.append(_generate_element(NS_IEC+"unit", text=obj.unit))
    if obj.unit_id:
        et_iec.append(reference_to_xml(obj.unit_id, NS_IEC+"unitId"))
    if obj.source_of_definition:
        et_iec.append(_generate_element(NS_IEC+"sourceOfDefinition", text=obj.source_of_definition))
    if obj.symbol:
        et_iec.append(_generate_element(NS_IEC+"symbol", text=obj.symbol))
    if obj.data_type:
        et_iec.append(_generate_element(NS_IEC+"dataType", text=_generic.IEC61360_DATA_TYPES[obj.data_type]))
    if obj.definition:
        et_iec.append(lang_string_set_to_xml(obj.definition, NS_IEC + "definition"))
    if obj.value_format:
        et_iec.append(_generate_element(NS_IEC+"valueFormat", text=model.datatypes.XSD_TYPE_NAMES[obj.value_format]))
    if obj.value_list:
        et_iec.append(_iec_value_list_to_xml(obj.value_list, NS_IEC+"valueList"))
    if obj.value:
        et_iec.append(_generate_element(NS_IEC+"value", text=model.datatypes.xsd_repr(obj.value)))
    if obj.value_id:
        et_iec.append(reference_to_xml(obj.value_id, NS_IEC+"valueId"))
    if obj.level_types:
        for level_type in obj.level_types:
            et_iec.append(_generate_element(NS_IEC+"levelType", text=_generic.IEC61360_LEVEL_TYPES[level_type]))
    return et_iec


def asset_administration_shell_to_xml(obj: model.AssetAdministrationShell,
                                      tag: str = NS_AAS+"assetAdministrationShell") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.aas.AssetAdministrationShell` to XML

    :param obj: Object of class :class:`~aas.model.aas.AssetAdministrationShell`
    :param tag: Namespace+Tag of the ElementTree object. Default is "aas:assetAdministrationShell"
    :return: Serialized ElementTree object
    """
    et_aas = abstract_classes_to_xml(tag, obj)
    if obj.derived_from:
        et_aas.append(reference_to_xml(obj.derived_from, tag=NS_AAS+"derivedFrom"))
    if obj.submodel:
        et_submodels = _generate_element(NS_AAS + "submodelRefs")
        for reference in obj.submodel:
            et_submodels.append(reference_to_xml(reference, tag=NS_AAS+"submodelRef"))
        et_aas.append(et_submodels)
    et_aas.append(asset_information_to_xml(obj.asset_information, tag=NS_AAS + "assetInformation"))
    return et_aas


# ##############################################################
# transformation functions to serialize classes from model.security
# ##############################################################


def security_to_xml(obj: model.Security,
                    tag: str = NS_ABAC+"security") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.security.Security` to XML

    todo: This is not yet implemented

    :param obj: Object of class :class:`~aas.model.security.Security`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:security"
    :return: Serialized ElementTree object
    """
    return abstract_classes_to_xml(tag, obj)


# ##############################################################
# transformation functions to serialize classes from model.submodel
# ##############################################################


def submodel_element_to_xml(obj: model.SubmodelElement) -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.SubmodelElement` to XML

    :param obj: Object of class :class:`~aas.model.submodel.SubmodelElement`
    :return: Serialized ElementTree object
    """
    if isinstance(obj, model.DataElement):
        return data_element_to_xml(obj)
    if isinstance(obj, model.BasicEventElement):
        return basic_event_element_to_xml(obj)
    if isinstance(obj, model.Capability):
        return capability_to_xml(obj)
    if isinstance(obj, model.Entity):
        return entity_to_xml(obj)
    if isinstance(obj, model.Operation):
        return operation_to_xml(obj)
    if isinstance(obj, model.AnnotatedRelationshipElement):
        return annotated_relationship_element_to_xml(obj)
    if isinstance(obj, model.RelationshipElement):
        return relationship_element_to_xml(obj)
    if isinstance(obj, model.SubmodelElementCollection):
        return submodel_element_collection_to_xml(obj)


def submodel_to_xml(obj: model.Submodel,
                    tag: str = NS_AAS+"submodel") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Submodel` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Submodel`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:submodel"
    :return: Serialized ElementTree object
    """
    et_submodel = abstract_classes_to_xml(tag, obj)
    et_submodel_elements = _generate_element(NS_AAS + "submodelElements")
    if obj.submodel_element:
        for submodel_element in obj.submodel_element:
            # TODO: simplify this should our suggestion regarding the XML schema get accepted
            # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
            et_submodel_element = _generate_element(NS_AAS+"submodelElement")
            et_submodel_element.append(submodel_element_to_xml(submodel_element))
            et_submodel_elements.append(et_submodel_element)
    et_submodel.append(et_submodel_elements)
    return et_submodel


def property_to_xml(obj: model.Property,
                    tag: str = NS_AAS+"property") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Property` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Property`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:property"
    :return: Serialized ElementTree object
    """
    et_property = abstract_classes_to_xml(tag, obj)
    if obj.value_id:
        et_property.append(reference_to_xml(obj.value_id, NS_AAS + "valueId"))
    if obj.value:
        et_property.append(_value_to_xml(obj.value, obj.value_type))
    et_property.append(_generate_element(NS_AAS + "valueType", text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    return et_property


def multi_language_property_to_xml(obj: model.MultiLanguageProperty,
                                   tag: str = NS_AAS+"multiLanguageProperty") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.MultiLanguageProperty` to XML

    :param obj: Object of class :class:`~aas.model.submodel.MultiLanguageProperty`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:multiLanguageProperty"
    :return: Serialized ElementTree object
    """
    et_multi_language_property = abstract_classes_to_xml(tag, obj)
    if obj.value_id:
        et_multi_language_property.append(reference_to_xml(obj.value_id, NS_AAS+"valueId"))
    if obj.value:
        et_multi_language_property.append(lang_string_set_to_xml(obj.value, tag=NS_AAS + "value"))
    return et_multi_language_property


def range_to_xml(obj: model.Range,
                 tag: str = NS_AAS+"range") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Range` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Range`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:range"
    :return: Serialized ElementTree object
    """
    et_range = abstract_classes_to_xml(tag, obj)
    if obj.max is not None:
        et_range.append(_value_to_xml(obj.max, obj.value_type, tag=NS_AAS + "max"))
    if obj.min is not None:
        et_range.append(_value_to_xml(obj.min, obj.value_type, tag=NS_AAS + "min"))
    et_range.append(_generate_element(name=NS_AAS + "valueType",
                                      text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    return et_range


def blob_to_xml(obj: model.Blob,
                tag: str = NS_AAS+"blob") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Blob` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Blob`
    :param tag: Namespace+Tag of the serialized element. Default is "blob"
    :return: Serialized ElementTree object
    """
    et_blob = abstract_classes_to_xml(tag, obj)
    et_value = etree.Element(NS_AAS + "value")
    if obj.value is not None:
        et_value.text = base64.b64encode(obj.value).decode()
    et_blob.append(et_value)
    et_blob.append(_generate_element(NS_AAS + "contentType", text=obj.content_type))
    return et_blob


def file_to_xml(obj: model.File,
                tag: str = NS_AAS+"file") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.File` to XML

    :param obj: Object of class :class:`~aas.model.submodel.File`
    :param tag: Namespace+Tag of the serialized element. Default is "aas:file"
    :return: Serialized ElementTree object
    """
    et_file = abstract_classes_to_xml(tag, obj)
    if obj.value:
        et_file.append(_generate_element(NS_AAS + "value", text=obj.value))
    et_file.append(_generate_element(NS_AAS + "contentType", text=obj.content_type))
    return et_file


def resource_to_xml(obj: model.Resource,
                    tag: str = NS_AAS+"resource") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.base.Resource` to XML

    :param obj: Object of class :class:`~aas.model.base.Resource`
    :param tag: Namespace+Tag of the serialized element. Default is "aas:resource"
    :return: Serialized ElementTree object
    """
    et_resource = abstract_classes_to_xml(tag, obj)
    et_resource.append(_generate_element(NS_AAS + "path", text=obj.path))
    if obj.content_type:
        et_resource.append(_generate_element(NS_AAS + "contentType", text=obj.content_type))
    return et_resource


def reference_element_to_xml(obj: model.ReferenceElement,
                             tag: str = NS_AAS+"referenceElement") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.ReferenceElement` to XMl

    :param obj: Object of class :class:`~aas.model.submodel.ReferenceElement`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:referenceElement"
    :return: Serialized ElementTree object
    """
    et_reference_element = abstract_classes_to_xml(tag, obj)
    if obj.value:
        et_reference_element.append(reference_to_xml(obj.value, NS_AAS+"value"))
    return et_reference_element


def submodel_element_collection_to_xml(obj: model.SubmodelElementCollection,
                                       tag: str = NS_AAS+"submodelElementCollection") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.SubmodelElementCollection` to XML

    Note that we do not have parameter "allowDuplicates" in out implementation

    :param obj: Object of class :class:`~aas.model.submodel.SubmodelElementCollection`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:submodelElementCollection"
    :return: Serialized ElementTree object
    """
    et_submodel_element_collection = abstract_classes_to_xml(tag, obj)
    # todo: remove wrapping submodelElement-tag, in accordance to future schema
    et_submodel_element_collection.append(_generate_element(NS_AAS + "allowDuplicates",
                                                            text=boolean_to_xml(obj.allow_duplicates)))
    et_submodel_element_collection.append(_generate_element(NS_AAS + "ordered", text=boolean_to_xml(obj.ordered)))
    et_value = _generate_element(NS_AAS + "value")
    if obj.value:
        for submodel_element in obj.value:
            et_submodel_element = _generate_element(NS_AAS+"submodelElement")
            et_submodel_element.append(submodel_element_to_xml(submodel_element))
            et_value.append(et_submodel_element)
    et_submodel_element_collection.append(et_value)
    return et_submodel_element_collection


def relationship_element_to_xml(obj: model.RelationshipElement,
                                tag: str = NS_AAS+"relationshipElement") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.RelationshipElement` to XML

    :param obj: Object of class :class:`~aas.model.submodel.RelationshipElement`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:relationshipElement"
    :return: Serialized ELementTree object
    """
    et_relationship_element = abstract_classes_to_xml(tag, obj)
    et_relationship_element.append(reference_to_xml(obj.first, NS_AAS+"first"))
    et_relationship_element.append(reference_to_xml(obj.second, NS_AAS+"second"))
    return et_relationship_element


def annotated_relationship_element_to_xml(obj: model.AnnotatedRelationshipElement,
                                          tag: str = NS_AAS+"annotatedRelationshipElement") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.AnnotatedRelationshipElement` to XML

    :param obj: Object of class :class:`~aas.model.submodel.AnnotatedRelationshipElement`
    :param tag: Namespace+Tag of the serialized element (optional): Default is "aas:annotatedRelationshipElement"
    :return: Serialized ElementTree object
    """
    et_annotated_relationship_element = relationship_element_to_xml(obj, tag)
    et_annotations = _generate_element(name=NS_AAS+"annotations")
    if obj.annotation:
        for data_element in obj.annotation:
            et_data_element = _generate_element(name=NS_AAS+"dataElement")
            et_data_element.append(data_element_to_xml(data_element))
            et_annotations.append(et_data_element)
    et_annotated_relationship_element.append(et_annotations)
    return et_annotated_relationship_element


def operation_variable_to_xml(obj: model.OperationVariable,
                              tag: str = NS_AAS+"operationVariable") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.OperationVariable` to XML

    :param obj: Object of class :class:`~aas.model.submodel.OperationVariable`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:operationVariable"
    :return: Serialized ElementTree object
    """
    et_operation_variable = _generate_element(tag)
    et_value = _generate_element(NS_AAS+"value")
    et_value.append(submodel_element_to_xml(obj.value))
    et_operation_variable.append(et_value)
    return et_operation_variable


def operation_to_xml(obj: model.Operation,
                     tag: str = NS_AAS+"operation") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Operation` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Operation`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:operation"
    :return: Serialized ElementTree object
    """
    et_operation = abstract_classes_to_xml(tag, obj)
    if obj.in_output_variable:
        for in_out_ov in obj.in_output_variable:
            et_operation.append(operation_variable_to_xml(in_out_ov, NS_AAS+"inoutputVariable"))
    if obj.input_variable:
        for input_ov in obj.input_variable:
            et_operation.append(operation_variable_to_xml(input_ov, NS_AAS+"inputVariable"))
    if obj.output_variable:
        for output_ov in obj.output_variable:
            et_operation.append(operation_variable_to_xml(output_ov, NS_AAS+"outputVariable"))
    return et_operation


def capability_to_xml(obj: model.Capability,
                      tag: str = NS_AAS+"capability") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Capability` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Capability`
    :param tag: Namespace+Tag of the serialized element, default is "aas:capability"
    :return: Serialized ElementTree object
    """
    return abstract_classes_to_xml(tag, obj)


def entity_to_xml(obj: model.Entity,
                  tag: str = NS_AAS+"entity") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.Entity` to XML

    :param obj: Object of class :class:`~aas.model.submodel.Entity`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:entity"
    :return: Serialized ElementTree object
    """
    # todo: remove wrapping submodelElement, in accordance to future schemas
    et_entity = abstract_classes_to_xml(tag, obj)
    if obj.global_asset_id:
        et_entity.append(reference_to_xml(obj.global_asset_id, NS_AAS + "globalAssetId"))
    if obj.specific_asset_id:
        et_entity.append(specific_asset_id_to_xml(obj.specific_asset_id, NS_AAS + "specificAssetId"))
    et_entity.append(_generate_element(NS_AAS + "entityType", text=_generic.ENTITY_TYPES[obj.entity_type]))
    et_statements = _generate_element(NS_AAS + "statements")
    for statement in obj.statement:
        # todo: remove the <submodelElement> once the proposed changes get accepted
        et_submodel_element = _generate_element(NS_AAS + "submodelElement")
        et_submodel_element.append(submodel_element_to_xml(statement))
        et_statements.append(et_submodel_element)
    et_entity.append(et_statements)
    return et_entity


def basic_event_element_to_xml(obj: model.BasicEventElement, tag: str = NS_AAS+"basicEventElement") -> etree.Element:
    """
    Serialization of objects of class :class:`~aas.model.submodel.BasicEventElement` to XML

    :param obj: Object of class :class:`~aas.model.submodel.BasicEventElement`
    :param tag: Namespace+Tag of the serialized element (optional). Default is "aas:basicEventElement"
    :return: Serialized ElementTree object
    """
    et_basic_event_element = abstract_classes_to_xml(tag, obj)
    et_basic_event_element.append(reference_to_xml(obj.observed, NS_AAS+"observed"))
    return et_basic_event_element


# ##############################################################
# general functions
# ##############################################################


def write_aas_xml_file(file: IO,
                       data: model.AbstractObjectStore,
                       **kwargs) -> None:
    """
    Write a set of AAS objects to an Asset Administration Shell XML file according to 'Details of the Asset
    Administration Shell', chapter 5.4

    :param file: A file-like object to write the XML-serialized data to
    :param data: :class:`ObjectStore <aas.model.provider.AbstractObjectStore>` which contains different objects of the
                 AAS meta model which should be serialized to an XML file
    :param kwargs: Additional keyword arguments to be passed to `tree.write()`
    """
    # separate different kind of objects
    asset_administration_shells = []
    submodels = []
    concept_descriptions = []
    for obj in data:
        if isinstance(obj, model.AssetAdministrationShell):
            asset_administration_shells.append(obj)
        elif isinstance(obj, model.Submodel):
            submodels.append(obj)
        elif isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)

    # serialize objects to XML
    root = etree.Element(NS_AAS + "aasenv", nsmap=NS_MAP)
    et_asset_administration_shells = etree.Element(NS_AAS + "assetAdministrationShells")
    for aas_obj in asset_administration_shells:
        et_asset_administration_shells.append(asset_administration_shell_to_xml(aas_obj))
    et_concept_descriptions = etree.Element(NS_AAS + "conceptDescriptions")
    for con_obj in concept_descriptions:
        et_concept_descriptions.append(concept_description_to_xml(con_obj))
    et_submodels = etree.Element(NS_AAS + "submodels")
    for sub_obj in submodels:
        et_submodels.append(submodel_to_xml(sub_obj))
    root.insert(0, et_submodels)
    root.insert(0, et_concept_descriptions)
    root.insert(0, et_asset_administration_shells)

    tree = etree.ElementTree(root)
    tree.write(file, encoding="UTF-8", xml_declaration=True, method="xml", **kwargs)
