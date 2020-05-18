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
Module for serializing Asset Administration Shell data to the official XML format

How to use:
- For generating an XML-File from a model.registry.AbstractObjectStore, check out the function "write_aas_xml_file".
- For serializing any object to an XML fragment, that fits the XML specification from 'Details of the
  Asset Administration Shell', chapter 5.4, check out `<your_object_class_name_here>_to_xml()`. These functions return
  an xml.etree.ElementTree.Element object to be serialized into XML.
"""

from lxml import etree  # type: ignore
from typing import Dict, IO, Optional
import base64

from aas import model
from .. import _generic


# ##############################################################
# functions to manipulate etree.Elements more effectively
# ##############################################################

# Namespace definition
NS_AAS = "{http://www.admin-shell.io/aas/2/0}"
NS_ABAC = "{http://www.admin-shell.io/aas/abac/2/0}"
NS_AAS_COMMON = "{http://www.admin-shell.io/aas_common/2/0}"
NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
NS_XS = "{http://www.w3.org/2001/XMLSchema}"
NS_IEC = "{http://www.admin-shell.io/IEC61360/2/0}"
NS_MAP = {"aas": "http://www.admin-shell.io/aas/2/0",
          "abac": "http://www.admin-shell.io/aas/abac/2/0",
          "aas_common": "http://www.admin-shell.io/aas_common/2/0",
          "xsi": "http://www.w3.org/2001/XMLSchema-instance",
          "IEC": "http://www.admin-shell.io/IEC61360/2/0",
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
    serialize a boolean to XML

    :param obj: boolean
    :return: string in the XML accepted form
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

    :param tag: tag of the element
    :param obj: an object of the AAS
    :return: parent element with the serialized information from the abstract classes
    """
    elm = _generate_element(tag)
    if isinstance(obj, model.Referable):
        elm.append(_generate_element(name=NS_AAS + "idShort", text=obj.id_short))
        if obj.category:
            elm.append(_generate_element(name=NS_AAS + "category", text=obj.category))
        if obj.description:
            elm.append(lang_string_set_to_xml(obj.description, tag=NS_AAS + "description"))
    if isinstance(obj, model.Identifiable):
        elm.append(_generate_element(name=NS_AAS + "identification",
                                     text=obj.identification.id,
                                     attributes={"idType": _generic.IDENTIFIER_TYPES[obj.identification.id_type]}))
        if obj.administration:
            elm.append(administrative_information_to_xml(obj.administration))
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
            for qualifier in obj.qualifier:
                et_qualifier = _generate_element(NS_AAS+"qualifier")
                if isinstance(qualifier, model.Qualifier):
                    et_qualifier.append(qualifier_to_xml(qualifier, tag=NS_AAS+"qualifier"))
                if isinstance(qualifier, model.Formula):
                    et_qualifier.append(formula_to_xml(qualifier, tag=NS_AAS+"formula"))
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
    serialization of objects of class LangStringSet to XML

    :param obj: object of class LangStringSet
    :param tag: tag name of the returned XML element (incl. namespace)
    :return: serialized ElementTree object
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
    serialization of objects of class AdministrativeInformation to XML

    :param obj: object of class AdministrativeInformation
    :param tag: tag of the serialized element. default is "administration"
    :return: serialized ElementTree object
    """
    et_administration = _generate_element(tag)
    if obj.version:
        et_administration.append(_generate_element(name=NS_AAS + "version", text=obj.version))
        if obj.revision:
            et_administration.append(_generate_element(name=NS_AAS + "revision", text=obj.revision))
    return et_administration


def data_element_to_xml(obj: model.DataElement) -> etree.Element:
    """
    serialization of objects of class DataElement to XML

    :param obj: Object of class DataElement
    :return: serialized ElementTree element
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
    serialization of objects of class Reference to XML

    :param obj: object of class Reference
    :param tag: tag of the returned element
    :return: serialized ElementTree
    """
    et_reference = _generate_element(tag)
    et_keys = _generate_element(name=NS_AAS + "keys")
    for aas_key in obj.key:
        et_keys.append(_generate_element(name=NS_AAS + "key",
                                         text=aas_key.value,
                                         attributes={"idType": _generic.KEY_TYPES[aas_key.id_type],
                                                     "local": boolean_to_xml(aas_key.local),
                                                     "type": _generic.KEY_ELEMENTS[aas_key.type]}))
    et_reference.append(et_keys)
    return et_reference


def formula_to_xml(obj: model.Formula, tag: str = NS_AAS+"formula") -> etree.Element:
    """
    serialization of objects of class Formula to XML

    :param obj: object of class Formula
    :param tag: tag of the ElementTree object, default is "formula"
    :return: serialized ElementTree object
    """
    et_formula = abstract_classes_to_xml(tag, obj)
    if obj.depends_on:
        et_depends_on = _generate_element(name=NS_AAS + "dependsOnRefs", text=None)
        for aas_reference in obj.depends_on:
            et_depends_on.append(reference_to_xml(aas_reference, NS_AAS+"reference"))
        et_formula.append(et_depends_on)
    return et_formula


def qualifier_to_xml(obj: model.Qualifier, tag: str = NS_AAS+"qualifier") -> etree.Element:
    """
    serialization of objects of class Qualifier to XML

    :param obj: object of class Qualifier
    :param tag: tag of the serialized ElementTree object, default is "qualifier"
    :return: serialized ElementTreeObject
    """
    et_qualifier = abstract_classes_to_xml(tag, obj)
    et_qualifier.append(_generate_element(NS_AAS + "type", text=obj.type))
    et_qualifier.append(_generate_element(NS_AAS + "valueType", text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    if obj.value_id:
        et_qualifier.append(reference_to_xml(obj.value_id, NS_AAS+"valueId"))
    if obj.value:
        et_qualifier.append(_value_to_xml(obj.value, obj.value_type))
    return et_qualifier


def value_reference_pair_to_xml(obj: model.ValueReferencePair,
                                tag: str = NS_AAS+"valueReferencePair") -> etree.Element:
    """
    serialization of objects of class ValueReferencePair to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization
          check namespace, tag and correct serialization

    :param obj: object of class ValueReferencePair
    :param tag: tag of the serialized element, default is "valueReferencePair"
    :return: serialized ElementTree object
    """
    et_vrp = _generate_element(tag)
    et_vrp.append(_value_to_xml(obj.value, obj.value_type))
    et_vrp.append(reference_to_xml(obj.value_id, "valueId"))
    return et_vrp


def value_list_to_xml(obj: model.ValueList,
                      tag: str = NS_AAS+"valueList") -> etree.Element:
    """
    serialization of objects of class ValueList to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueList
    :param tag: tag of the serialized element, default is "valueList"
    :return: serialized ElementTree object
    """
    et_value_list = _generate_element(tag)
    for aas_reference_pair in obj:
        et_value_list.append(value_reference_pair_to_xml(aas_reference_pair, "valueReferencePair"))
    return et_value_list


# ##############################################################
# transformation functions to serialize classes from model.aas
# ##############################################################


def view_to_xml(obj: model.View, tag: str = NS_AAS+"view") -> etree.Element:
    """
    serialization of objects of class View to XML

    :param obj: object of class View
    :param tag: namespace+tag of the ElementTree object. default is "view"
    :return: serialized ElementTree object
    """
    et_view = abstract_classes_to_xml(tag, obj)
    et_contained_elements = _generate_element(name=NS_AAS + "containedElements")
    if obj.contained_element:
        for contained_element in obj.contained_element:
            et_contained_elements.append(reference_to_xml(contained_element, NS_AAS+"containedElementRef"))
    et_view.append(et_contained_elements)
    return et_view


def asset_to_xml(obj: model.Asset, tag: str = NS_AAS+"asset") -> etree.Element:
    """
    serialization of objects of class Asset to XML

    :param obj: object of class Asset
    :param tag: namespace+tag of the ElementTree object. default is "asset"
    :return: serialized ElementTree object
    """
    et_asset = abstract_classes_to_xml(tag, obj)
    if obj.asset_identification_model:
        et_asset.append(reference_to_xml(obj.asset_identification_model, NS_AAS+"assetIdentificationModelRef"))
    if obj.bill_of_material:
        et_asset.append(reference_to_xml(obj.bill_of_material, NS_AAS+"billOfMaterialRef"))
    et_asset.append(_generate_element(name=NS_AAS + "kind", text=_generic.ASSET_KIND[obj.kind]))
    return et_asset


def concept_description_to_xml(obj: model.ConceptDescription,
                               tag: str = NS_AAS+"conceptDescription") -> etree.Element:
    """
    serialization of objects of class ConceptDescription to XML

    :param obj: object of class ConceptDescription
    :param tag: tag of the ElementTree object. default is "conceptDescription"
    :return: serialized ElementTree object
    """
    et_concept_description = abstract_classes_to_xml(tag, obj)
    if isinstance(obj, model.concept.IEC61360ConceptDescription):
        et_embedded_data_specification = _generate_element(NS_AAS+"embeddedDataSpecification")
        et_data_spec_content = _generate_element(NS_AAS+"dataSpecificationContent")
        et_data_spec_content.append(_iec61360_concept_description_to_xml(obj))
        et_embedded_data_specification.append(et_data_spec_content)
        et_concept_description.append(et_embedded_data_specification)
        et_embedded_data_specification.append(reference_to_xml(model.Reference(tuple([model.Key(
            model.KeyElements.GLOBAL_REFERENCE,
            False,
            "http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0",
            model.KeyType.IRI
        )])), NS_AAS+"dataSpecification"))
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

    def _iec_lang_string_set_to_xml(lss: model.LangStringSet, lss_tag: str) -> etree.Element:
        """
        serialization of objects of class LangStringSet to XML

        :param lss: object of class LangStringSet
        :param lss_tag: lss_tag name of the returned XML element (incl. namespace)
        :return: serialized ElementTree object
        """
        et_lss = _generate_element(name=lss_tag)
        for language in lss:
            et_lss.append(_generate_element(name=NS_IEC + "langString",
                                            text=lss[language],
                                            attributes={"lang": language}))
        return et_lss

    def _iec_reference_to_xml(ref: model.Reference, ref_tag: str = NS_AAS + "reference") -> etree.Element:
        """
        serialization of objects of class Reference to XML

        :param ref: object of class Reference
        :param ref_tag: ref_tag of the returned element
        :return: serialized ElementTree
        """
        et_reference = _generate_element(ref_tag)
        et_keys = _generate_element(name=NS_IEC + "keys")
        for aas_key in ref.key:
            et_keys.append(_generate_element(name=NS_IEC + "key",
                                             text=aas_key.value,
                                             attributes={"idType": _generic.KEY_TYPES[aas_key.id_type],
                                                         "local": boolean_to_xml(aas_key.local),
                                                         "type": _generic.KEY_ELEMENTS[aas_key.type]}))
        et_reference.append(et_keys)
        return et_reference

    def _iec_value_reference_pair_to_xml(vrp: model.ValueReferencePair,
                                         vrp_tag: str = NS_IEC + "valueReferencePair") -> etree.Element:
        """
        serialization of objects of class ValueReferencePair to XML

        :param vrp: object of class ValueReferencePair
        :param vrp_tag: vl_tag of the serialized element, default is "valueReferencePair"
        :return: serialized ElementTree object
        """
        et_vrp = _generate_element(vrp_tag)
        et_vrp.append(_iec_reference_to_xml(vrp.value_id, NS_IEC + "valueId"))
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
    et_iec.append(_iec_lang_string_set_to_xml(obj.preferred_name, NS_IEC + "preferredName"))
    if obj.short_name:
        et_iec.append(_iec_lang_string_set_to_xml(obj.short_name, NS_IEC + "shortName"))
    if obj.unit:
        et_iec.append(_generate_element(NS_IEC+"unit", text=obj.unit))
    if obj.unit_id:
        et_iec.append(_iec_reference_to_xml(obj.unit_id, NS_IEC+"unitId"))
    if obj.source_of_definition:
        et_iec.append(_generate_element(NS_IEC+"sourceOfDefinition", text=obj.source_of_definition))
    if obj.symbol:
        et_iec.append(_generate_element(NS_IEC+"symbol", text=obj.symbol))
    if obj.data_type:
        et_iec.append(_generate_element(NS_IEC+"dataType", text=_generic.IEC61360_DATA_TYPES[obj.data_type]))
    if obj.definition:
        et_iec.append(_iec_lang_string_set_to_xml(obj.definition, NS_IEC + "definition"))
    if obj.value_format:
        et_iec.append(_generate_element(NS_IEC+"valueFormat", text=model.datatypes.XSD_TYPE_NAMES[obj.value_format]))
    if obj.value_list:
        et_iec.append(_iec_value_list_to_xml(obj.value_list, NS_IEC+"valueList"))
    if obj.value:
        et_iec.append(_generate_element(NS_IEC+"value", text=model.datatypes.xsd_repr(obj.value)))
    if obj.value_id:
        et_iec.append(_iec_reference_to_xml(obj.value_id, NS_IEC+"valueId"))
    if obj.level_types:
        for level_type in obj.level_types:
            et_iec.append(_generate_element(NS_IEC+"levelType", text=_generic.IEC61360_LEVEL_TYPES[level_type]))
    return et_iec


def concept_dictionary_to_xml(obj: model.ConceptDictionary,
                              tag: str = NS_AAS+"conceptDictionary") -> etree.Element:
    """
    serialization of objects of class ConceptDictionary to XML

    :param obj: object of class ConceptDictionary
    :param tag: tag of the ElementTree object. default is "conceptDictionary"
    :return: serialized ElementTree object
    """
    et_concept_dictionary = abstract_classes_to_xml(tag, obj)
    et_concept_descriptions_refs = _generate_element(NS_AAS + "conceptDescriptionRefs")
    if obj.concept_description:
        for reference in obj.concept_description:
            et_concept_descriptions_refs.append(reference_to_xml(reference, NS_AAS+"conceptDescriptionRef"))
    et_concept_dictionary.append(et_concept_descriptions_refs)
    return et_concept_dictionary


def asset_administration_shell_to_xml(obj: model.AssetAdministrationShell,
                                      tag: str = NS_AAS+"assetAdministrationShell") -> etree.Element:
    """
    serialization of objects of class AssetAdministrationShell to XML

    :param obj: object of class AssetAdministrationShell
    :param tag: tag of the ElementTree object. default is "assetAdministrationShell"
    :return: serialized ElementTree object
    """
    et_aas = abstract_classes_to_xml(tag, obj)
    if obj.derived_from:
        et_aas.append(reference_to_xml(obj.derived_from, tag=NS_AAS+"derivedFrom"))
    et_aas.append(reference_to_xml(obj.asset, tag=NS_AAS+"assetRef"))
    if obj.submodel:
        et_submodels = _generate_element(NS_AAS + "submodelRefs")
        for reference in obj.submodel:
            et_submodels.append(reference_to_xml(reference, tag=NS_AAS+"submodelRef"))
        et_aas.append(et_submodels)
    if obj.view:
        et_views = _generate_element(NS_AAS + "views")
        for view in obj.view:
            et_views.append(view_to_xml(view, NS_AAS+"view"))
        et_aas.append(et_views)
    if obj.concept_dictionary:
        et_concept_dictionaries = _generate_element(NS_AAS + "conceptDictionaries")
        for concept_dictionary in obj.concept_dictionary:
            et_concept_dictionaries.append(concept_dictionary_to_xml(concept_dictionary,
                                                                     NS_AAS+"conceptDictionary"))
        et_aas.append(et_concept_dictionaries)
    if obj.security:
        et_aas.append(security_to_xml(obj.security, tag=NS_ABAC+"security"))
    return et_aas


# ##############################################################
# transformation functions to serialize classes from model.security
# ##############################################################


def security_to_xml(obj: model.Security,
                    tag: str = NS_ABAC+"security") -> etree.Element:
    """
    serialization of objects of class Security to XML

    todo: This is not yet implemented

    :param obj: object of class Security
    :param tag: tag of the serialized element (optional). Default is "security"
    :return: serialized ElementTree object
    """
    return abstract_classes_to_xml(tag, obj)


# ##############################################################
# transformation functions to serialize classes from model.submodel
# ##############################################################


def submodel_element_to_xml(obj: model.SubmodelElement) -> etree.Element:
    """
    serialization of objects of class SubmodelElement to XML

    :param obj: object of class SubmodelElement
    :return: serialized ElementTree object
    """
    if isinstance(obj, model.DataElement):
        return data_element_to_xml(obj)
    if isinstance(obj, model.BasicEvent):
        return basic_event_to_xml(obj)
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
    serialization of objects of class Submodel to XML

    :param obj: object of class Submodel
    :param tag: tag of the serialized element (optional). Default is "submodel"
    :return: serialized ElementTree object
    """
    et_submodel = abstract_classes_to_xml(tag, obj)
    et_submodel_elements = _generate_element(NS_AAS + "submodelElements")
    if obj.submodel_element:
        for submodel_element in obj.submodel_element:
            # TODO: simplify this should our suggestion regarding the XML schema get accepted
            # https://git.rwth-aachen.de/acplt/pyaas/-/issues/57
            et_submodel_element = _generate_element(NS_AAS+"submodelElement")
            et_submodel_element.append(submodel_element_to_xml(submodel_element))
            et_submodel_elements.append(et_submodel_element)
    et_submodel.append(et_submodel_elements)
    return et_submodel


