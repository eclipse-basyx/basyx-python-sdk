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

from typing import Any, Callable, Dict, IO, Iterable, List, Optional, Set, Tuple, Type, TypeVar
from .xml_serialization import NS_AAS, NS_AAS_COMMON, NS_ABAC, NS_IEC, NS_XSI
from .._generic import MODELING_KIND_INVERSE, ASSET_KIND_INVERSE, KEY_ELEMENTS_INVERSE, KEY_TYPES_INVERSE,\
    IDENTIFIER_TYPES_INVERSE, ENTITY_TYPES_INVERSE, IEC61360_DATA_TYPES_INVERSE, IEC61360_LEVEL_TYPES_INVERSE,\
    KEY_ELEMENTS_CLASSES_INVERSE

logger = logging.getLogger(__name__)

T = TypeVar('T')


def _get_child_mandatory(element: ElTree.Element, child_tag: str) -> ElTree.Element:
    child = element.find(child_tag)
    if child is None:
        raise KeyError(f"XML element {element.tag} has no child {child_tag}!")
    return child


def _get_attrib_mandatory(element: ElTree.Element, attrib: str) -> str:
    if attrib not in element.attrib:
        raise KeyError(f"XML element {element.tag} has no attribute with name {attrib}!")
    return element.attrib[attrib]


def _get_attrib_mandatory_mapped(element: ElTree.Element, attrib: str, dct: Dict[str, T]) -> T:
    attrib_value = _get_attrib_mandatory(element, attrib)
    if attrib_value not in dct:
        raise ValueError(f"Attribute {attrib} of XML element {element.tag} has invalid value: {attrib_value}")
    return dct[attrib_value]


def _get_text_or_none(element: Optional[ElTree.Element]) -> Optional[str]:
    return element.text if element is not None else None


def _get_text_mandatory(element: ElTree.Element) -> str:
    text = element.text
    if text is None:
        raise KeyError(f"XML element {element.tag} has no text!")
    return text


def _get_text_mandatory_mapped(element: ElTree.Element, dct: Dict[str, T]) -> T:
    text = _get_text_mandatory(element)
    if text not in dct:
        raise ValueError(f"Text of XML element {element.tag} is invalid: {text}")
    return dct[text]


def _constructor_name_to_typename(constructor: Callable[[ElTree.Element, bool], T]) -> str:
    return "".join([s[0].upper() + s[1:] for s in constructor.__name__.split("_")[2:]])


def _exception_to_str(exception: BaseException) -> str:
    string = str(exception)
    return string[1:-1] if isinstance(exception, KeyError) else string


def _failsafe_construct(element: Optional[ElTree.Element], constructor: Callable[..., T], failsafe: bool,
                        **kwargs: Any) -> Optional[T]:
    if element is None:
        return None
    try:
        return constructor(element, failsafe, **kwargs)
    except (KeyError, ValueError) as e:
        error_message = f"while converting XML element with tag {element.tag} to "\
                        f"type {_constructor_name_to_typename(constructor)}"
        if not failsafe:
            raise type(e)(error_message) from e
        error_type = type(e).__name__
        cause: Optional[BaseException] = e
        while cause is not None:
            error_message = _exception_to_str(cause) + "\n -> " + error_message
            cause = cause.__cause__
        logger.error(error_type + ": " + error_message)
        logger.error(f"Failed to construct {_constructor_name_to_typename(constructor)}!")
        return None


def _failsafe_construct_multiple(elements: Iterable[ElTree.Element], constructor: Callable[..., T], failsafe: bool,
                                 **kwargs: Any) -> Iterable[T]:
    for element in elements:
        parsed = _failsafe_construct(element, constructor, failsafe, **kwargs)
        if parsed is not None:
            yield parsed


def _find_and_construct_mandatory(element: ElTree.Element, child_tag: str, constructor: Callable[..., T],
                                  **kwargs: Any) -> T:
    constructed = _failsafe_construct(_get_child_mandatory(element, child_tag), constructor, False, **kwargs)
    if constructed is None:
        raise TypeError("The result of a non-failsafe _failsafe_construct() call was None! "
                        "This is a bug in the pyAAS XML deserialization, please report it!")
    return constructed


