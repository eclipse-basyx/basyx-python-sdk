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

from ... import model
import xml.etree.ElementTree as ElTree
import logging

from typing import Dict, IO, Optional, Set, TypeVar, Callable
from .xml_serialization import NS_AAS, NS_AAS_COMMON, NS_ABAC, NS_IEC, NS_XSI, MODELING_KIND, ASSET_KIND, KEY_ELEMENTS,\
    KEY_TYPES, IDENTIFIER_TYPES, ENTITY_TYPES, IEC61360_DATA_TYPES, IEC61360_LEVEL_TYPES

logger = logging.getLogger(__name__)

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


def _get_child_text_or_none(element: ElTree.Element, child: str) -> Optional[str]:
    optional_child = element.find(child)
    return optional_child.text if optional_child else None


T = TypeVar('T')


def object_from_xml(constructor: Callable[[ElTree.Element, bool], T], element: ElTree.Element, failsafe: bool) ->\
        Optional[T]:
    try:
        return constructor(element, failsafe)
    except(TypeError, KeyError) as e:
        error_message = "{} while converting XML Element with tag {} to type {}: {}".format(
            type(e).__name__,
            element.tag,
            constructor.__name__,
            e
        )
        if failsafe:
            logger.error(error_message)
            return None
        raise type(e)(error_message)


def construct_key(element: ElTree.Element, _failsafe: bool) -> model.Key:
    if element.text is None:
        raise TypeError("XML Key Element has no text!")
    return model.Key(
        KEY_ELEMENTS_INVERSE[element.attrib["type"]],
        element.attrib["local"] == "True",
        element.text,
        KEY_TYPES_INVERSE[element.attrib["idType"]]
    )


def construct_reference(element: ElTree.Element, failsafe: bool) -> model.Reference:
    return model.Reference(
        tuple(key for key in [object_from_xml(construct_key, el, failsafe) for el in element.find("keys") or []]
              if key is not None)
    )


def construct_administrative_information(element: ElTree.Element, _failsafe: bool) -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_child_text_or_none(element, NS_AAS + "version"),
        _get_child_text_or_none(element, NS_AAS + "revision")
    )


def construct_lang_string_set(element: ElTree.Element, _failsafe: bool) -> model.LangStringSet:
    lss: model.LangStringSet = {}
    for lang_string in element:
        if lang_string.tag != NS_IEC + "langString" or not lang_string.attrib["lang"] or lang_string.text is None:
            logger.warning(f"Skipping invalid XML Element with tag {lang_string.tag}")
            continue
        lss[lang_string.attrib["lang"]] = lang_string.text
    return lss


def construct_qualifier(element: ElTree.Element, failsafe: bool) -> model.Qualifier:
    type_ = _get_child_text_or_none(element, "type")
    value_type = _get_child_text_or_none(element, "valueType")
    if not type_ or not value_type:
        raise TypeError("XML Qualifier Element has no type or valueType")
    q = model.Qualifier(
        type_,
        value_type,
        _get_child_text_or_none(element, "value")
    )
    value_id = element.find("valueId")
    if value_id:
        value_id_obj = object_from_xml(
            construct_reference,
            value_id,
            failsafe
        )
        if value_id_obj:
            q.value_id = value_id_obj
    amend_abstract_attributes(q, element, failsafe)
    return q


def construct_formula(element: ElTree.Element, failsafe: bool) -> model.Formula:
    ref_set: Set[model.Reference] = set()
    for ref in element:
        obj = object_from_xml(construct_reference, ref, failsafe)
        if not obj:
            logger.warning(f"Skipping invalid XML Element with tag {ref.tag}")
            continue
        ref_set.add(obj)
    return model.Formula(ref_set)


def construct_constraint(element: ElTree.Element, failsafe: bool) -> model.Constraint:
    if element.tag == NS_AAS + "qualifier":
        return construct_qualifier(element, failsafe)
    if element.tag == NS_AAS + "formula":
        return construct_formula(element, failsafe)
    raise TypeError("Given element is neither a qualifier nor a formula!")


