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
from typing import List, Dict, Iterator, IO, Optional
import inspect
import base64

from aas import model


# ##############################################################
# functions to manipulate ElTree.Elements more effectively
# ##############################################################

# Namespace definition
ns_aas = "{http://www.admin-shell.io/aas/2/0}"
ns_abac = "{http://www.admin-shell.io/aas/abac/2/0}"
ns_aas_common = "{http://www.admin-shell.io/aas_common/2/0}"
ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
ns_iec = "{http://www.admin-shell.io/IEC61360/2/0}"


def generate_element(name: str,
                     text: Optional[str] = None,
                     attributes: Optional[Dict] = None,
                     namespace: str = ns_aas) -> ElTree.Element:
    """
    generate an ElementTree.Element object

    :param name: Name of the element
    :param text: Text of the element. Default is None
    :param attributes: Attributes of the elements in form of a dict {"attribute_name": "attribute_content"}
    :param namespace: Namespace of the element as. Default is the AAS namespace
    :return: ElementTree.Element object
    """
    # todo: is there the option to not specify a namespace?
    et_element = ElTree.Element(namespace+name)
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


def find_rec(parent: ElTree.Element, tag: str) -> Iterator[ElTree.Element]:
    """
    Finds all elements recursively that have the given tag

    todo: Check if this really works as intended

    :param parent: ElTree.Element object to search through
    :param tag: tag of the ElTree.Element to find
    :return: List of ElTree.Elements that have the tag
    """
    for item in parent.findall(tag):
        yield item
    for item in parent:
        find_rec(item, tag)


def update_element(old_element: ElTree.Element,
                   new_element: ElTree.Element) -> ElTree.Element:
    """
    update an existing ElTree.Element with a new ElTree.Elements

    The new_element can be a child, or sub..-child of the old_element.
    ToDo: Check if this works as expected
    todo: Is this the correct type of error raised?

    :param old_element: Element to update
    :param new_element: ElTree.Element with the data for update
    :return: ElTree.Element with the updated information
    """
    elements_to_update = list(find_rec(old_element, new_element.tag))  # search for elements that match new_element
    if len(elements_to_update) > 1:  # more than one element found that matches with new_element, sth went wrong.
        raise ValueError("Found " + str(len(elements_to_update)) + " elements [" + new_element.tag +
                                                                   "] in " + old_element.tag + ". Expected 1")
    if elements_to_update is not []:  # if the element already exists, remove the outdated element
        old_element.remove(elements_to_update[0])
    old_element.insert(0, new_element)  # insert the new_element
    return old_element


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


def referable_to_xml(obj: model.Referable) -> List[ElTree.Element]:
    """
    serialization of objects of class Referable to XML

    :param obj: object of class Referable
    :return: List of ElementTree object to insert into the parent element
    """
    ser_list: List[ElTree.Element] = []
    et_id_short = generate_element(name="idShort", text=obj.id_short, namespace=ns_aas)
    ser_list += [et_id_short]
    if obj.category:
        et_category = generate_element(name="category", text=obj.category, namespace=ns_aas)
        ser_list += [et_category]
    if obj.description:
        et_description = lang_string_set_to_xml(obj.description, name="description")
        ser_list += [et_description]
    return ser_list


def identifiable_to_xml(obj: model.Identifiable) -> List[ElTree.Element]:
    """
    serialization of objects of class Identifiable to XML

    :param obj: object of class Identifiable
    :return: List of serialized ElementTree objects to insert into the parent
    """
    ser_list: List[ElTree.Element] = []
    et_identification = generate_element(name="identification",
                                         text=obj.identification.id,
                                         attributes={"idType": IDENTIFIER_TYPES[obj.identification.id_type]},
                                         namespace=ns_aas)
    ser_list += [et_identification]
    if obj.administration:
        et_administration = generate_element(name="administration", text=None, namespace=ns_aas)
        if obj.administration.version:
            et_version = generate_element(name="version", text=obj.administration.version, namespace=ns_aas)
            et_administration.insert(0, et_version)
            if obj.administration.revision:
                et_revision = generate_element(name="revision", text=obj.administration.revision, namespace=ns_aas)
                et_administration.insert(1, et_revision)
        ser_list += [et_administration]
    return ser_list


def has_data_specification_to_xml(obj: model.HasDataSpecification) -> List[ElTree.Element]:
    """
    serialization of objects of class HasDataSpecification to XML

    :param obj: object of class HasDataSpecification
    :return: list of serialized ElemenTree objects to insert into parent
    """
    ser_list: List[ElTree.Element] = []
    for embedded_data_specification in obj.data_specification:
        et_embedded_data_specification = generate_element(name="embeddedDataSpecification",
                                                          text=None,
                                                          namespace=ns_aas)
        et_data_spec_content = generate_element(name="dataSpecificationContent")  # todo: not done yet
        et_data_spec = generate_element(name="dataSpecification")
        for et_key in reference_to_xml(embedded_data_specification):
            et_data_spec.insert(0, et_key)
        et_embedded_data_specification.insert(0, et_data_spec_content)
        et_embedded_data_specification.insert(0, et_data_spec)
        ser_list += [et_embedded_data_specification]
    return ser_list