def _construct_key(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Key:
    return model.Key(
        _get_attrib_mandatory_mapped(element, "type", KEY_ELEMENTS_INVERSE),
        _get_attrib_mandatory(element, "local").lower() == "true",
        _get_text_mandatory(element),
        _get_attrib_mandatory_mapped(element, "idType", KEY_TYPES_INVERSE)
    )


def _construct_key_tuple(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> Tuple[model.Key, ...]:
    keys = _get_child_mandatory(element, NS_AAS + "keys")
    return tuple(_failsafe_construct_multiple(keys.findall(NS_AAS + "key"), _construct_key, failsafe))


def _construct_reference(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Reference:
    return model.Reference(_construct_key_tuple(element, failsafe))


def _construct_aas_reference(element: ElTree.Element, failsafe: bool, type_: Type[model.base._RT], **_kwargs: Any)\
        -> model.AASReference[model.base._RT]:
    keys = _construct_key_tuple(element, failsafe)
    if len(keys) != 0 and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type, type(None)), type_):
        logger.warning(f"Type {keys[-1].type.name} of last key of reference to {' / '.join(str(k) for k in keys)} "
                       f"does not match reference type {type_.__name__}")
    return model.AASReference(keys, type_)


def _construct_submodel_reference(element: ElTree.Element, failsafe: bool, **kwargs: Any)\
        -> model.AASReference[model.Submodel]:
    return _construct_aas_reference(element, failsafe, model.Submodel, **kwargs)


def _construct_asset_reference(element: ElTree.Element, failsafe: bool, **kwargs: Any)\
        -> model.AASReference[model.Asset]:
    return _construct_aas_reference(element, failsafe, model.Asset, **kwargs)


def _construct_asset_administration_shell_reference(element: ElTree.Element, failsafe: bool, **kwargs: Any)\
        -> model.AASReference[model.AssetAdministrationShell]:
    return _construct_aas_reference(element, failsafe, model.AssetAdministrationShell, **kwargs)


def _construct_referable_reference(element: ElTree.Element, failsafe: bool, **kwargs: Any)\
        -> model.AASReference[model.Referable]:
    return _construct_aas_reference(element, failsafe, model.Referable, **kwargs)


def _construct_concept_description_reference(element: ElTree.Element, failsafe: bool, **kwargs: Any)\
        -> model.AASReference[model.ConceptDescription]:
    return _construct_aas_reference(element, failsafe, model.ConceptDescription, **kwargs)


def _construct_administrative_information(element: ElTree.Element, _failsafe: bool, **_kwargs: Any)\
        -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_text_or_none(element.find(NS_AAS + "version")),
        _get_text_or_none(element.find(NS_AAS + "revision"))
    )


def _construct_lang_string_set(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.LangStringSet:
    lss: model.LangStringSet = {}
    for lang_string in element.findall(NS_IEC + "langString"):
        lss[_get_attrib_mandatory(lang_string, "lang")] = _get_text_mandatory(lang_string)
    return lss


def _construct_qualifier(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Qualifier:
    q = model.Qualifier(
        _get_text_mandatory(_get_child_mandatory(element, NS_AAS + "type")),
        _get_text_mandatory_mapped(_get_child_mandatory(element, NS_AAS + "valueType"),
                                   model.datatypes.XSD_TYPE_CLASSES)
    )
    value = element.find(NS_AAS + "value")
    if value is not None:
        q.value = value.text
    value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), _construct_reference, failsafe)
    if value_id is not None:
        q.value_id = value_id
    _amend_abstract_attributes(q, element, failsafe)
    return q


