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

# TODO: add constructor for submodel + all classes required by submodel

from ... import model
import xml.etree.ElementTree as ElTree
import logging

from typing import Any, Callable, Dict, IO, Iterable, Optional, Set, Tuple, Type, TypeVar
from .xml_serialization import NS_AAS, NS_AAS_COMMON, NS_ABAC, NS_IEC, NS_XSI
from .._generic import MODELING_KIND, ASSET_KIND, KEY_ELEMENTS,\
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


def _unwrap(monad: Optional[T]) -> T:
    if monad is not None:
        return monad
    raise TypeError(f"Unwrap failed for value {monad}!")


def _constructor_name_to_typename(constructor: Callable[[ElTree.Element, bool], T]) -> str:
    return "".join([s[0].upper() + s[1:] for s in constructor.__name__.split("_")[2:]])


def _get_text_or_none(element: Optional[ElTree.Element]) -> Optional[str]:
    return element.text if element is not None else None


def _get_text_mandatory(element: Optional[ElTree.Element]) -> str:
    # unwrap value here so a TypeError is thrown if the element is None
    element_unwrapped = _unwrap(element)
    text = _get_text_or_none(element_unwrapped)
    if text is None:
        raise TypeError(f"XML element {element_unwrapped.tag} has no text!")
    return text


def _objects_from_xml_elements(elements: Iterable[ElTree.Element], constructor: Callable[..., T],
                               failsafe: bool, **kwargs: Any) -> Iterable[T]:
    for element in elements:
        parsed = _object_from_xml_element(element, constructor, failsafe, **kwargs)
        if parsed is not None:
            yield parsed


def _object_from_xml_element(element: Optional[ElTree.Element], constructor: Callable[..., T],
                             failsafe: bool, **kwargs: Any) -> Optional[T]:
    if element is None:
        return None
    try:
        return constructor(element, failsafe, **kwargs)
    except (KeyError, TypeError) as e:
        error_message = f"{type(e).__name__} while converting XML element with tag {element.tag} to " \
                        f"type {_constructor_name_to_typename(constructor)}: {e}"
        if not failsafe:
            raise type(e)(error_message) from e
        logger.error(error_message)
        return None


def _object_from_xml_element_mandatory(parent: ElTree.Element, tag: str,
                                       constructor: Callable[..., T], **kwargs: Any) -> T:
    element = parent.find(tag)
    if element is None:
        raise KeyError(f"No such element {tag} found in {parent.tag}!")
    return _unwrap(_object_from_xml_element(element, constructor, False, **kwargs))