def abstract_classes_to_xml(obj: object) -> List[ElTree.Element]:
    """
    transformation function to serialize abstract classes from model.base which are inherited by many classes.

    If the object obj is inheriting from an abstract class, this function returns the serialized information from that
    abstract class in form of ElementTree objects in a list.

    :param obj: an object of the AAS
    :return: a list of ElementTree.Elements to be inserted into the parent Element of the object
    """
    elements: List[ElTree.Element] = []
    if isinstance(obj, model.Referable):
        for referable_element in referable_to_xml(obj):
            elements += [referable_element]
        """
        try:  # todo: What does this do? What do we need it for?
            ref_type = next(iter(t for t in inspect.getmro(type(obj)) if t in model.KEY_ELEMENTS_CLASSES))
        except StopIteration as e:
            raise TypeError("Object of type {} is Referable but does not inherit from a known AAS type"
                            .format(obj.__class__.__name__)) from e
        et_model_type = ElTree.Element("modelType")
        et_model_type.text = ref_type.__name__
        elements += [et_model_type]
        """
    if isinstance(obj, model.Identifiable):
        for identifiable_elements in identifiable_to_xml(obj):
            elements += [identifiable_elements]

    if isinstance(obj, model.HasDataSpecification):
        if obj.data_specification:
            for data_spec_element in has_data_specification_to_xml(obj):
                elements += [data_spec_element]

    if isinstance(obj, model.HasSemantics):
        if obj.semantic_id:
            et_semantics = generate_element(name="semanticId", text=None, namespace=ns_aas)
            for et_key in reference_to_xml(obj.semantic_id):
                et_semantics.insert(0, et_key)
            elements += [et_semantics]

    if isinstance(obj, model.HasKind):
        # todo: it's not possible to HaveKind and not have a kind
        if obj.kind is model.ModelingKind.TEMPLATE:
            et_modeling_kind = generate_element(name="kind", text="Template", namespace=ns_aas)
            elements += [et_modeling_kind]
        elif obj.kind is model.ModelingKind.INSTANCE:
            et_modeling_kind = generate_element(name="kind", text="Instance", namespace=ns_aas)
            elements += [et_modeling_kind]

    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            et_qualifier = generate_element(name="qualifier", text=None, namespace=ns_aas)
            for qual in obj.qualifier:
                et_qualifiers = constraint_to_xml(qual, name="qualifiers")
                et_qualifier.insert(0, et_qualifiers)
                # todo: seems like the XSD-schema messed up the plural "s"?
                # todo: formula and qualifier seem not to be implemented yet
            elements += [et_qualifier]

    return elements


# ##############################################################
# transformation functions to serialize classes from model.base
# ##############################################################


def lang_string_set_to_xml(obj: model.LangStringSet, name: str) -> ElTree.Element:
    """
    serialization of objects of class LangStringSet to XML

    :param obj: object of class LangStringSet
    :param name: Name of the returned element
    :return: serialized ElementTree object
    """
    et_lss = generate_element(name=name, text=None, namespace=ns_aas)
    for language in obj:
        et_lang_string = generate_element(name="langString",
                                          text=obj[language],
                                          attributes={"lang": language},
                                          namespace=ns_aas)
        et_lss.insert(0, et_lang_string)
    return et_lss


def key_to_xml(obj: model.Key) -> ElTree.Element:
    """
    serialization of objects of class Key to XML

    todo: the value of the key is in its text, the XSD-schema was not clear about where to put it

    :param obj: object of class Key
    :return: serialized ElementTree object
    """
    et_key = generate_element(name="key",
                              text=obj.value,
                              attributes={"idType": KEY_TYPES[obj.id_type],
                                          "local": boolean_to_xml(obj.local),
                                          "type": KEY_ELEMENTS[obj.type_]},
                              namespace=ns_aas)
    return et_key