def _construct_formula(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Formula:
    ref_set: Set[model.Reference] = set()
    depends_on_refs = element.find(NS_AAS + "dependsOnRefs")
    if depends_on_refs is not None:
        ref_set = set(_failsafe_construct_multiple(depends_on_refs.findall(NS_AAS + "reference"), _construct_reference,
                                                   failsafe))
    return model.Formula(ref_set)


def _construct_constraint(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Constraint:
    return {
        NS_AAS + "qualifier": _construct_qualifier,
        NS_AAS + "formula": _construct_formula
    }[element.tag](element, failsafe)


def _construct_identifier(element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Identifier:
    return model.Identifier(
        _get_text_mandatory(element),
        _get_attrib_mandatory_mapped(element, "idType", IDENTIFIER_TYPES_INVERSE)
    )


def _construct_security(_element: ElTree.Element, _failsafe: bool, **_kwargs: Any) -> model.Security:
    return model.Security()


def _construct_view(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.View:
    view = model.View(_get_text_mandatory(_get_child_mandatory(element, NS_AAS + "idShort")))
    contained_elements = element.find(NS_AAS + "containedElements")
    if contained_elements is not None:
        view.contained_element = set(
            _failsafe_construct_multiple(contained_elements.findall(NS_AAS + "containedElementRef"),
                                         _construct_referable_reference, failsafe)
        )
    _amend_abstract_attributes(view, element, failsafe)
    return view


def _construct_concept_dictionary(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDictionary:
    cd = model.ConceptDictionary(_get_text_mandatory(_get_child_mandatory(element, NS_AAS + "idShort")))
    concept_description = element.find(NS_AAS + "conceptDescriptionRefs")
    if concept_description is not None:
        cd.concept_description = set(_failsafe_construct_multiple(
            concept_description.findall(NS_AAS + "conceptDescriptionRef"),
            _construct_concept_description_reference,
            failsafe
        ))
    _amend_abstract_attributes(cd, element, failsafe)
    return cd


def _construct_asset_administration_shell(element: ElTree.Element, failsafe: bool, **_kwargs: Any)\
        -> model.AssetAdministrationShell:
    aas = model.AssetAdministrationShell(
        _find_and_construct_mandatory(element, NS_AAS + "assetRef", _construct_asset_reference),
        _find_and_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    security = _failsafe_construct(element.find(NS_ABAC + "security"), _construct_security, failsafe)
    if security is not None:
        aas.security = security
    submodels = element.find(NS_AAS + "submodelRefs")
    if submodels is not None:
        aas.submodel = set(_failsafe_construct_multiple(submodels.findall(NS_AAS + "submodelRef"),
                                                        _construct_submodel_reference, failsafe))
    views = element.find(NS_AAS + "views")
    if views is not None:
        for view in _failsafe_construct_multiple(views.findall(NS_AAS + "view"), _construct_view, failsafe):
            aas.view.add(view)
    concept_dictionaries = element.find(NS_AAS + "conceptDictionaries")
    if concept_dictionaries is not None:
        for cd in _failsafe_construct_multiple(concept_dictionaries.findall(NS_AAS + "conceptDictionary"),
                                               _construct_concept_dictionary, failsafe):
            aas.concept_dictionary.add(cd)
    derived_from = _failsafe_construct(element.find(NS_AAS + "derivedFrom"),
                                       _construct_asset_administration_shell_reference, failsafe)
    if derived_from is not None:
        aas.derived_from = derived_from
    _amend_abstract_attributes(aas, element, failsafe)
    return aas


def _construct_asset(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Asset:
    asset = model.Asset(
        _get_text_mandatory_mapped(_get_child_mandatory(element, NS_AAS + "kind"), ASSET_KIND_INVERSE),
        _find_and_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    asset.asset_identification_model = _failsafe_construct(element.find(NS_AAS + "assetIdentificationModelRef"),
                                                           _construct_submodel_reference, failsafe)
    asset.bill_of_material = _failsafe_construct(element.find(NS_AAS + "billOfMaterialRef"),
                                                 _construct_submodel_reference, failsafe)
    _amend_abstract_attributes(asset, element, failsafe)
    return asset


def _construct_submodel(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.Submodel:
    pass


def _construct_concept_description(element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDescription:
    cd = model.ConceptDescription(
        _find_and_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    is_case_of = set(_failsafe_construct_multiple(element.findall(NS_AAS + "isCaseOf"), _construct_reference, failsafe))
    if len(is_case_of) != 0:
        cd.is_case_of = is_case_of
    _amend_abstract_attributes(cd, element, failsafe)
    return cd


def _amend_abstract_attributes(obj: object, element: ElTree.Element, failsafe: bool, **_kwargs: Any) -> None:
    if isinstance(obj, model.Referable):
        category = _get_text_or_none(element.find(NS_AAS + "category"))
        if category is not None:
            obj.category = category
        description = _failsafe_construct(element.find(NS_AAS + "description"), _construct_lang_string_set, failsafe)
        if description is not None:
            obj.description = description
    if isinstance(obj, model.Identifiable):
        id_short = _get_text_or_none(element.find(NS_AAS + "idShort"))
        if id_short is not None:
            obj.id_short = id_short
        administration = _failsafe_construct(element.find(NS_AAS + "administration"),
                                             _construct_administrative_information, failsafe)
        if administration:
            obj.administration = administration
    if isinstance(obj, model.HasSemantics):
        semantic_id = _failsafe_construct(element.find(NS_AAS + "semanticId"), _construct_reference, failsafe)
        if semantic_id is not None:
            obj.semantic_id = semantic_id
    if isinstance(obj, model.Qualifiable):
        for constraint in _failsafe_construct_multiple(element.findall(NS_AAS + "qualifiers"), _construct_constraint,
                                                       failsafe):
            obj.qualifier.add(constraint)


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
        for element in _failsafe_construct_multiple(list_.findall(element_tag), constructor, failsafe):
            # element is always Identifiable, because the tag is checked earlier
            # this is just to satisfy the type checker
            if isinstance(element, model.Identifiable):
                ret.add(element)
    return ret