def property_to_xml(obj: model.Property,
                    tag: str = NS_AAS+"property") -> etree.Element:
    """
    serialization of objects of class Property to XML

    :param obj: object of class Property
    :param tag: tag of the serialized element (optional), default is "property"
    :return: serialized ElementTree object
    """
    et_property = abstract_classes_to_xml(tag, obj)
    et_property.append(_generate_element(NS_AAS + "valueType", text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    if obj.value:
        et_property.append(_value_to_xml(obj.value, obj.value_type))
    if obj.value_id:
        et_property.append(reference_to_xml(obj.value_id, NS_AAS + "valueId"))
    return et_property


def multi_language_property_to_xml(obj: model.MultiLanguageProperty,
                                   tag: str = NS_AAS+"multiLanguageProperty") -> etree.Element:
    """
    serialization of objects of class MultiLanguageProperty to XML

    :param obj: object of class MultiLanguageProperty
    :param tag: tag of the serialized element (optional), default is "multiLanguageProperty"
    :return: serialized ElementTree object
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
    serialization of objects of class Range to XML

    :param obj: object of class Range
    :param tag: namespace+tag of the serialized element (optional), default is "range
    :return: serialized ElementTree object
    """
    et_range = abstract_classes_to_xml(tag, obj)
    et_range.append(_generate_element(name=NS_AAS + "valueType",
                                      text=model.datatypes.XSD_TYPE_NAMES[obj.value_type]))
    if obj.min is not None:
        et_range.append(_value_to_xml(obj.min, obj.value_type, tag=NS_AAS+"min"))
    if obj.max is not None:
        et_range.append(_value_to_xml(obj.max, obj.value_type, tag=NS_AAS+"max"))
    return et_range


def blob_to_xml(obj: model.Blob,
                tag: str = NS_AAS+"blob") -> etree.Element:
    """
    serialization of objects of class Blob to XML

    :param obj: object of class Blob
    :param tag: tag of the serialized element, default is "blob"
    :return: serialized ElementTree object
    """
    et_blob = abstract_classes_to_xml(tag, obj)
    et_value = etree.Element(NS_AAS + "value")
    if obj.value is not None:
        et_value.text = base64.b64encode(obj.value).decode()
    et_blob.append(et_value)
    et_blob.append(_generate_element(NS_AAS + "mimeType", text=obj.mime_type))
    return et_blob


def file_to_xml(obj: model.File,
                tag: str = NS_AAS+"file") -> etree.Element:
    """
    serialization of objects of class File to XML

    :param obj: object of class File
    :param tag: tag of the serialized element, default is "file"
    :return: serialized ElementTree object
    """
    et_file = abstract_classes_to_xml(tag, obj)
    et_file.append(_generate_element(NS_AAS + "mimeType", text=obj.mime_type))
    if obj.value:
        et_file.append(_generate_element(NS_AAS + "value", text=obj.value))
    return et_file


def reference_element_to_xml(obj: model.ReferenceElement,
                             tag: str = NS_AAS+"referenceElement") -> etree.Element:
    """
    serialization of objects of class ReferenceElement to XMl

    :param obj: object of class ReferenceElement
    :param tag: namespace+tag of the serialized element (optional), default is "referenceElement"
    :return: serialized ElementTree object
    """
    et_reference_element = abstract_classes_to_xml(tag, obj)
    if obj.value:
        et_reference_element.append(reference_to_xml(obj.value, NS_AAS+"value"))
    return et_reference_element


def submodel_element_collection_to_xml(obj: model.SubmodelElementCollection,
                                       tag: str = NS_AAS+"submodelElementCollection") -> etree.Element:
    """
    serialization of objects of class SubmodelElementCollection to XML

    Note that we do not have parameter "allowDuplicates" in out implementation

    :param obj: object of class SubmodelElementCollection
    :param tag: namespace+tag of the serialized element (optional), default is "submodelElementCollection"
    :return: serialized ElementTree object
    """
    et_submodel_element_collection = abstract_classes_to_xml(tag, obj)
    # todo: remove wrapping submodelElement-tag, in accordance to future schema
    et_value = _generate_element(NS_AAS + "value")
    if obj.value:
        for submodel_element in obj.value:
            et_submodel_element = _generate_element(NS_AAS+"submodelElement")
            et_submodel_element.append(submodel_element_to_xml(submodel_element))
            et_value.append(et_submodel_element)
    et_submodel_element_collection.append(et_value)
    et_submodel_element_collection.append(_generate_element(NS_AAS + "ordered", text=boolean_to_xml(obj.ordered)))
    et_submodel_element_collection.append(_generate_element(NS_AAS + "allowDuplicates", text="false"))
    return et_submodel_element_collection


def relationship_element_to_xml(obj: model.RelationshipElement,
                                tag: str = NS_AAS+"relationshipElement") -> etree.Element:
    """
    serialization of objects of class RelationshipElement to XML

    :param obj: object of class RelationshipElement
    :param tag: tag of the serialized element (optional), default is "relationshipElement"
    :return: serialized ELementTree object
    """
    et_relationship_element = abstract_classes_to_xml(tag, obj)
    et_relationship_element.append(reference_to_xml(obj.first, NS_AAS+"first"))
    et_relationship_element.append(reference_to_xml(obj.second, NS_AAS+"second"))
    return et_relationship_element


def annotated_relationship_element_to_xml(obj: model.AnnotatedRelationshipElement,
                                          tag: str = NS_AAS+"annotatedRelationshipElement") -> etree.Element:
    """
    serialization of objects of class AnnotatedRelationshipElement to XML

    :param obj: object of class AnnotatedRelationshipElement
    :param tag: tag of the serialized element (optional), default is "annotatedRelationshipElement
    :return: serialized ElementTree object
    """
    et_annotated_relationship_element = relationship_element_to_xml(obj, tag)
    et_annotations = _generate_element(name=NS_AAS+"annotations")
    if obj.annotation:
        for data_element in obj.annotation:
            et_annotations.append(data_element_to_xml(data_element))
    et_annotated_relationship_element.append(et_annotations)
    return et_annotated_relationship_element


def operation_variable_to_xml(obj: model.OperationVariable,
                              tag: str = NS_AAS+"operationVariable") -> etree.Element:
    """
    serialization of objects of class OperationVariable to XML

    :param obj: object of class OperationVariable
    :param tag: tag of the serialized element (optional), default is "operationVariable"
    :return: serialized ElementTree object
    """
    et_operation_variable = _generate_element(tag)
    et_value = _generate_element(NS_AAS+"value")
    et_value.append(submodel_element_to_xml(obj.value))
    et_operation_variable.append(et_value)
    return et_operation_variable


def operation_to_xml(obj: model.Operation,
                     tag: str = NS_AAS+"operation") -> etree.Element:
    """
    serialization of objects of class Operation to XML

    :param obj: object of class Operation
    :param tag: namespace+tag of the serialized element (optional), default is "operation"
    :return: serialized ElementTree object
    """
    et_operation = abstract_classes_to_xml(tag, obj)
    if obj.input_variable:
        for input_ov in obj.input_variable:
            et_operation.append(operation_variable_to_xml(input_ov, NS_AAS+"inputVariable"))
    if obj.output_variable:
        for output_ov in obj.output_variable:
            et_operation.append(operation_variable_to_xml(output_ov, NS_AAS+"outputVariable"))
    if obj.in_output_variable:
        for in_out_ov in obj.in_output_variable:
            et_operation.append(operation_variable_to_xml(in_out_ov, NS_AAS+"inoutputVariable"))
    return et_operation


def capability_to_xml(obj: model.Capability,
                      tag: str = NS_AAS+"capability") -> etree.Element:
    """
    serialization of objects of class Capability to XML

    :param obj: object of class Capability
    :param tag: tag of the serialized element, default is "capability"
    :return: serialized ElementTree object
    """
    return abstract_classes_to_xml(tag, obj)


def entity_to_xml(obj: model.Entity,
                  tag: str = NS_AAS+"entity") -> etree.Element:
    """
    serialization of objects of class Entity to XML

    :param obj: object of class Entity
    :param tag: tag of the serialized element (optional), default is "entity"
    :return: serialized ElementTree object
    """
    # todo: remove wrapping submodelElement, in accordance to future schemas
    et_entity = abstract_classes_to_xml(tag, obj)
    et_statements = _generate_element(NS_AAS + "statements")
    for statement in obj.statement:
        # todo: remove the <submodelElement> once the proposed changes get accepted
        et_submodel_element = _generate_element(NS_AAS+"submodelElement")
        et_submodel_element.append(submodel_element_to_xml(statement))
        et_statements.append(et_submodel_element)
    et_entity.append(et_statements)
    et_entity.append(_generate_element(NS_AAS + "entityType", text=_generic.ENTITY_TYPES[obj.entity_type]))
    if obj.asset:
        et_entity.append(reference_to_xml(obj.asset, NS_AAS+"assetRef"))
    return et_entity


def basic_event_to_xml(obj: model.BasicEvent,
                       tag: str = NS_AAS+"basicEvent") -> etree.Element:
    """
    serialization of objects of class BasicEvent to XML

    :param obj: object of class BasicEvent
    :param tag: tag of the serialized element (optional), default is "basicEvent"
    :return: serialized ElementTree object
    """
    et_basic_event = abstract_classes_to_xml(tag, obj)
    et_basic_event.append(reference_to_xml(obj.observed, NS_AAS+"observed"))
    return et_basic_event


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
    :param data: ObjectStore which contains different objects of the AAS meta model which should be serialized to an
                 XML file
    :param kwargs: Additional keyword arguments to be passed to tree.write()
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
    root = etree.Element(NS_AAS + "aasenv", nsmap=NS_MAP)
    et_asset_administration_shells = etree.Element(NS_AAS + "assetAdministrationShells")
    for aas_obj in asset_administration_shells:
        et_asset_administration_shells.append(asset_administration_shell_to_xml(aas_obj))
    et_assets = _generate_element(NS_AAS + "assets")
    for ass_obj in assets:
        et_assets.append(asset_to_xml(ass_obj))
    et_submodels = etree.Element(NS_AAS + "submodels")
    for sub_obj in submodels:
        et_submodels.append(submodel_to_xml(sub_obj))
    et_concept_descriptions = etree.Element(NS_AAS + "conceptDescriptions")
    for con_obj in concept_descriptions:
        et_concept_descriptions.append(concept_description_to_xml(con_obj))
    root.insert(0, et_concept_descriptions)
    root.insert(0, et_submodels)
    root.insert(0, et_assets)
    root.insert(0, et_asset_administration_shells)

    tree = etree.ElementTree(root)
    tree.write(file, encoding="UTF-8", xml_declaration=True, method="xml", **kwargs)