def administrative_information_to_xml(obj: model.AdministrativeInformation) -> ElTree.Element:
    """
    serialization of objects of class AdministrativeInformation to XML

    :param obj: object of class AdministrativeInformation
    :return: serialized ElementTree object
    """
    et_administration = generate_element(name="administration", text=None, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_administration.insert(0, i)
    if obj.version:
        et_administration_version = generate_element(name="version",
                                                     text=obj.version,
                                                     namespace=ns_aas)
        et_administration = update_element(et_administration, et_administration_version)
        if obj.revision:
            et_administration_revision = generate_element(name="revision",
                                                          text=obj.revision,
                                                          namespace=ns_aas)
            et_administration = update_element(et_administration, et_administration_revision)
    return et_administration


def identifier_to_xml(obj: model.Identifier) -> ElTree.Element:
    """
    serialization of objects of class Identifier to XML

    todo: XSD Schema type identifier_t is never used, so unclear how to name parent element

    :param obj: object of class Identifier
    :return: serialized ElementTree object
    """
    et_identifier = generate_element(name="identifier", text=None, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_identifier.insert(0, i)
    et_id = generate_element(name="id", text=obj.id, namespace=ns_aas)
    et_id_type = generate_element(name="idType", text=IDENTIFIER_TYPES[obj.id_type], namespace=ns_aas)
    et_identifier.insert(0, et_id_type)
    et_identifier.insert(0, et_id)
    return et_identifier


def reference_to_xml(obj: model.Reference) -> ElTree.Element:
    """
    serialization of objects of class Reference to XML

    How to use: For serializing a reference with name "nameExample", generate a new empty ElementTree object with that
                name (Don't forget the namespace!) and insert the returned ElementTree object from this function into
                the ElementTree object with name "nameExample".

    :param obj: object of class Reference
    :return: serialized ElementTree object with name "keys"
    """
    et_keys = ElTree.Element("keys")
    for aas_key in obj.key:
        et_key = key_to_xml(aas_key)
        et_keys.insert(0, et_key)
    return et_keys


def constraint_to_xml(obj: model.Constraint, name: str) -> ElTree.Element:
    """
    serialization of objects of class Constraint to XML

    todo: implement correctly

    :param obj: object of class Constraint
    :param name: Name of the ElementTree object that is of type constraint_t
    :return: serialized ElementTree object
    """
    constraint_classes = [model.Qualifier, model.Formula]
    et_constraint = generate_element(name=name, text=None, namespace=ns_aas)
    try:
        const_type = next(iter(t for t in inspect.getmro(type(obj)) if t in constraint_classes))
    except StopIteration as e:
        raise TypeError("Object of type {} is a Constraint but does not inherit from a known AAS Constraint type"
                        .format(obj.__class__.__name__)) from e
    # if const_type is model.Qualifier:
        # et_qualifier = qualifier_to_xml(obj.)
    et_constraint.set("modelType", const_type.__name__)
    return et_constraint


def namespace_to_xml(obj: model.Namespace) -> ElTree.Element:
    """
    serialization of objects of class Namespace to XML

    todo: Since this is not yet part of the Details of the AAS model, it's not entirely clear how to serialize this

    :param obj: object of class Namespace
    :return: serialized ElementTree Object
    """
    et_namespace = generate_element(name="namespace", text=None, namespace="local")
    for i in abstract_classes_to_xml(obj):
        et_namespace.insert(0, i)
    return et_namespace


def formula_to_xml(obj: model.Formula, name: str = "formula") -> ElTree.Element:
    """
    serialization of objects of class Formula to XML

    :param obj: object of class Formula
    :param name: name of the ElementTree object, default is "formula"
    :return: serialized ElementTree object
    """
    et_formula = generate_element(name=name, text=None, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_formula.insert(0, i)
    if obj.depends_on:
        et_depends_on = generate_element(name="dependsOnRefs", text=None, namespace=ns_aas)
        for aas_reference in obj.depends_on:
            et_ref = generate_element(name="reference", text=None, namespace=ns_aas)
            et_keys = reference_to_xml(aas_reference)
            et_ref.insert(0, et_keys)
            et_depends_on.insert(0, et_ref)
        et_formula.insert(0, et_depends_on)
    return et_formula


def qualifier_to_xml(obj: model.Qualifier, name: str = "qualifier") -> ElTree.Element:
    """
    serialization of objects of class Qualifier to XML

    :param obj: object of class Qualifier
    :param name: name of the serialized ElementTree object, default is "qualifier"
    :return: serialized ElementTreeObject
    """
    et_qualifier = generate_element(name=name, text=None, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_qualifier.insert(0, i)
    if obj.value:
        et_value = ElTree.Element(ns_aas+"value")
        et_value.text = obj.value  # should be a string, since ValueDataType is a string
        et_qualifier.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element(ns_aas+"valueId")
        et_value_id.insert(0, reference_to_xml(obj.value_id))
        et_qualifier.insert(0, et_value_id)
    et_value_type = ElTree.Element(ns_aas+"valueType")
    et_value_type.text = obj.value_type  # should be a string, so no problems
    et_qualifier.insert(0, et_value_type)

    et_type = ElTree.Element(ns_aas+"type")
    et_type.text = obj.type_  # should be a string as well
    et_qualifier.insert(0, et_type)

    return et_qualifier


def value_reference_pair_to_xml(obj: model.ValueReferencePair) -> ElTree.Element:
    """
    serialization of objects of class ValueReferencePair to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueReferencePair
    :return: serialized ElementTree object
    """
    et_vrp = ElTree.Element(ns_aas+"valueReferencePair")
    for i in abstract_classes_to_xml(obj):
        et_vrp.insert(0, i)
    et_value = ElTree.Element(ns_aas+"value")
    et_value.text = obj.value  # since obj.value is of type ValueDataType, which is a string, it should be fine
    et_vrp.insert(0, et_value)
    et_value_id = ElTree.Element(ns_aas+"valueId")
    et_value_id.insert(0, reference_to_xml(obj.value_id))  # obj.value_id is a Reference
    et_vrp.insert(0, et_value_id)
    return et_vrp


def value_list_to_xml(obj: model.ValueList) -> ElTree.Element:
    """
    serialization of objects of class ValueList to XML

    todo: couldn't find it in the official schema, so guessing how to implement serialization

    :param obj: object of class ValueList
    :return: serialized ElementTree object
    """
    et_vl = ElTree.Element(ns_aas+"valueList")
    for i in abstract_classes_to_xml(obj):
        et_vl.insert(0, i)
    for aas_reference_pair in obj.value_reference_pair_type:
        et_value_reference_pair = value_reference_pair_to_xml(aas_reference_pair)
        et_vl.insert(0, et_value_reference_pair)
    return et_vl


# ##############################################################
# transformation functions to serialize classes from model.aas
# ##############################################################


def view_to_xml(obj: model.View, name: str = "view") -> ElTree.Element:
    """
    serialization of objects of class View to XML

    :param obj: object of class View
    :param name: name of the ELementTree object. default is "view"
    :return: serialized ElementTree object
    """
    et_view = generate_element(name=name, text=None, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_view.insert(0, i)
    if obj.contained_element:
        et_contained_elements = generate_element(name="containedElements")
        for contained_element in obj.contained_element:
            et_contained_element_ref = generate_element(name="containedElementRef", namespace=ns_aas)
            et_contained_element_ref.insert(0, reference_to_xml(contained_element))
            et_contained_elements.insert(0, et_contained_element_ref)
        et_view.insert(0, et_contained_elements)
    return et_view


def asset_to_xml(obj: model.Asset, name: str = "asset") -> ElTree.Element:
    """
    serialization of objects of class Asset to XML

    :param obj: object of class Asset
    :param name: name of the ElementTree object. default is "asset"
    :return: serialized ElementTree object
    """
    et_asset = generate_element(name=name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_asset.insert(0, i)
    et_kind = generate_element(name="kind", text=ASSET_KIND[obj.kind], namespace=ns_aas)
    et_asset.insert(0, et_kind)
    if obj.asset_identification_model:
        et_asset_identification_model = ElTree.Element(ns_aas+"assetIdentificationModelRef")
        et_asset_identification_model.insert(0, reference_to_xml(obj.asset_identification_model))
        et_asset.insert(0, et_asset_identification_model)
    if obj.bill_of_material:
        et_bill_of_material = ElTree.Element("billOfMaterialRef")
        et_bill_of_material.insert(0, reference_to_xml(obj.bill_of_material))
        et_asset.insert(0, et_bill_of_material)
    return et_asset


def concept_description_to_xml(obj: model.ConceptDescription,
                               name: str = "conceptDescription") -> ElTree.Element:
    """
    serialization of objects of class ConceptDescription to XML

    :param obj: object of class ConceptDescription
    :param name: name of the ElementTree object. default is "conceptDescription"
    :return: serialized ElementTree object
    """
    et_concept_description = generate_element(name=name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_concept_description.insert(0, i)
    if obj.is_case_of:
        for reference in obj.is_case_of:
            et_is_case_of = generate_element(name="isCaseOf", namespace=ns_aas)
            et_is_case_of.insert(0, reference_to_xml(reference))
            et_concept_description.insert(0, et_is_case_of)
    return et_concept_description


def concept_dictionary_to_xml(obj: model.ConceptDictionary,
                              name: str = "conceptDictionary") -> ElTree.Element:
    """
    serialization of objects of class ConceptDictionary to XML

    :param obj: object of class ConceptDictionary
    :param name: name of the ElementTree object. default is "conceptDictionary"
    :return: serialized ElementTree object
    """
    et_concept_dictionary = generate_element(name=name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_concept_dictionary.insert(0, i)
    if obj.concept_description:
        et_concept_descriptions_refs = ElTree.Element(ns_aas+"conceptDescriptionRefs")
        for reference in obj.concept_description:
            et_concept_description_ref = ElTree.Element(ns_aas+"conceptDescriptionRef")
            et_concept_description_ref.insert(0, reference_to_xml(reference))
            et_concept_descriptions_refs.insert(0, et_concept_description_ref)
        et_concept_dictionary.insert(0, et_concept_descriptions_refs)
    return et_concept_dictionary


def asset_administration_shell_to_xml(obj: model.AssetAdministrationShell,
                                      name: str = "assetAdministrationShell") -> ElTree.Element:
    """
    serialization of objects of class AssetAdministrationShell to XML

    :param obj: object of class AssetAdministrationShell
    :param name: name of the ElementTree object. default is "assetAdministrationShell"
    :return: serialized ElementTree object
    """
    et_aas = generate_element(name)
    for i in abstract_classes_to_xml(obj):
        et_aas.insert(0, i)
    et_namespace = namespace_to_xml(obj)
    et_aas = update_element(et_aas, et_namespace)  # todo: do i need this line?
    if obj.derived_from:
        et_derived_from = generate_element("derivedFrom", namespace=ns_aas)
        et_reference = reference_to_xml(obj.derived_from)
        et_derived_from.insert(0, et_reference)
        et_aas.insert(0, et_derived_from)
    et_asset = generate_element("assetRef", namespace=ns_aas)
    et_ref_asset = reference_to_xml(obj.asset)
    et_asset.insert(0, et_ref_asset)
    et_aas.insert(0, et_asset)
    if obj.submodel_:
        et_submodels = generate_element("submodelRefs", namespace=ns_aas)
        for reference in obj.submodel_:
            et_ref_submodel = generate_element("submodelRef", namespace=ns_aas)
            et_ref_keys = reference_to_xml(reference)
            et_ref_submodel.insert(0, et_ref_keys)
            et_submodels.insert(0, et_ref_submodel)
        et_aas.insert(0, et_submodels)
    if obj.view:
        et_views = generate_element("views", namespace=ns_aas)
        for view in obj.view:
            et_view = view_to_xml(view, name="view")
            et_views.insert(0, et_view)
        et_aas.insert(0, et_views)
    if obj.concept_dictionary:
        et_concept_dictionaries = generate_element("conceptDictionaries", namespace=ns_aas)
        for concept_dictionary in obj.concept_dictionary:
            et_concept_dictionary = concept_dictionary_to_xml(concept_dictionary)
            et_concept_dictionaries.insert(0, et_concept_dictionary)
        et_aas.insert(0, et_concept_dictionaries)
    if obj.security_:
        et_security = security_to_xml(obj.security_, name="security")
        et_aas.insert(0, et_security)
    return et_aas


# ##############################################################
# transformation functions to serialize classes from model.security
# ##############################################################


def security_to_xml(obj: model.Security,
                    name: str = "security") -> ElTree.Element:
    """
    serialization of objects of class Security to XML

    todo: This is not yet implemented

    :param obj: object of class Security
    :param name: tag of the serialized element (optional). Default is "security"
    :return: serialized ElementTree object
    """
    et_security = generate_element(name, namespace=ns_abac)
    for i in abstract_classes_to_xml(obj):
        et_security.insert(0, i)
    return et_security


# ##############################################################
# transformation functions to serialize classes from model.submodel
# ##############################################################


def submodel_element_to_xml(obj: model.SubmodelElement,
                            name: str = "submodelElement") -> ElTree.Element:
    """
    serialization of objects of class SubmodelElement to XML

    todo: this seems to miss in the json implementation? Because it consists only of inherited parameters?
    todo: this seems to be different in the schema and in our implementation

    :param obj: object of class SubmodelElement
    :param name: tag of the serialized element (optional), default is "submodelElement"
    :return: serialized ElementTree object
    """
    et_submodel_element = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_submodel_element.insert(0, i)
    return et_submodel_element


def submodel_to_xml(obj: model.Submodel,
                    name: str = "submodel") -> ElTree.Element:
    """
    serialization of objects of class Submodel to XML

    :param obj: object of class Submodel
    :param name: tag of the serialized element (optional). Default is "submodel"
    :return: serialized ElementTree object
    """
    et_submodel = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_submodel.insert(0, i)
    if obj.submodel_element:
        et_submodel_elements = generate_element("submodelElements", namespace=ns_aas)
        for submodel_element in obj.submodel_element:
            et_submodel_element = submodel_element_to_xml(submodel_element)
            et_submodel_elements.insert(0, et_submodel_element)
        et_submodel.insert(0, et_submodel_elements)
    return et_submodel


def data_element_to_xml(obj: model.DataElement) -> ElTree.Element:
    """
    serialization of objects of class DataElement to XML

    :param obj: object of class DataElement
    :return: serialized ElementTree object
    """
    et_data_element = ElTree.Element(ns_aas+"dataElement")
    for i in abstract_classes_to_xml(obj):
        et_data_element.insert(0, i)
    return et_data_element


def property_to_xml(obj: model.Property,
                    name: str = "property") -> ElTree.Element:
    """
    serialization of objects of class Property to XML

    :param obj: object of class Property
    :param name: tag of the serialized element (optional), default is "property"
    :return: serialized ElementTree object
    """
    et_property = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_property.insert(0, i)
    if obj.value:
        et_value = ElTree.Element(ns_aas+"value")
        et_value.text = obj.value
        et_property.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element(ns_aas+"valueId")
        et_reference = reference_to_xml(obj.value_id)
        et_value_id.insert(0, et_reference)
        et_property.insert(0, et_value_id)
    et_value_type = ElTree.Element(ns_aas+"valueType")
    et_value_type.text = obj.value_type
    et_property.insert(0, et_value_type)
    return et_property


def multi_language_property_to_xml(obj: model.MultiLanguageProperty,
                                   name: str = "multiLanguageProperty") -> ElTree.Element:
    """
    serialization of objects of class MultiLanguageProperty to XML

    :param obj: object of class MultiLanguageProperty
    :param name: tag of the serialized element (optional), default is "multiLanguageProperty"
    :return: serialized ElementTree object
    """
    et_multi_language_property = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_multi_language_property.insert(0, i)
    if obj.value:
        et_value = lang_string_set_to_xml(obj.value, name="value")
        et_multi_language_property.insert(0, et_value)
    if obj.value_id:
        et_value_id = ElTree.Element(ns_aas+"valueId")
        et_reference = reference_to_xml(obj.value_id)
        et_value_id.insert(0, et_reference)
        et_multi_language_property.insert(0, et_value_id)
    return et_multi_language_property


def range_to_xml(obj: model.Range,
                 name: str = "range") -> ElTree.Element:
    """
    serialization of objects of class Range to XML

    :param obj: object of class Range
    :param name: tag of the serialized element (optional), default is "range
    :return: serialized ElementTree object
    """
    et_range = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_range.insert(0, i)
    et_value_type = ElTree.Element(ns_aas+"valueType")
    et_value_type.text = obj.value_type
    et_range = update_element(et_range, et_value_type)
    if obj.min_:
        et_min = ElTree.Element(ns_aas+"min")
        et_min.text = obj.min_
        et_range = update_element(et_range, et_min)
    if obj.max_:
        et_max = ElTree.Element(ns_aas+"max")
        et_max.text = obj.max_
        et_range = update_element(et_range, et_max)
    return et_range


def blob_to_xml(obj: model.Blob) -> ElTree.Element:
    """
    serialization of objects of class Blob to XML

    :param obj: object of class Blob
    :return: serialized ElementTree object
    """
    et_blob = ElTree.Element(ns_aas+"blob")
    for i in abstract_classes_to_xml(obj):
        et_blob.insert(0, i)
    et_mime_type = ElTree.Element(ns_aas+"mimeType")
    et_mime_type.text = obj.mime_type  # base.MimeType = str
    et_blob.insert(0, et_mime_type)

    et_value = ElTree.Element(ns_aas+"value")
    if obj.value is not None:
        et_value.text = base64.b64encode(obj.value).decode()
    et_blob.insert(0, et_value)
    return et_blob


def file_to_xml(obj: model.File) -> ElTree.Element:
    """
    serialization of objects of class File to XML

    :param obj: object of class File
    :return: serialized ElementTree object
    """
    et_file = ElTree.Element(ns_aas+"file")
    for i in abstract_classes_to_xml(obj):
        et_file.insert(0, i)
    et_value = ElTree.Element(ns_aas+"value")
    et_value.text = obj.value  # base.PathType = str
    # et_file = update_element(et_file, et_value)
    # only reason to update would be if there was already such an entry for it somewhere
    et_file.insert(0, et_value)
    et_mime_type = ElTree.Element(ns_aas+"mimeType")
    et_mime_type.text = obj.mime_type
    # et_file = update_element(et_file, et_mime_type)
    et_file.insert(0, et_mime_type)
    return et_file


def reference_element_to_xml(obj: model.ReferenceElement,
                             name: str = "referenceElement") -> ElTree.Element:
    """
    serialization of objects of class ReferenceElement to XMl

    :param obj: object of class ReferenceElement
    :param name: tag of the serialized element (optional), default is "referenceElement"
    :return: serialized ElementTree object
    """
    et_reference_element = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_reference_element.insert(0, i)
    if obj.value:
        et_value = ElTree.Element(ns_aas+"value")
        et_ref = reference_to_xml(obj.value)
        et_value.insert(0, et_ref)
        et_reference_element.insert(0, et_value)
    return et_reference_element


def submodel_element_collection_to_xml(obj: model.SubmodelElementCollection,
                                       name: str = "submodelElementCollection") -> ElTree.Element:
    """
    serialization of objects of class SubmodelElementCollection to XML

    Note that we do not have parameter "allowDuplicates" in out implementation

    :param obj: object of class SubmodelElementCollection
    :param name: tag of the serialized element (optional), default is "submodelElementCollection"
    :return: serialized ElementTree object
    """
    et_submodel_element_collection = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_submodel_element_collection.insert(0, i)
    if obj.value:
        et_value = ElTree.Element(ns_aas+"value")
        for submodel_element in obj.value:
            et_submodel_element = submodel_element_to_xml(submodel_element)
            et_value.insert(0, et_submodel_element)
        et_submodel_element_collection.insert(0, et_value)
    et_ordered = ElTree.Element(ns_aas+"ordered")
    et_ordered.text = boolean_to_xml(obj.ordered)
    # todo: ordered does not seem to be a boolean in our model?
    et_submodel_element_collection.insert(0, et_ordered)
    return et_submodel_element_collection


def relationship_element_to_xml(obj: model.RelationshipElement,
                                name: str = "relationshipElement") -> ElTree.Element:
    """
    serialization of objects of class RelationshipElement to XML

    :param obj: object of class RelationshipElement
    :param name: tag of the serialized element (optional), default is "relationshipElement"
    :return: serialized ELementTree object
    """
    et_relationship_element = generate_element(name, namespace=ns_aas)
    for i in abstract_classes_to_xml(obj):
        et_relationship_element.insert(0, i)
    et_first = ElTree.Element(ns_aas+"first")
    et_ref1 = reference_to_xml(obj.first)
    et_first.insert(0, et_ref1)
    et_relationship_element.insert(0, et_first)

    et_second = ElTree.Element(ns_aas+"second")
    et_ref2 = reference_to_xml(obj.second)
    et_second.insert(0, et_ref2)
    et_relationship_element.insert(0, et_second)

    return et_relationship_element


def annotated_relationship_element_to_xml(obj: model.AnnotatedRelationshipElement,
                                          name: str = "annotatedRelationshipElement") -> ElTree.Element:
    """
    serialization of objects of class AnnotatedRelationshipElement to XML

    todo: in the schema, annotatedRelationshipElement is of type relationshipElement_t, so there is no way to store
    todo: the annotations in the schema
    todo: I guessed the implementation, but of course, the namespace is wrong

    :param obj: object of class AnnotatedRelationshipElement
    :param name: tag of the serialized element (optional), default is "annotatedRelationshipElement
    :return: serialized ElementTree object
    """
    et_annotated_relationship_element = relationship_element_to_xml(obj, name)
    if obj.annotation:
        et_annotations = ElTree.Element(ns_aas+"annotations")
        for ref in obj.annotation:
            et_annotation = generate_element("annotation", namespace="none:")
            et_reference = reference_to_xml(ref)
            et_annotation.insert(0, et_reference)
            et_annotations.insert(0, et_annotation)
        et_annotated_relationship_element.insert(0, et_annotations)

    return et_annotated_relationship_element


def operation_variable_to_xml(obj: model.OperationVariable,
                              name: str = "operationVariable") -> ElTree.Element:
    """
    serialization of objects of class OperationVariable to XML

    :param obj: object of class OperationVariable
    :param name: tag of the serialized element (optional), default is "operationVariable"
    :return: serialized ElementTree object
    """
    et_operation_variable = generate_element(name)
    for i in abstract_classes_to_xml(obj):
        et_operation_variable.insert(0, i)
    et_value = submodel_element_to_xml(obj.value, name="value")
    et_operation_variable.insert(0, et_value)
    return et_operation_variable


def operation_to_xml(obj: model.Operation,
                     name: str = "operation") -> ElTree.Element:
    """
    serialization of objects of class Operation to XML

    todo: operation_variables are of type NamespaceSet[OperationVariable], not sure how to deal with this

    :param obj: object of class Operation
    :param name: tag of the serialized element (optional), default is "operation"
    :return: serialized ElementTree object
    """
    et_operation = generate_element(name)
    for i in abstract_classes_to_xml(obj):
        et_operation.insert(0, i)
    """
    et_input_var = operation_variable_to_xml(obj.input_variable, name="inputVariable")
    et_output_var = operation_variable_to_xml(obj.output_variable, name="outputVariable")
    et_inout_var = operation_variable_to_xml(obj.in_output_variable, name="inoutputVariable")
    et_operation.insert(0, et_inout_var)
    et_operation.insert(0, et_output_var)
    et_operation.insert(0, et_input_var)
    """
    return et_operation


def capability_to_xml(obj: model.Capability) -> ElTree.Element:
    """
    serialization of objects of class Capability to XML

    todo: in the schema, a capability is a string, this implementation therefore has the wrong namespace

    :param obj: object of class Capability
    :return: serialized ElementTree object
    """
    et_capability = ElTree.Element("none:"+"capability")
    for i in abstract_classes_to_xml(obj):
        et_capability.insert(0, i)
    return et_capability


def entity_to_xml(obj: model.Entity,
                  name: str = "entity") -> ElTree.Element:
    """
    serialization of objects of class Entity to XML

    :param obj: object of class Entity
    :param name: tag of the serialized element (optional), default is "entity"
    :return: serialized ElementTree object
    """
    et_entity = generate_element(name)
    for i in abstract_classes_to_xml(obj):
        et_entity.insert(0, i)

    et_statements = submodel_element_to_xml(obj.statement, name="statements")
    et_entity.insert(0, et_statements)

    et_entity_type = ElTree.Element(ns_aas+"entityType")
    et_entity_type.text = ENTITY_TYPES[obj.entity_type]
    et_entity.insert(0, et_entity_type)

    if obj.asset:
        et_asset = ElTree.Element(ns_aas+"assetRef")
        et_ref = reference_to_xml(obj.asset)
        et_asset.insert(0, et_ref)
        et_entity.insert(0, et_asset)

    return et_entity


def event_to_xml(obj: model.Event) -> ElTree.Element:
    """
    serialization of objects of class Event to XML

    todo didn't find it in the schema, so guessing implementation, therefore wrong namespace

    :param obj: object of class Event
    :return: serialized ElementTree object
    """
    et_event = ElTree.Element("none:"+"event")
    for i in abstract_classes_to_xml(obj):
        et_event.insert(0, i)
    return et_event


def basic_event_to_xml(obj: model.BasicEvent,
                       name: str = "basicEvent") -> ElTree.Element:
    """
    serialization of objects of class BasicEvent to XML

    :param obj: object of class BasicEvent
    :param name: tag of the serialized element (optional), default is "basicEvent"
    :return: serialized ElementTree object
    """
    et_basic_event = generate_element(name)
    for i in abstract_classes_to_xml(obj):
        et_basic_event.insert(0, i)
    et_observed = ElTree.Element(ns_aas+"observed")
    et_ref = reference_to_xml(obj.observed)
    et_observed.insert(0, et_ref)
    et_basic_event.insert(0, et_observed)
    return et_basic_event


# ##############################################################
# general functions
# ##############################################################


def aas_object_to_xml(obj: object) -> ElTree.Element:
    """
    Takes an object from aas.model and returns its serialized xml.ElementTree.Element object.

    Warning: this function does this non recursive, only for the non-aas-object type of attributes.
             Use aas_object_to_xml for recursive serialization

    :param obj: object from aas.model
    :return: serialized xml.ElementTree.Element object
    """
    if isinstance(obj, model.AssetAdministrationShell):
        return asset_administration_shell_to_xml(obj)
    if isinstance(obj, model.Identifier):
        return identifier_to_xml(obj)
    if isinstance(obj, model.AdministrativeInformation):
        return administrative_information_to_xml(obj)
    if isinstance(obj, model.Reference):
        return reference_to_xml(obj)
    if isinstance(obj, model.Key):
        return key_to_xml(obj)
    if isinstance(obj, model.Asset):
        return asset_to_xml(obj)
    if isinstance(obj, model.Submodel):
        return submodel_to_xml(obj)
    if isinstance(obj, model.Operation):
        return operation_to_xml(obj)
    if isinstance(obj, model.OperationVariable):
        return operation_variable_to_xml(obj)
    if isinstance(obj, model.Capability):
        return capability_to_xml(obj)
    if isinstance(obj, model.BasicEvent):
        return basic_event_to_xml(obj)
    if isinstance(obj, model.Entity):
        return entity_to_xml(obj)
    if isinstance(obj, model.View):
        return view_to_xml(obj)
    if isinstance(obj, model.ConceptDictionary):
        return concept_dictionary_to_xml(obj)
    if isinstance(obj, model.ConceptDescription):
        return concept_description_to_xml(obj)
    if isinstance(obj, model.Property):
        return property_to_xml(obj)
    if isinstance(obj, model.Range):
        return range_to_xml(obj)
    if isinstance(obj, model.MultiLanguageProperty):
        return multi_language_property_to_xml(obj)
    if isinstance(obj, model.File):
        return file_to_xml(obj)
    if isinstance(obj, model.Blob):
        return blob_to_xml(obj)
    if isinstance(obj, model.ReferenceElement):
        return reference_element_to_xml(obj)
    if isinstance(obj, model.SubmodelElementCollection):
        return submodel_element_collection_to_xml(obj)
    if isinstance(obj, model.AnnotatedRelationshipElement):
        return annotated_relationship_element_to_xml(obj)
    if isinstance(obj, model.RelationshipElement):
        return relationship_element_to_xml(obj)
    if isinstance(obj, model.Qualifier):
        return qualifier_to_xml(obj)
    if isinstance(obj, model.Formula):
        return formula_to_xml(obj)
    raise TypeError("Got object of class "+obj.__class__.__name__+" Expected objects from classes of aas.model. "
                                                                  "If object is part of aas.model, then check, if it "
                                                                  "has a serialization function.")


def write_aas_xml_file(file: IO,
                       data: model.AbstractObjectStore) -> None:
    """
    Write a set of AAS objects to an Asset Administration Shell XML file according to 'Details of the Asset
    Administration Shell', chapter 5.4

    todo: check the header for the file, i copied it from the example

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

    et_asset_administration_shells = ElTree.Element("assetAdministrationShells")
    for aas_obj in asset_administration_shells:
        et_asset_administration_shells.insert(0, aas_object_to_xml(aas_obj))
    et_assets = ElTree.Element("assets")
    for ass_obj in assets:
        et_assets.insert(0, aas_object_to_xml(ass_obj))
    et_submodels = ElTree.Element("submodels")
    for sub_obj in submodels:
        et_submodels.insert(0, aas_object_to_xml(sub_obj))
    et_concept_descriptions = ElTree.Element("conceptDescriptions")
    for con_obj in concept_descriptions:
        et_concept_descriptions.insert(0, aas_object_to_xml(con_obj))
    root.insert(0, et_concept_descriptions)
    root.insert(0, et_submodels)
    root.insert(0, et_assets)
    root.insert(0, et_asset_administration_shells)

    tree = ElTree.ElementTree(root)
    tree.write(file, encoding="UTF-8", xml_declaration=True, method="xml")
