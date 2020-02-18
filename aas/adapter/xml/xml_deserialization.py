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
Module for deserializing Asset Administration Shell data from the official XML format
"""

# TODO: add more constructors
# TODO: implement error handling / failsafe parsing
# TODO: add better (more useful) helper functions

from ... import model
import xml.etree.ElementTree as ElTree

from typing import Dict, IO, Optional
from .xml_serialization import NS_AAS, NS_AAS_COMMON, NS_ABAC, NS_IEC, NS_XSI, MODELING_KIND, ASSET_KIND, KEY_ELEMENTS,\
    KEY_TYPES, IDENTIFIER_TYPES, ENTITY_TYPES, IEC61360_DATA_TYPES, IEC61360_LEVEL_TYPES

MODELING_KIND_INVERSE: Dict[str, model.ModelingKind] = {v: k for k, v in MODELING_KIND.items()}
ASSET_KIND_INVERSE: Dict[str, model.AssetKind] = {v: k for k, v in ASSET_KIND.items()}
KEY_ELEMENTS_INVERSE: Dict[str, model.KeyElements] = {v: k for k, v in KEY_ELEMENTS.items()}
KEY_TYPES_INVERSE: Dict[str, model.KeyType] = {v: k for k, v in KEY_TYPES.items()}
IDENTIFIER_TYPES_INVERSE: Dict[str, model.IdentifierType] = {v: k for k, v in IDENTIFIER_TYPES.items()}
ENTITY_TYPES_INVERSE: Dict[str, model.EntityType] = {v: k for k, v in ENTITY_TYPES.items()}
KEY_ELEMENTS_CLASSES_INVERSE: Dict[model.KeyElements, type] = {v: k for k, v in model.KEY_ELEMENTS_CLASSES.items()}
IEC61360_DATA_TYPES_INVERSE: Dict[str, model.concept.IEC61360DataType] = {v: k for k, v in IEC61360_DATA_TYPES.items()}
IEC61360_LEVEL_TYPES_INVERSE: Dict[str, model.concept.IEC61360LevelType] = \
    {v: k for k, v in IEC61360_LEVEL_TYPES.items()}


def _get_text_or_none(_dict: Dict[str, ElTree.Element], key: str) -> Optional[str]:
    return _dict[key].text if key in _dict else None


def construct_key(element: ElTree.Element) -> model.Key:
    return model.Key(
        KEY_ELEMENTS_INVERSE[element.attrib["type"]],
        element.attrib["local"] == "True",
        element.text,
        KEY_TYPES_INVERSE[element.attrib["idType"]]
    )


def construct_reference(element: ElTree.Element) -> model.Reference:
    return model.Reference(
        [construct_key(k) for k in element["keys"]]
    )


def construct_administrative_information(element: ElTree.Element) -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_text_or_none(element, NS_AAS + "version"),
        _get_text_or_none(element, NS_AAS + "revision")
    )


def construct_lang_string_set(element: ElTree.Element) -> model.LangStringSet:
    lss = model.LangStringSet
    for lang_string in element:
        if lang_string.tag != NS_IEC + "langString" or not lang_string.attrib["lang"]:
            continue
        lss[lang_string.attrib["lang"]] = lang_string.text
    return lss


def construct_qualifier(element: ElTree.Element) -> model.Qualifier:
    q = model.Qualifier(
        _get_text_or_none(element, "type"),
        _get_text_or_none(element, "valueType"),
        _get_text_or_none(element, "value"),
        construct_reference(element["valueId"])
    )
    amend_abstract_attributes(q, element)
    return q


def construct_formula(element: ElTree.Element) -> model.Formula:
    return model.Formula(
        set(construct_reference(ref) for ref in element)
    )


def construct_constraint(element: ElTree.Element) -> model.Constraint:
    if element.tag == NS_AAS + "qualifier":
        return construct_qualifier(element)
    if element.tag == NS_AAS + "formula":
        return construct_formula(element)
    raise TypeError("Given element is neither a qualifier nor a formula!")


def amend_abstract_attributes(obj: object, element: ElTree.Element) -> None:
    if isinstance(obj, model.Referable):
        if NS_AAS + "category" in element:
            obj.category = element[NS_AAS + "category"].text
        if NS_AAS + "description" in element:
            obj.description = construct_lang_string_set(element[NS_AAS + "description"])
    if isinstance(obj, model.Identifiable):
        if NS_AAS + "idShort" in element:
            obj.id_short = element[NS_AAS + "idShort"].text
        if NS_AAS + "administration" in element:
            obj.administration = construct_administrative_information(element[NS_AAS + "administration"])
    if isinstance(obj, model.HasSemantics):
        if NS_AAS + "semanticId" in element:
            obj.semantic_id = construct_reference(element[NS_AAS + "semanticId"])
    if isinstance(obj, model.Qualifiable):
        if NS_AAS + "qualifiers" in element:
            for constraint in element[NS_AAS + "qualifiers"]:
                obj.qualifier.add(construct_constraint(constraint))


def read_xml_aas_file(file: IO, failsafe: bool = True) -> model.DictObjectStore:
    """
    Read an Asset Administration Shell XML file according to 'Details of the Asset Administration Shell', chapter 5.4

    :param file: A file-like object to read the XML-serialized data from
    :param failsafe: If True, the file is parsed in a failsafe way: Instead of raising an Exception for missing
                     attributes and wrong types, errors are logged and defective objects are skipped
    :return: A DictObjectStore containing all AAS objects from the XML file
    """


