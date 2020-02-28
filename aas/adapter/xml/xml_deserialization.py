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

from typing import Any, Callable, Dict, IO, List, Optional, Set, TypeVar
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

T = TypeVar('T')


def _unwrap(monad: Optional[Any]) -> Any:
    if monad is not None:
        return monad
    raise Exception(f"Unwrap failed for value {monad}!")


def _get_text_or_none(element: Optional[ElTree.Element]) -> Optional[str]:
    return element.text if element is not None else None


def _get_text_mandatory(element: Optional[ElTree.Element]) -> str:
    # unwrap value here so an exception is thrown if the element is None
    text = _get_text_or_none(_unwrap(element))
    if not text:
        # ignore type here as the "None case" cannot occur because of _unwrap()
        raise TypeError(f"XML element {element.tag} has no text!")  # type: ignore
    return text


def _objects_from_xml_elements(elements: List[ElTree.Element], constructor: Callable[[ElTree.Element, bool], T],
                               failsafe: bool) -> List[T]:
    ret: List[T] = []
    for element in elements:
        try:
            ret.append(constructor(element, failsafe))
        except (KeyError, TypeError) as e:
            error_message = "{} while converting XML element with tag {} to type {}: {}".format(
                type(e).__name__,
                element.tag,
                constructor.__name__,
                e
            )
            if failsafe:
                logger.error(error_message)
                continue
            raise type(e)(error_message)
    return ret


def _object_from_xml_element(element: ElTree.Element, constructor: Callable[[ElTree.Element, bool], T], failsafe: bool)\
        -> Optional[T]:
    objects = _objects_from_xml_elements([element], constructor, failsafe)
    return objects[0] if objects else None


def _object_from_xml_element_mandatory(parent: ElTree.Element, tag: str,
                                       constructor: Callable[[ElTree.Element, bool], T]) -> T:
    element = parent.find(tag)
    if element is None:
        raise TypeError(f"No such element {tag} found in {parent.tag}!")
    return _unwrap(_object_from_xml_element(element, constructor, False))


def construct_key(element: ElTree.Element, _failsafe: bool) -> model.Key:
    return model.Key(
        KEY_ELEMENTS_INVERSE[element.attrib["type"]],
        element.attrib["local"] == "True",
        _get_text_mandatory(element),
        KEY_TYPES_INVERSE[element.attrib["idType"]]
    )


def construct_reference(element: ElTree.Element, failsafe: bool) -> model.Reference:
    return model.Reference(
        tuple(_objects_from_xml_elements(_unwrap(element.find(NS_AAS + "keys")).findall(NS_AAS + "key"), construct_key,
                                         failsafe))
    )


def construct_administrative_information(element: ElTree.Element, _failsafe: bool) -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_text_or_none(element.find(NS_AAS + "version")),
        _get_text_or_none(element.find(NS_AAS + "revision"))
    )


def construct_lang_string_set(element: ElTree.Element, _failsafe: bool) -> model.LangStringSet:
    lss: model.LangStringSet = {}
    for lang_string in element.findall(NS_IEC + "langString"):
        lss[lang_string.attrib["lang"]] = _get_text_mandatory(lang_string)
    return lss


def construct_qualifier(element: ElTree.Element, failsafe: bool) -> model.Qualifier:
    q = model.Qualifier(
        _get_text_mandatory(element.find(NS_AAS + "type")),
        _get_text_mandatory(element.find(NS_AAS + "valueType")),
        _get_text_or_none(element.find(NS_AAS + "value"))
    )
    value_id = element.find(NS_AAS + "valueId")
    if value_id:
        q.value_id = _unwrap(_object_from_xml_element(value_id, construct_reference, failsafe))
    amend_abstract_attributes(q, element, failsafe)
    return q


def construct_formula(element: ElTree.Element, failsafe: bool) -> model.Formula:
    ref_set: Set[model.Reference] = set()

    for ref in element:
        obj = _object_from_xml_element(ref, construct_reference, failsafe)
        if not obj:
            logger.warning(f"Skipping invalid XML element with tag {ref.tag}")
            continue
        ref_set.add(obj)
    return model.Formula(ref_set)


def construct_constraint(element: ElTree.Element, failsafe: bool) -> model.Constraint:
    return {
        NS_AAS + "qualifier": construct_qualifier,
        NS_AAS + "formula": construct_formula
    }[element.tag](element, failsafe)


def construct_identification(element: ElTree.Element, _failsafe: bool) -> model.Identifier:
    return model.Identifier(
        _get_text_mandatory(element),
        IDENTIFIER_TYPES_INVERSE[element.attrib["idType"]]
    )


def construct_asset_administration_shell(element: ElTree.Element, failsafe: bool) -> model.AssetAdministrationShell:
    pass


def construct_asset(element: ElTree.Element, failsafe: bool) -> model.Asset:
    pass


def construct_submodel(element: ElTree.Element, failsafe: bool) -> model.Submodel:
    pass


def construct_concept_description(element: ElTree.Element, failsafe: bool) -> model.ConceptDescription:
    cd = model.ConceptDescription(
        _object_from_xml_element_mandatory(element, NS_AAS + "identification", construct_identification),
        set(_objects_from_xml_elements(element.findall(NS_AAS + "isCaseOf"), construct_reference, failsafe))
    )
    amend_abstract_attributes(cd, element, failsafe)
    return cd


def amend_abstract_attributes(obj: object, element: ElTree.Element, failsafe: bool) -> None:
    if isinstance(obj, model.Referable):
        if element.find(NS_AAS + "category"):
            obj.category = _get_text_or_none(element.find(NS_AAS + "category"))
        description = element.find(NS_AAS + "description")
        if description:
            obj.description = _object_from_xml_element(description, construct_lang_string_set, failsafe)
    if isinstance(obj, model.Identifiable):
        if element.find(NS_AAS + "idShort"):
            obj.id_short = _get_text_or_none(element.find(NS_AAS + "idShort"))
        administration = element.find(NS_AAS + "administration")
        if administration:
            obj.administration = _object_from_xml_element(administration, construct_administrative_information,
                                                          failsafe)
    if isinstance(obj, model.HasSemantics):
        semantic_id = element.find(NS_AAS + "semanticId")
        if semantic_id:
            obj.semantic_id = _object_from_xml_element(semantic_id, construct_reference, failsafe)
    if isinstance(obj, model.Qualifiable):
        for constraint in element:
            if constraint.tag != NS_AAS + "qualifiers":
                logger.warning(f"Skipping XML element with invalid tag {constraint.tag}")
                continue
            constraint_obj = _object_from_xml_element(constraint, construct_constraint, failsafe)
            if not constraint_obj:
                logger.warning(f"Skipping invalid XML element with tag {constraint.tag}")
                continue
            obj.qualifier.add(constraint_obj)


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
                parsed = _object_from_xml_element(element, constructor, failsafe)
                # parsed is always Identifiable, because the tag is checked earlier
                # this is just to satisfy the type checker and to make sure no error occurred while parsing
                if parsed and isinstance(parsed, model.Identifiable):
                    ret.add(parsed)
        except (KeyError, TypeError) as e:
            error_message = f"{type(e).__name__} while parsing XML List with tag {list_.tag}: {e}"
            if not failsafe:
                raise type(e)(error_message)
            logger.error(error_message)
    return ret
