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

Use this module by calling read_xml_aas_file(file, failsafe).
The function returns a DictObjectStore containing all parsed elements.

Unlike the JSON deserialization, parsing is done top-down. Elements with a specific tag are searched on the level
directly below the level of the current xml element (in terms of parent and child relation) and parsed when
found. Constructor functions of these elements will then again search for mandatory and optional child elements
and construct them if available, and so on.

This module supports parsing in failsafe and non-failsafe mode.
In failsafe mode errors regarding missing attributes and elements or invalid values are caught and logged.
In non-failsafe mode any error would abort parsing.
Error handling is done only by _failsafe_construct() in this module. Nearly all constructor functions are called
by other constructor functions via _failsafe_construct(), so an error chain is constructed in the error case,
which allows printing stacktrace-like error messages like the following in the error case (in failsafe mode of course):

KeyError: aas:identification on line 252 has no attribute with name idType!
 -> Failed to convert aas:identification on line 252 to type Identifier!
 -> Failed to convert aas:conceptDescription on line 247 to type ConceptDescription!
"""

from ... import model
from lxml import etree  # type: ignore
import logging
import base64

from typing import Any, Callable, Dict, IO, Iterable, Optional, Tuple, Type, TypeVar
from mypy_extensions import TypedDict  # TODO: import this from typing should we require python 3.8+ at some point
from .xml_serialization import NS_AAS, NS_ABAC, NS_IEC
from .._generic import MODELING_KIND_INVERSE, ASSET_KIND_INVERSE, KEY_ELEMENTS_INVERSE, KEY_TYPES_INVERSE, \
    IDENTIFIER_TYPES_INVERSE, ENTITY_TYPES_INVERSE, KEY_ELEMENTS_CLASSES_INVERSE

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _str_to_bool(string: str) -> bool:
    """
    XML only allows "false" and "true" (case-sensitive) as valid values for a boolean.

    This function checks the string and raises a ValueError if the string is neither "true" nor "false".

    :param string: String representation of a boolean. ("true" or "false")
    :return: The respective boolean value.
    :raises ValueError: If string is neither "true" nor "false".
    """
    if string not in ("true", "false"):
        raise ValueError(f"{string} is not a valid boolean! Only true and false are allowed.")
    return string == "true"


def _tag_replace_namespace(tag: str, nsmap: Dict[str, str]) -> str:
    """
    Attempts to replace the namespace in front of a tag with the prefix used in the xml document.

    :param tag: The tag of an xml element.
    :param nsmap: A dict mapping prefixes to namespaces.
    :return: The modified element tag. If the namespace wasn't found in nsmap, the unmodified tag is returned.
    """
    split = tag.split("}")
    for prefix, namespace in nsmap.items():
        if namespace == split[0][1:]:
            return prefix + ":" + split[1]
    return tag


def _element_pretty_identifier(element: etree.Element) -> str:
    """
    Returns a pretty element identifier for a given XML element.

    If the prefix is known, the namespace in the element tag is replaced by the prefix.
    If additionally also the sourceline is known, is is added as a suffix to name.
    For example, instead of "{http://www.admin-shell.io/aas/2/0}assetAdministrationShell" this function would return
    "aas:assetAdministrationShell on line $line", if both, prefix and sourceline, are known.

    :param element: The xml element.
    :return: The pretty element identifier.
    """
    identifier = element.tag
    if element.prefix is not None:
        identifier = element.prefix + ":" + element.tag.split("}")[1]
    if element.sourceline is not None:
        identifier += f" on line {element.sourceline}"
    return identifier


def _constructor_name_to_typename(constructor: Callable[[etree.Element, bool], T]) -> str:
    """
    A helper function for converting the name of a constructor function to the respective type name.

    _construct_some_type -> SomeType

    :param constructor: The constructor function.
    :return: The name of the type the constructor function constructs.
    """
    return "".join([s[0].upper() + s[1:] for s in constructor.__name__.split("_")[2:]])


def _exception_to_str(exception: BaseException) -> str:
    """
    A helper function used to stringify exceptions.

    It removes the quotation marks '' that are put around str(KeyError), otherwise it's just calls str(exception).

    :param exception: The exception to stringify.
    :return: The stringified exception.
    """
    string = str(exception)
    return string[1:-1] if isinstance(exception, KeyError) else string


def _get_child_mandatory(parent: etree.Element, child_tag: str) -> etree.Element:
    """
    A helper function for getting a mandatory child element.

    :param parent: The parent element.
    :param child_tag: The tag of the child element to return.
    :return: The child element.
    :raises KeyError: If the parent element has no child element with the given tag.
    """
    child = parent.find(child_tag)
    if child is None:
        raise KeyError(_element_pretty_identifier(parent)
                       + f" has no child {_tag_replace_namespace(child_tag, parent.nsmap)}!")
    return child


def _get_child_multiple(parent: etree.Element, exppected_tag: str, failsafe: bool) -> Iterable[etree.Element]:
    """
    Iterates over all children, matching the tag.

    not failsafe: Throws an error if a child element doesn't match.
    failsafe: Logs a warning if a child element doesn't match.

    :param parent: The parent element.
    :param exppected_tag: The tag of the children.
    :return: An iterator over all child elements that match child_tag.
    :raises KeyError: If the tag of a child element doesn't match and failsafe is true.
    """
    for child in parent:
        if child.tag != exppected_tag:
            error_message = f"{_element_pretty_identifier(child)}, child of {_element_pretty_identifier(parent)}, " \
                            f"doesn't match the expected tag {_tag_replace_namespace(exppected_tag, child.nsmap)}!"
            if not failsafe:
                raise KeyError(error_message)
            logger.warning(error_message)
            continue
        yield child


def _get_attrib_mandatory(element: etree.Element, attrib: str) -> str:
    """
    A helper function for getting a mandatory attribute of an element.

    :param element: The xml element.
    :param attrib: The name of the attribute.
    :return: The value of the attribute.
    :raises KeyError: If the attribute does not exist.
    """
    if attrib not in element.attrib:
        raise KeyError(f"{_element_pretty_identifier(element)} has no attribute with name {attrib}!")
    return element.attrib[attrib]


def _get_attrib_mandatory_mapped(element: etree.Element, attrib: str, dct: Dict[str, T]) -> T:
    """
    A helper function for getting a mapped mandatory attribute of an xml element.

    It first gets the attribute value using _get_attrib_mandatory(), which raises a KeyError if the attribute
    does not exist.
    Then it returns dct[<attribute value>] and raises a ValueError, if the attribute value does not exist in the dict.

    :param element: The xml element.
    :param attrib: The name of the attribute.
    :param dct: The dictionary that is used to map the attribute value.
    :return: The mapped value of the attribute.
    :raises ValueError: If the value of the attribute does not exist in dct.
    """
    attrib_value = _get_attrib_mandatory(element, attrib)
    if attrib_value not in dct:
        raise ValueError(f"Attribute {attrib} of {_element_pretty_identifier(element)} "
                         f"has invalid value: {attrib_value}")
    return dct[attrib_value]


def _get_text_or_none(element: Optional[etree.Element]) -> Optional[str]:
    """
    A helper function for getting the text of an element, when it's not clear whether the element exists or not.

    This function is useful whenever the text of an optional child element is needed.
    Then the text can be get with: text = _get_text_or_none(element.find("childElement")
    element.find() returns either the element or None, if it doesn't exist. This is why this function accepts
    an optional element, to reduce the amount of code in the constructor functions below.

    :param element: The xml element or None.
    :return: The text of the xml element if the xml element is not None and if the xml element has a text.
             None otherwise.
    """
    return element.text if element is not None else None


def _get_text_mandatory(element: etree.Element) -> str:
    """
    A helper function for getting the mandatory text of an element.

    :param element: The xml element.
    :return: The text of the xml element.
    :raises KeyError: If the xml element has no text.
    """
    text = element.text
    if text is None:
        raise KeyError(_element_pretty_identifier(element) + " has no text!")
    return text


def _get_text_mandatory_mapped(element: etree.Element, dct: Dict[str, T]) -> T:
    """
    A helper function for getting the mapped mandatory text of an element.

    It first gets the text of the element using _get_text_mandatory(),
    which raises a KeyError if the element has no text.
    Then it returns dct[<element text>] and raises a ValueError, if the text of the element does not exist in the dict.

    :param element: The xml element.
    :param dct: The dictionary that is used to map the text.
    :return: The mapped text of the element.
    :raises ValueError: If the text of the xml element does not exist in dct.
    """
    text = _get_text_mandatory(element)
    if text not in dct:
        raise ValueError(_element_pretty_identifier(element) + f" has invalid text: {text}")
    return dct[text]


def _failsafe_construct(element: Optional[etree.Element], constructor: Callable[..., T], failsafe: bool,
                        **kwargs: Any) -> Optional[T]:
    """
    A wrapper function that is used to handle exceptions raised in constructor functions.

    This is the only function of this module where exceptions are caught.
    This is why constructor functions should (in almost all cases) call other constructor functions using this function,
    so errors can be caught and logged in failsafe mode.
    The functions accepts None as a valid value for element for the same reason _get_text_or_none() does, so it can be
    called like _failsafe_construct(element.find("childElement"), ...), since element.find() can return None.
    This function will also return None in this case.

    :param element: The xml element or None.
    :param constructor: The constructor function to apply on the element.
    :param failsafe: Indicates whether errors should be caught or re-raised.
    :param kwargs: Optional keyword arguments that are passed to the constructor function.
    :return: The constructed class instance, if construction was successful.
             None if the element was None or if the construction failed.
    """
    if element is None:
        return None
    try:
        return constructor(element, failsafe, **kwargs)
    except (KeyError, ValueError) as e:
        type_name = _constructor_name_to_typename(constructor)
        error_message = f"Failed to create {type_name} from {_element_pretty_identifier(element)}!"
        if not failsafe:
            raise type(e)(error_message) from e
        error_type = type(e).__name__
        cause: Optional[BaseException] = e
        while cause is not None:
            error_message = _exception_to_str(cause) + "\n -> " + error_message
            cause = cause.__cause__
        logger.error(error_type + ": " + error_message)
        return None


def _failsafe_construct_mandatory(element: etree.Element, constructor: Callable[..., T], **kwargs: Any) -> T:
    """
    _failsafe_construct() but not failsafe and it returns T instead of Optional[T]

    :param element: The xml element.
    :param constructor: The constructor function to apply on the xml element.
    :param kwargs: Optional keyword arguments that are passed to the constructor function.
    :return: The constructed child element.
    :raises TypeError: If the result of _failsafe_construct() in non-failsafe mode was None.
                       This shouldn't be possible and if it happens, indicates a bug in _failsafe_construct().
    """
    constructed = _failsafe_construct(element, constructor, False, **kwargs)
    if constructed is None:
        raise TypeError("The result of a non-failsafe _failsafe_construct() call was None! "
                        "This is a bug in the pyAAS XML deserialization, please report it!")
    return constructed


def _failsafe_construct_multiple(elements: Iterable[etree.Element], constructor: Callable[..., T], failsafe: bool,
                                 **kwargs: Any) -> Iterable[T]:
    """
    A generator function that applies _failsafe_construct() to multiple elements.

    :param elements: Any iterable containing any number of xml elements.
    :param constructor: The constructor function to apply on the xml elements.
    :param failsafe: Indicates whether errors should be caught or re-raised.
    :param kwargs: Optional keyword arguments that are passed to the constructor function.
    :return: An iterator over the successfully constructed elements.
             If an error occurred while constructing an element and while in failsafe mode,
             the respective element will be skipped.
    """
    for element in elements:
        parsed = _failsafe_construct(element, constructor, failsafe, **kwargs)
        if parsed is not None:
            yield parsed


def _child_construct_mandatory(parent: etree.Element, child_tag: str, constructor: Callable[..., T], **kwargs: Any) \
        -> T:
    """
    Shorthand for _failsafe_construct_mandatory() in combination with _get_child_mandatory().

    :param parent: The xml element where the child element is searched.
    :param child_tag: The tag of the child element to construct.
    :param constructor: The constructor function for the child element.
    :param kwargs: Optional keyword arguments that are passed to the constructor function.
    :return: The constructed child element.
    """
    return _failsafe_construct_mandatory(_get_child_mandatory(parent, child_tag), constructor, **kwargs)


def _child_construct_multiple(parent: etree.Element, expected_tag: str, constructor: Callable[..., T], failsafe: bool,
                              **kwargs: Any) -> Iterable[T]:
    """
    Shorthand for _failsafe_construct_multiple() in combination with _get_child_multiple().

    :param parent: The xml element where child elements are searched.
    :param expected_tag: The expected tag of the child elements.
    :param constructor: The constructor function for the child element.
    :param kwargs: Optional keyword arguments that are passed to the constructor function.
    :return: An iterator over successfully constructed child elements.
             If an error occurred while constructing an element and while in failsafe mode,
             the respective element will be skipped.
    """
    return _failsafe_construct_multiple(_get_child_multiple(parent, expected_tag, failsafe), constructor, failsafe,
                                        **kwargs)


def _child_text_mandatory(parent: etree.Element, child_tag: str) -> str:
    """
    Shorthand for _get_text_mandatory() in combination with _get_child_mandatory().

    :param parent: The xml element where the child element is searched.
    :param child_tag: The tag of the child element to get the text from.
    :return: The text of the child element.
    """
    return _get_text_mandatory(_get_child_mandatory(parent, child_tag))


def _child_text_mandatory_mapped(parent: etree.Element, child_tag: str, dct: Dict[str, T]) -> T:
    """
    Shorthand for _get_text_mandatory_mapped() in combination with _get_child_mandatory().

    :param parent: The xml element where the child element is searched.
    :param child_tag: The tag of the child element to get the text from.
    :param dct: The dictionary that is used to map the text of the child element.
    :return: The mapped text of the child element.
    """
    return _get_text_mandatory_mapped(_get_child_mandatory(parent, child_tag), dct)


def _amend_abstract_attributes(obj: object, element: etree.Element, failsafe: bool) -> None:
    """
    A helper function that amends optional attributes to already constructed class instances, if they inherit
    from an abstract class like Referable, Identifiable, HasSemantics or Qualifiable.

    :param obj: The constructed class instance.
    :param element: The respective xml element.
    :param failsafe: Indicates whether errors should be caught or re-raised.
    :return: None
    """
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
        qualifiers = element.find(NS_AAS + "qualifiers")
        if qualifiers is not None:
            for constraint in _failsafe_construct_multiple(qualifiers, _construct_constraint, failsafe):
                obj.qualifier.add(constraint)


class ModelingKindKwArg(TypedDict, total=False):
    kind: model.ModelingKind


def _get_modeling_kind_kwarg(element: etree.Element) -> ModelingKindKwArg:
    """
    A helper function that creates a dict containing the modeling kind or nothing for a given xml element.

    Since the modeling kind can only be set in the __init__ method of a class that inherits from model.HasKind,
    the dict returned by this function can be passed directly to the classes __init__ method.
    An alternative to this function would be returning the modeling kind directly and falling back to the default
    value if no "kind" xml element is present, but in this case the default value would have to be defined here as well.
    In my opinion defining what the default value is, should be the task of the __init__ method, not the task of any
    function in the deserialization.

    :param element: The xml element.
    :return: A dict containing {"kind": <the parsed modeling kind>}, if a kind element was found.
             An empty dict if not.
    """
    kwargs: ModelingKindKwArg = ModelingKindKwArg()
    kind = element.find(NS_AAS + "kind")
    if kind is not None:
        kwargs["kind"] = _get_text_mandatory_mapped(kind, MODELING_KIND_INVERSE)
    return kwargs


def _construct_key(element: etree.Element, _failsafe: bool, **_kwargs: Any) -> model.Key:
    return model.Key(
        _get_attrib_mandatory_mapped(element, "type", KEY_ELEMENTS_INVERSE),
        _str_to_bool(_get_attrib_mandatory(element, "local")),
        _get_text_mandatory(element),
        _get_attrib_mandatory_mapped(element, "idType", KEY_TYPES_INVERSE)
    )


def _construct_key_tuple(element: etree.Element, failsafe: bool, **_kwargs: Any) -> Tuple[model.Key, ...]:
    keys = _get_child_mandatory(element, NS_AAS + "keys")
    return tuple(_child_construct_multiple(keys, NS_AAS + "key", _construct_key, failsafe))


def _construct_reference(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Reference:
    return model.Reference(_construct_key_tuple(element, failsafe))


def _construct_aas_reference(element: etree.Element, failsafe: bool, type_: Type[model.base._RT], **_kwargs: Any) \
        -> model.AASReference[model.base._RT]:
    keys = _construct_key_tuple(element, failsafe)
    if len(keys) != 0 and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type, type(None)), type_):
        logger.warning(f"Type {keys[-1].type.name} of last key of reference to {' / '.join(str(k) for k in keys)} "
                       f"does not match reference type {type_.__name__}")
    return model.AASReference(keys, type_)


def _construct_submodel_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.Submodel]:
    return _construct_aas_reference(element, failsafe, model.Submodel, **kwargs)


def _construct_asset_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.Asset]:
    return _construct_aas_reference(element, failsafe, model.Asset, **kwargs)


def _construct_asset_administration_shell_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.AssetAdministrationShell]:
    return _construct_aas_reference(element, failsafe, model.AssetAdministrationShell, **kwargs)


def _construct_referable_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.Referable]:
    return _construct_aas_reference(element, failsafe, model.Referable, **kwargs)


def _construct_concept_description_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.ConceptDescription]:
    return _construct_aas_reference(element, failsafe, model.ConceptDescription, **kwargs)


def _construct_data_element_reference(element: etree.Element, failsafe: bool, **kwargs: Any) \
        -> model.AASReference[model.DataElement]:
    return _construct_aas_reference(element, failsafe, model.DataElement, **kwargs)


def _construct_administrative_information(element: etree.Element, _failsafe: bool, **_kwargs: Any) \
        -> model.AdministrativeInformation:
    return model.AdministrativeInformation(
        _get_text_or_none(element.find(NS_AAS + "version")),
        _get_text_or_none(element.find(NS_AAS + "revision"))
    )


def _construct_lang_string_set(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.LangStringSet:
    lss: model.LangStringSet = {}
    for lang_string in _get_child_multiple(element, NS_AAS + "langString", failsafe):
        lss[_get_attrib_mandatory(lang_string, "lang")] = _get_text_mandatory(lang_string)
    return lss


def _construct_qualifier(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Qualifier:
    qualifier = model.Qualifier(
        _child_text_mandatory(element, NS_AAS + "type"),
        _child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES)
    )
    value = _get_text_or_none(element.find(NS_AAS + "value"))
    if value is not None:
        qualifier.value = model.datatypes.from_xsd(value, qualifier.value_type)
    value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), _construct_reference, failsafe)
    if value_id is not None:
        qualifier.value_id = value_id
    _amend_abstract_attributes(qualifier, element, failsafe)
    return qualifier


def _construct_formula(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Formula:
    formula = model.Formula()
    depends_on_refs = element.find(NS_AAS + "dependsOnRefs")
    if depends_on_refs is not None:
        for ref in _failsafe_construct_multiple(depends_on_refs.findall(NS_AAS + "reference"), _construct_reference,
                                                failsafe):
            formula.depends_on.add(ref)
    return formula


def _construct_identifier(element: etree.Element, _failsafe: bool, **_kwargs: Any) -> model.Identifier:
    return model.Identifier(
        _get_text_mandatory(element),
        _get_attrib_mandatory_mapped(element, "idType", IDENTIFIER_TYPES_INVERSE)
    )


def _construct_security(_element: etree.Element, _failsafe: bool, **_kwargs: Any) -> model.Security:
    """
    TODO: this is just a stub implementation
    """
    return model.Security()


def _construct_view(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.View:
    view = model.View(_child_text_mandatory(element, NS_AAS + "idShort"))
    contained_elements = element.find(NS_AAS + "containedElements")
    if contained_elements is not None:
        for ref in _failsafe_construct_multiple(contained_elements.findall(NS_AAS + "containedElementRef"),
                                                _construct_referable_reference, failsafe):
            view.contained_element.add(ref)
    _amend_abstract_attributes(view, element, failsafe)
    return view


def _construct_concept_dictionary(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDictionary:
    concept_dictionary = model.ConceptDictionary(_child_text_mandatory(element, NS_AAS + "idShort"))
    concept_description = element.find(NS_AAS + "conceptDescriptionRefs")
    if concept_description is not None:
        for ref in _failsafe_construct_multiple(concept_description.findall(NS_AAS + "conceptDescriptionRef"),
                                                _construct_concept_description_reference, failsafe):
            concept_dictionary.concept_description.add(ref)
    _amend_abstract_attributes(concept_dictionary, element, failsafe)
    return concept_dictionary


def _construct_submodel_element(element: etree.Element, failsafe: bool, **kwargs: Any) -> model.SubmodelElement:
    submodel_elements: Dict[str, Callable[..., model.SubmodelElement]] = {NS_AAS + k: v for k, v in {
        "annotatedRelationshipElement": _construct_annotated_relationship_element,
        "basicEvent": _construct_basic_event,
        "blob": _construct_blob,
        "capability": _construct_capability,
        "entity": _construct_entity,
        "file": _construct_file,
        "multiLanguageProperty": _construct_multi_language_property,
        "operation": _construct_operation,
        "property": _construct_property,
        "range": _construct_range,
        "referenceElement": _construct_reference_element,
        "relationshipElement": _construct_relationship_element,
        "submodelElementCollection": _construct_submodel_element_collection
    }.items()}
    if element.tag not in submodel_elements:
        raise KeyError(_element_pretty_identifier(element) + " is not a valid submodel element!")
    return submodel_elements[element.tag](element, failsafe, **kwargs)


def _construct_constraint(element: etree.Element, failsafe: bool, **kwargs: Any) -> model.Constraint:
    constraints: Dict[str, Callable[..., model.Constraint]] = {NS_AAS + k: v for k, v in {
        "formula": _construct_formula,
        "qualifier": _construct_qualifier
    }.items()}
    if element.tag not in constraints:
        raise KeyError(_element_pretty_identifier(element) + " is not a valid constraint!")
    return constraints[element.tag](element, failsafe, **kwargs)


def _construct_operation_variable(element: etree.Element, _failsafe: bool, **_kwargs: Any) -> model.OperationVariable:
    value = _get_child_mandatory(element, NS_AAS + "value")
    if len(value) == 0:
        raise KeyError(f"{_element_pretty_identifier(value)} has no submodel element!")
    if len(value) > 1:
        logger.warning(f"{_element_pretty_identifier(value)} has more than one submodel element,"
                       "using the first one...")
    return model.OperationVariable(
        _failsafe_construct_mandatory(value[0], _construct_submodel_element)
    )


def _construct_annotated_relationship_element(element: etree.Element, failsafe: bool, **_kwargs: Any) \
        -> model.AnnotatedRelationshipElement:
    annotated_relationship_element = model.AnnotatedRelationshipElement(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_construct_mandatory(element, NS_AAS + "first", _construct_referable_reference),
        _child_construct_mandatory(element, NS_AAS + "second", _construct_referable_reference),
        **_get_modeling_kind_kwarg(element)
    )
    annotations = _get_child_mandatory(element, NS_AAS + "annotations")
    for data_element_ref in _failsafe_construct_multiple(annotations.findall(NS_AAS + "reference"),
                                                         _construct_data_element_reference, failsafe):
        annotated_relationship_element.annotation.add(data_element_ref)
    _amend_abstract_attributes(annotated_relationship_element, element, failsafe)
    return annotated_relationship_element


def _construct_basic_event(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.BasicEvent:
    basic_event = model.BasicEvent(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_construct_mandatory(element, NS_AAS + "observed", _construct_referable_reference),
        **_get_modeling_kind_kwarg(element)
    )
    _amend_abstract_attributes(basic_event, element, failsafe)
    return basic_event


def _construct_blob(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Blob:
    blob = model.Blob(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_text_mandatory(element, NS_AAS + "mimeType"),
        **_get_modeling_kind_kwarg(element)
    )
    value = element.find(NS_AAS + "value")
    if value is not None:
        blob.value = base64.b64decode(_get_text_mandatory(value))
    _amend_abstract_attributes(blob, element, failsafe)
    return blob


def _construct_capability(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Capability:
    capability = model.Capability(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    _amend_abstract_attributes(capability, element, failsafe)
    return capability


def _construct_entity(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Entity:
    entity = model.Entity(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_text_mandatory_mapped(element, NS_AAS + "entityType", ENTITY_TYPES_INVERSE),
        **_get_modeling_kind_kwarg(element)
    )
    asset_ref = _failsafe_construct(element.find(NS_AAS + "assetRef"), _construct_asset_reference, failsafe)
    if asset_ref is not None:
        entity.asset = asset_ref
    for stmt in _failsafe_construct_multiple(_get_child_mandatory(element, NS_AAS + "statements"),
                                             _construct_submodel_element, failsafe):
        entity.statement.add(stmt)
    _amend_abstract_attributes(entity, element, failsafe)
    return entity


def _construct_file(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.File:
    file = model.File(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    value = element.find(NS_AAS + "value")
    if value is not None:
        file.value = _get_text_mandatory(value)
    _amend_abstract_attributes(file, element, failsafe)
    return file


def _construct_multi_language_property(element: etree.Element, failsafe: bool, **_kwargs: Any) \
        -> model.MultiLanguageProperty:
    multi_language_property = model.MultiLanguageProperty(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    value = _failsafe_construct(element.find(NS_AAS + "value"), _construct_lang_string_set, failsafe)
    if value is not None:
        multi_language_property.value = value
    value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), _construct_reference, failsafe)
    if value_id is not None:
        multi_language_property.value_id = value_id
    _amend_abstract_attributes(multi_language_property, element, failsafe)
    return multi_language_property


def _construct_operation(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Operation:
    operation = model.Operation(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    in_output_variable = element.find(NS_AAS + "inoutputVariable")
    if in_output_variable is not None:
        for var in _child_construct_multiple(in_output_variable, NS_AAS + "operationVariable",
                                             _construct_operation_variable, failsafe):
            operation.in_output_variable.append(var)
    input_variable = element.find(NS_AAS + "inputVariable")
    if input_variable is not None:
        for var in _child_construct_multiple(input_variable, NS_AAS + "operationVariable",
                                             _construct_operation_variable, failsafe):
            operation.input_variable.append(var)
    output_variable = element.find(NS_AAS + "outputVariable")
    if output_variable is not None:
        for var in _child_construct_multiple(output_variable, NS_AAS + "operationVariable",
                                             _construct_operation_variable, failsafe):
            operation.output_variable.append(var)
    _amend_abstract_attributes(operation, element, failsafe)
    return operation


def _construct_property(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Property:
    property_ = model.Property(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        value_type=_child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES),
        **_get_modeling_kind_kwarg(element)
    )
    value = _get_text_or_none(element.find(NS_AAS + "value"))
    if value is not None:
        property_.value = model.datatypes.from_xsd(value, property_.value_type)
    value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), _construct_reference, failsafe)
    if value_id is not None:
        property_.value_id = value_id
    _amend_abstract_attributes(property_, element, failsafe)
    return property_


def _construct_range(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Range:
    range_ = model.Range(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        value_type=_child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES),
        **_get_modeling_kind_kwarg(element)
    )
    max_ = _get_text_or_none(element.find(NS_AAS + "max"))
    if max_ is not None:
        range_.max = model.datatypes.from_xsd(max_, range_.value_type)
    min_ = _get_text_or_none(element.find(NS_AAS + "min"))
    if min_ is not None:
        range_.min = model.datatypes.from_xsd(min_, range_.value_type)
    _amend_abstract_attributes(range_, element, failsafe)
    return range_


def _construct_reference_element(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.ReferenceElement:
    reference_element = model.ReferenceElement(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    value = _failsafe_construct(element.find(NS_AAS + "value"), _construct_referable_reference, failsafe)
    if value is not None:
        reference_element.value = value
    _amend_abstract_attributes(reference_element, element, failsafe)
    return reference_element


def _construct_relationship_element(element: etree.Element, failsafe: bool, **_kwargs: Any) \
        -> model.RelationshipElement:
    relationship_element = model.RelationshipElement(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        _child_construct_mandatory(element, NS_AAS + "first", _construct_referable_reference),
        _child_construct_mandatory(element, NS_AAS + "second", _construct_referable_reference),
        **_get_modeling_kind_kwarg(element)
    )
    _amend_abstract_attributes(relationship_element, element, failsafe)
    return relationship_element


def _construct_submodel_element_collection(element: etree.Element, failsafe: bool, **_kwargs: Any) \
        -> model.SubmodelElementCollection:
    ordered = _str_to_bool(_child_text_mandatory(element, NS_AAS + "ordered"))
    collection_type = model.SubmodelElementCollectionOrdered if ordered else model.SubmodelElementCollectionUnordered
    collection = collection_type(
        _child_text_mandatory(element, NS_AAS + "idShort"),
        **_get_modeling_kind_kwarg(element)
    )
    value = _get_child_mandatory(element, NS_AAS + "value")
    for se in _failsafe_construct_multiple(value, _construct_submodel_element, failsafe):
        collection.value.add(se)
    _amend_abstract_attributes(collection, element, failsafe)
    return collection


def _construct_asset_administration_shell(element: etree.Element, failsafe: bool, **_kwargs: Any) \
        -> model.AssetAdministrationShell:
    aas = model.AssetAdministrationShell(
        _child_construct_mandatory(element, NS_AAS + "assetRef", _construct_asset_reference),
        _child_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    security = _failsafe_construct(element.find(NS_ABAC + "security"), _construct_security, failsafe)
    if security is not None:
        aas.security = security
    submodels = element.find(NS_AAS + "submodelRefs")
    if submodels is not None:
        for ref in _child_construct_multiple(submodels, NS_AAS + "submodelRef", _construct_submodel_reference,
                                             failsafe):
            aas.submodel.add(ref)
    views = element.find(NS_AAS + "views")
    if views is not None:
        for view in _child_construct_multiple(views, NS_AAS + "view", _construct_view, failsafe):
            aas.view.add(view)
    concept_dictionaries = element.find(NS_AAS + "conceptDictionaries")
    if concept_dictionaries is not None:
        for cd in _child_construct_multiple(concept_dictionaries, NS_AAS + "conceptDictionary",
                                            _construct_concept_dictionary, failsafe):
            aas.concept_dictionary.add(cd)
    derived_from = _failsafe_construct(element.find(NS_AAS + "derivedFrom"),
                                       _construct_asset_administration_shell_reference, failsafe)
    if derived_from is not None:
        aas.derived_from = derived_from
    _amend_abstract_attributes(aas, element, failsafe)
    return aas


def _construct_asset(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Asset:
    asset = model.Asset(
        _child_text_mandatory_mapped(element, NS_AAS + "kind", ASSET_KIND_INVERSE),
        _child_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    asset_identification_model = _failsafe_construct(element.find(NS_AAS + "assetIdentificationModelRef"),
                                                     _construct_submodel_reference, failsafe)
    if asset_identification_model is not None:
        asset.asset_identification_model = asset_identification_model
    bill_of_material = _failsafe_construct(element.find(NS_AAS + "billOfMaterialRef"), _construct_submodel_reference,
                                           failsafe)
    if bill_of_material is not None:
        asset.bill_of_material = bill_of_material
    _amend_abstract_attributes(asset, element, failsafe)
    return asset


def _construct_submodel(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.Submodel:
    submodel = model.Submodel(
        _child_construct_mandatory(element, NS_AAS + "identification", _construct_identifier),
        **_get_modeling_kind_kwarg(element)
    )
    for submodel_element in _get_child_mandatory(element, NS_AAS + "submodelElements"):
        constructed = _failsafe_construct(submodel_element, _construct_submodel_element, failsafe)
        if constructed is not None:
            submodel.submodel_element.add(constructed)
    _amend_abstract_attributes(submodel, element, failsafe)
    return submodel


def _construct_concept_description(element: etree.Element, failsafe: bool, **_kwargs: Any) -> model.ConceptDescription:
    cd = model.ConceptDescription(
        _child_construct_mandatory(element, NS_AAS + "identification", _construct_identifier)
    )
    for ref in _failsafe_construct_multiple(element.findall(NS_AAS + "isCaseOf"), _construct_reference, failsafe):
        cd.is_case_of.add(ref)
    _amend_abstract_attributes(cd, element, failsafe)
    return cd


def read_xml_aas_file(file: IO, failsafe: bool = True) -> model.DictObjectStore:
    """
    Read an Asset Administration Shell XML file according to 'Details of the Asset Administration Shell', chapter 5.4

    :param file: A filename or file-like object to read the XML-serialized data from
    :param failsafe: If True, the file is parsed in a failsafe way: Instead of raising an Exception for missing
                     attributes and wrong types, errors are logged and defective objects are skipped
    :return: A DictObjectStore containing all AAS objects from the XML file
    """

    element_constructors = {NS_AAS + k: v for k, v in {
        "assetAdministrationShell": _construct_asset_administration_shell,
        "asset": _construct_asset,
        "submodel": _construct_submodel,
        "conceptDescription": _construct_concept_description
    }.items()}

    ret: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)

    try:
        tree = etree.parse(file, parser)
    except etree.XMLSyntaxError as e:
        if failsafe:
            logger.error(e)
            return ret
        raise e

    root = tree.getroot()

    # Add AAS objects to ObjectStore
    for list_ in root:
        element_tag = list_.tag[:-1]
        if list_.tag[-1] != "s" or element_tag not in element_constructors:
            error_message = f"Unexpected top-level list {_element_pretty_identifier(list_)}!"
            if not failsafe:
                raise TypeError(error_message)
            logger.warning(error_message)
            continue
        constructor = element_constructors[element_tag]
        for element in _child_construct_multiple(list_, element_tag, constructor, failsafe):
            # element is always Identifiable, because the tag is checked earlier
            # this is just to satisfy the type checker
            if isinstance(element, model.Identifiable):
                ret.add(element)
    return ret