def _construct_key(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Key:
    return model.Key(
        KEY_ELEMENTS_INVERSE[element.attrib["type"]],
        element.attrib["local"] == "True",
        _get_text_mandatory(element),
        KEY_TYPES_INVERSE[element.attrib["idType"]]
    )


def _construct_key_tuple(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> Tuple[model.Key, ...]:
    return tuple(_objects_from_xml_elements(_unwrap(element.find(NS_AAS + "keys")).findall(NS_AAS + "key"),
                                            _construct_key, failsafe))


def _construct_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Reference:
    return model.Reference(_construct_key_tuple(element, failsafe))


def _construct_submodel_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AASReference[model.Submodel]:
    return model.AASReference(_construct_key_tuple(element, failsafe), model.Submodel)


def _construct_asset_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AASReference[model.Asset]:
    return model.AASReference(_construct_key_tuple(element, failsafe), model.Asset)


def _construct_asset_administration_shell_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AASReference[model.AssetAdministrationShell]:
    return model.AASReference(_construct_key_tuple(element, failsafe), model.AssetAdministrationShell)


def _construct_referable_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AASReference[model.Referable]:
    return model.AASReference(_construct_key_tuple(element, failsafe), model.Referable)


def _construct_concept_description_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AASReference[model.ConceptDescription]:
    return model.AASReference(_construct_key_tuple(element, failsafe), model.ConceptDescription)


def _construct_administrative_information(element: ElTree.Element, _failsafe: bool, **_kwargs: Any)\
        -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_text_or_none(element.find(NS_AAS + "version")),
        _get_text_or_none(element.find(NS_AAS + "revision"))
    )


def _construct_lang_string_set(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.LangStringSet:
    lss: model.LangStringSet = {}
    for lang_string in element.findall(NS_IEC + "langString"):
        lss[lang_string.attrib["lang"]] = _get_text_mandatory(lang_string)
    return lss


def _construct_qualifier(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Qualifier:
    q = model.Qualifier(
        _get_text_mandatory(element.find(NS_AAS + "type")),
        model.datatypes.XSD_TYPE_CLASSES[_get_text_mandatory(element.find(NS_AAS + "valueType"))],
        _get_text_or_none(element.find(NS_AAS + "value"))
    )
    value_id = _object_from_xml_element(element.find(NS_AAS + "valueId"), _construct_reference, failsafe)
    if value_id is not None:
        q.value_id = value_id
    _amend_abstract_attributes(q, element, failsafe)
    return q


def _construct_formula(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Formula:
    ref_set: Set[model.Reference] = set()
    for ref in element:
        obj = _object_from_xml_element(ref, _construct_reference, failsafe)
        if not obj:
            logger.warning(f"Skipping invalid XML element with tag {ref.tag}")
            continue
        ref_set.add(obj)
    return model.Formula(ref_set)


def _construct_constraint(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Constraint:
    return {
        NS_AAS + "qualifier": _construct_qualifier,
        NS_AAS + "formula": _construct_formula
    }[element.tag](element, failsafe)


def _construct_identifier(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Identifier:
    return model.Identifier(
        _get_text_mandatory(element),
        IDENTIFIER_TYPES_INVERSE[element.attrib["idType"]]
    )


def _construct_security(_element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Security:
    return model.Security()


def _construct_view(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.View:
    view = model.View(_get_text_mandatory(element.find(NS_AAS + "idShort")))
    contained_elements = element.find(NS_AAS + "containedElements")
    if contained_elements is not None:
        view.contained_element = set(
            _objects_from_xml_elements(contained_elements.findall(NS_AAS + "containedElementRef"),
                                       _construct_referable_reference, failsafe)
        )
    _amend_abstract_attributes(view, element, failsafe)
    return view


def _construct_concept_dictionary(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDictionary:
    cd = model.ConceptDictionary(_get_text_mandatory(element.find(NS_AAS + "idShort")))
    concept_description = element.find(NS_AAS + "conceptDescriptionRefs")
    if concept_description is not None:
        cd.concept_description = set(_objects_from_xml_elements(
            concept_description.findall(NS_AAS + "conceptDescriptionRef"),
            _construct_concept_description_reference,
            failsafe
        ))
    _amend_abstract_attributes(cd, element, failsafe)
    return cd


def _construct_asset_administration_shell(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AssetAdministrationShell:
    aas = model.AssetAdministrationShell(
        _object_from_xml_element_mandatory(element, NS_AAS + "assetRef", _construct_asset_reference),
        _object_from_xml_element_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    aas.security = _object_from_xml_element(element.find(NS_ABAC + "security"), _construct_security, failsafe)
    submodels = element.find(NS_AAS + "submodelRefs")
    if submodels is not None:
        aas.submodel = set(_objects_from_xml_elements(submodels.findall(NS_AAS + "submodelRef"),
                                                      _construct_submodel_reference, failsafe))
    views = element.find(NS_AAS + "views")
    if views is not None:
        for view in _objects_from_xml_elements(views.findall(NS_AAS + "view"), _construct_view, failsafe):
            aas.view.add(view)
    concept_dictionaries = element.find(NS_AAS + "conceptDictionaries")
    if concept_dictionaries is not None:
        for cd in _objects_from_xml_elements(concept_dictionaries.findall(NS_AAS + "conceptDictionary"),
                                             _construct_concept_dictionary, failsafe):
            aas.concept_dictionary.add(cd)
    derived_from = element.find(NS_AAS + "derivedFrom")
    if derived_from is not None:
        aas.derived_from = _object_from_xml_element(element, _construct_asset_administration_shell_reference, failsafe)
    _amend_abstract_attributes(aas, element, failsafe)
    return aas


def _construct_asset(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Asset:
    asset = model.Asset(
        ASSET_KIND_INVERSE[_get_text_mandatory(element.find(NS_AAS + "kind"))],
        _object_from_xml_element_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    asset.asset_identification_model = _object_from_xml_element(element.find(NS_AAS + "assetIdentificationModelRef"),
                                                                _construct_submodel_reference, failsafe)
    asset.bill_of_material = _object_from_xml_element(element.find(NS_AAS + "billOfMaterialRef"),
                                                      _construct_submodel_reference, failsafe)
    _amend_abstract_attributes(asset, element, failsafe)
    return asset


def _construct_submodel(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Submodel:
    pass


def _construct_concept_description(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDescription:
    cd = model.ConceptDescription(
        _object_from_xml_element_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    is_case_of = set(_objects_from_xml_elements(element.findall(NS_AAS + "isCaseOf"), _construct_reference, failsafe))
    if len(is_case_of) != 0:
        cd.is_case_of = is_case_of
    _amend_abstract_attributes(cd, element, failsafe)
    return cd


def _amend_abstract_attributes(obj: object, element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> None:
    if isinstance(obj, model.Referable):
        category = element.find(NS_AAS + "category")
        if category:
            obj.category = _get_text_or_none(category)
        description = element.find(NS_AAS + "description")
        if description:
            obj.description = _object_from_xml_element(description, _construct_lang_string_set, failsafe)
    if isinstance(obj, model.Identifiable):
        id_short = element.find(NS_AAS + "idShort")
        if id_short:
            obj.id_short = _get_text_or_none(id_short)
        administration = element.find(NS_AAS + "administration")
        if administration:
            obj.administration = _object_from_xml_element(administration, _construct_administrative_information,
                                                          failsafe)
    if isinstance(obj, model.HasSemantics):
        semantic_id = element.find(NS_AAS + "semanticId")
        if semantic_id:
            obj.semantic_id = _object_from_xml_element(semantic_id, _construct_reference, failsafe)
    if isinstance(obj, model.Qualifiable):
        for constraint in element:
            if constraint.tag != NS_AAS + "qualifiers":
                logger.warning(f"Skipping XML element with invalid tag {constraint.tag}")
                continue
            constraint_obj = _object_from_xml_element(constraint, _construct_constraint, failsafe)
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

    element_constructors = {
        NS_AAS + "assetAdministrationShell": _construct_asset_administration_shell,
        NS_AAS + "asset": _construct_asset,
        NS_AAS + "submodel": _construct_submodel,
        NS_AAS + "conceptDescription": _construct_concept_description
    }

    tree = ElTree.parse(file)
    root = tree.getroot()

    # Add AAS objects to ObjectStore
    ret: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    for list_ in root:
        element_tag = list_.tag[:-1]
        if list_.tag[-1] != "s" or element_tag not in element_constructors.keys():
            raise TypeError(f"Unexpected list {list_.tag}")
        constructor = element_constructors[element_tag]
        for element in _objects_from_xml_elements(list_.findall(element_tag), constructor, failsafe):
            # element is always Identifiable, because the tag is checked earlier
            # this is just to satisfy the type checker
            if isinstance(element, model.Identifiable):
                ret.add(element)
    return ret