def amend_abstract_attributes(obj: object, element: ElTree.Element, failsafe: bool) -> None:
    if isinstance(obj, model.Referable):
        if element.find(NS_AAS + "category"):
            obj.category = _get_child_text_or_none(element, NS_AAS + "category")
        description = element.find(NS_AAS + "description")
        if description:
            obj.description = object_from_xml(
                construct_lang_string_set,
                description,
                failsafe
            )
    if isinstance(obj, model.Identifiable):
        if element.find(NS_AAS + "idShort"):
            obj.id_short = _get_child_text_or_none(element, NS_AAS + "idShort")
        administration = element.find(NS_AAS + "administration")
        if administration:
            obj.administration = object_from_xml(
                construct_administrative_information,
                administration,
                failsafe
            )
    if isinstance(obj, model.HasSemantics):
        semantic_id = element.find(NS_AAS + "semanticId")
        if semantic_id:
            obj.semantic_id = object_from_xml(
                construct_reference,
                semantic_id,
                failsafe
            )
    if isinstance(obj, model.Qualifiable):
        for constraint in element:
            if constraint.tag != NS_AAS + "qualifiers":
                logger.warning(f"Skipping XML Element with invalid tag {constraint.tag}")
                continue
            constraint_obj = object_from_xml(
                construct_constraint,
                constraint,
                failsafe
            )
            if not constraint_obj:
                logger.warning(f"Skipping invalid XML Element with tag {constraint.tag}")
                continue
            obj.qualifier.add(constraint_obj)


def construct_asset_administration_shell(element: ElTree.Element, failsafe: bool) -> model.AssetAdministrationShell:
    pass


def construct_asset(element: ElTree.Element, failsafe: bool) -> model.Asset:
    pass


def construct_submodel(element: ElTree.Element, failsafe: bool) -> model.Submodel:
    pass


def construct_concept_description(element: ElTree.Element, failsafe: bool) -> model.ConceptDescription:
    pass


def read_xml_aas_file(file: IO, failsafe: bool = True) -> model.DictObjectStore:
    """
    Read an Asset Administration Shell XML file according to 'Details of the Asset Administration Shell', chapter 5.4

    :param file: A file-like object to read the XML-serialized data from
    :param failsafe: If True, the file is parsed in a failsafe way: Instead of raising an Exception for missing
                     attributes and wrong types, errors are logged and defective objects are skipped
    :return: A DictObjectStore containing all AAS objects from the XML file
    """

    tag_parser_map = {
        NS_AAS + "assetAdministrationShell": construct_asset_administration_shell,
        NS_AAS + "asset": construct_asset,
        NS_AAS + "submodel": construct_submodel,
        NS_AAS + "conceptDescription": construct_concept_description
    }

    tree = ElTree.parse(file)
    root = tree.getroot()

    # Add AAS objects to ObjectStore
    ret: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    for list_ in root:
        try:
            if list_.tag[-1] != "s":
                raise TypeError(f"Unexpected list {list_.tag}")
            constructor = tag_parser_map[list_.tag[:-1]]
            for element in list_:
                if element.tag not in tag_parser_map.keys():
                    error_message = f"Unexpected element {element.tag} in list {list_.tag}"
                    if failsafe:
                        logger.warning(error_message)
                    else:
                        raise TypeError(error_message)
                parsed = object_from_xml(constructor, element, failsafe)
                # parsed is always Identifiable, because the tag is checked earlier
                # this is just to satisfy the typechecker and to make sure no error occured while parsing
                if parsed and isinstance(parsed, model.Identifiable):
                    ret.add(parsed)
        except (KeyError, TypeError) as e:
            error_message = f"{type(e).__name__} while parsing XML List with tag {list_.tag}: {e}"
            if not failsafe:
                raise type(e)(error_message)
            logger.error(error_message)
    return ret
