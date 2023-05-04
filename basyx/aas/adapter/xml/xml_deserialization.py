# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
.. _adapter.xml.xml_deserialization:

Module for deserializing Asset Administration Shell data from the official XML format

This module provides the following functions for parsing XML documents:

- :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_element` constructs a single object from an XML document
  containing a single element
- :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_file_into` constructs all elements of an XML document and
  stores them in a given :class:`ObjectStore <aas.model.provider.AbstractObjectStore>`
- :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_file` constructs all elements of an XML document and returns
  them in a :class:`~aas.model.provider.DictObjectStore`

These functions take a decoder class as keyword argument, which allows parsing in failsafe (default) or non-failsafe
mode. Parsing stripped elements - used in the HTTP adapter - is also possible. It is also possible to subclass the
default decoder class and provide an own decoder.

In failsafe mode errors regarding missing attributes and elements or invalid values are caught and logged.
In non-failsafe mode any error would abort parsing.
Error handling is done only by `_failsafe_construct()` in this module. Nearly all constructor functions are called
by other constructor functions via `_failsafe_construct()`, so an error chain is constructed in the error case,
which allows printing stacktrace-like error messages like the following in the error case (in failsafe mode of course):


.. code-block::

    KeyError: aas:identification on line 252 has no attribute with name idType!
        -> Failed to construct aas:identification on line 252 using construct_identifier!
        -> Failed to construct aas:conceptDescription on line 247 using construct_concept_description!


Unlike the JSON deserialization, parsing is done top-down. Elements with a specific tag are searched on the level
directly below the level of the current xml element (in terms of parent and child relation) and parsed when
found. Constructor functions of these elements will then again search for mandatory and optional child elements
and construct them if available, and so on.
"""

from ... import model
from lxml import etree  # type: ignore
import logging
import base64
import enum

from typing import Any, Callable, Dict, IO, Iterable, Optional, Set, Tuple, Type, TypeVar
from .xml_serialization import NS_AAS, NS_ABAC, NS_IEC
from .._generic import MODELING_KIND_INVERSE, ASSET_KIND_INVERSE, KEY_ELEMENTS_INVERSE, KEY_TYPES_INVERSE, \
    IDENTIFIER_TYPES_INVERSE, ENTITY_TYPES_INVERSE, IEC61360_DATA_TYPES_INVERSE, IEC61360_LEVEL_TYPES_INVERSE, \
    KEY_ELEMENTS_CLASSES_INVERSE

logger = logging.getLogger(__name__)

T = TypeVar("T")
RE = TypeVar("RE", bound=model.RelationshipElement)


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


def _get_all_children_expect_tag(parent: etree.Element, expected_tag: str, failsafe: bool) -> Iterable[etree.Element]:
    """
    Iterates over all children, matching the tag.

    not failsafe: Throws an error if a child element doesn't match.
    failsafe: Logs a warning if a child element doesn't match.

    :param parent: The parent element.
    :param expected_tag: The tag of the children.
    :return: An iterator over all child elements that match child_tag.
    :raises KeyError: If the tag of a child element doesn't match and failsafe is true.
    """
    for child in parent:
        if child.tag != expected_tag:
            error_message = f"{_element_pretty_identifier(child)}, child of {_element_pretty_identifier(parent)}, " \
                            f"doesn't match the expected tag {_tag_replace_namespace(expected_tag, child.nsmap)}!"
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


def _get_text_mapped_or_none(element: Optional[etree.Element], dct: Dict[str, T]) -> Optional[T]:
    """
    Returns dct[element.text] or None, if the element is None, has no text or the text is not in dct.

    :param element: The xml element or None.
    :param dct: The dictionary that is used to map the text.
    :return: The mapped text or None.
    """
    text = _get_text_or_none(element)
    if text is None or text not in dct:
        return None
    return dct[text]


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
        return constructor(element, **kwargs)
    except (KeyError, ValueError) as e:
        error_message = f"Failed to construct {_element_pretty_identifier(element)} using {constructor.__name__}!"
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
                        "This is a bug in the Eclipse BaSyx Python SDK XML deserialization, please report it!")
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


def _child_construct_multiple(parent: etree.Element, expected_tag: str, constructor: Callable[..., T],
                              failsafe: bool, **kwargs: Any) -> Iterable[T]:
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
    return _failsafe_construct_multiple(_get_all_children_expect_tag(parent, expected_tag, failsafe), constructor,
                                        failsafe, **kwargs)


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


def _get_modeling_kind(element: etree.Element) -> model.ModelingKind:
    """
    Returns the modeling kind of an element with the default value INSTANCE, if none specified.

    :param element: The xml element.
    :return: The modeling kind of the element.
    """
    modeling_kind = _get_text_mapped_or_none(element.find(NS_AAS + "kind"), MODELING_KIND_INVERSE)
    return modeling_kind if modeling_kind is not None else model.ModelingKind.INSTANCE


class AASFromXmlDecoder:
    """
    The default XML decoder class.

    It parses XML documents in a failsafe manner, meaning any errors encountered will be logged and invalid XML elements
    will be skipped.
    Most member functions support the `object_class` parameter. It was introduced so they can be overwritten
    in subclasses, which allows constructing instances of subtypes.
    """
    failsafe = True
    stripped = False

    @classmethod
    def _amend_abstract_attributes(cls, obj: object, element: etree.Element) -> None:
        """
        A helper function that amends optional attributes to already constructed class instances, if they inherit
        from an abstract class like Referable, Identifiable, HasSemantics or Qualifiable.

        :param obj: The constructed class instance.
        :param element: The respective xml element.
        :return: None
        """
        if isinstance(obj, model.Referable):
            category = _get_text_or_none(element.find(NS_AAS + "category"))
            if category is not None:
                obj.category = category
            description = _failsafe_construct(element.find(NS_AAS + "description"), cls.construct_lang_string_set,
                                              cls.failsafe)
            if description is not None:
                obj.description = description
        if isinstance(obj, model.Identifiable):
            id_short = _get_text_or_none(element.find(NS_AAS + "idShort"))
            if id_short is not None:
                obj.id_short = id_short
            administration = _failsafe_construct(element.find(NS_AAS + "administration"),
                                                 cls.construct_administrative_information, cls.failsafe)
            if administration:
                obj.administration = administration
        if isinstance(obj, model.HasSemantics):
            semantic_id = _failsafe_construct(element.find(NS_AAS + "semanticId"), cls.construct_reference,
                                              cls.failsafe)
            if semantic_id is not None:
                obj.semantic_id = semantic_id
        if isinstance(obj, model.Qualifiable) and not cls.stripped:
            # TODO: simplify this should our suggestion regarding the XML schema get accepted
            # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
            for constraint in element.findall(NS_AAS + "qualifier"):
                if len(constraint) == 0:
                    continue
                if len(constraint) > 1:
                    logger.warning(f"{_element_pretty_identifier(constraint)} has more than one constraint, "
                                   "which is invalid! Deserializing all constraints anyways...")
                for constructed in _failsafe_construct_multiple(constraint, cls.construct_constraint, cls.failsafe):
                    obj.qualifier.add(constructed)

    @classmethod
    def _construct_relationship_element_internal(cls, element: etree.Element, object_class: Type[RE], **_kwargs: Any) \
            -> RE:
        """
        Helper function used by construct_relationship_element() and construct_annotated_relationship_element()
        to reduce duplicate code
        """
        relationship_element = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            _child_construct_mandatory(element, NS_AAS + "first", cls._construct_referable_reference),
            _child_construct_mandatory(element, NS_AAS + "second", cls._construct_referable_reference),
            kind=_get_modeling_kind(element)
        )
        cls._amend_abstract_attributes(relationship_element, element)
        return relationship_element

    @classmethod
    def _construct_key_tuple(cls, element: etree.Element, namespace: str = NS_AAS, **_kwargs: Any) \
            -> Tuple[model.Key, ...]:
        """
        Helper function used by construct_reference() and construct_aas_reference() to reduce duplicate code
        """
        keys = _get_child_mandatory(element, namespace + "keys")
        return tuple(_child_construct_multiple(keys, namespace + "key", cls.construct_key, cls.failsafe))

    @classmethod
    def _construct_submodel_reference(cls, element: etree.Element, **kwargs: Any) -> model.AASReference[model.Submodel]:
        """
        Helper function. Doesn't support the object_class parameter. Overwrite construct_aas_reference instead.
        """
        return cls.construct_aas_reference_expect_type(element, model.Submodel, **kwargs)

    @classmethod
    def _construct_asset_reference(cls, element: etree.Element, **kwargs: Any) \
            -> model.AASReference[model.Asset]:
        """
        Helper function. Doesn't support the object_class parameter. Overwrite construct_aas_reference instead.
        """
        return cls.construct_aas_reference_expect_type(element, model.Asset, **kwargs)

    @classmethod
    def _construct_asset_administration_shell_reference(cls, element: etree.Element, **kwargs: Any) \
            -> model.AASReference[model.AssetAdministrationShell]:
        """
        Helper function. Doesn't support the object_class parameter. Overwrite construct_aas_reference instead.
        """
        return cls.construct_aas_reference_expect_type(element, model.AssetAdministrationShell, **kwargs)

    @classmethod
    def _construct_referable_reference(cls, element: etree.Element, **kwargs: Any) \
            -> model.AASReference[model.Referable]:
        """
        Helper function. Doesn't support the object_class parameter. Overwrite construct_aas_reference instead.
        """
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        return cls.construct_aas_reference_expect_type(element, model.Referable, **kwargs)  # type: ignore

    @classmethod
    def _construct_concept_description_reference(cls, element: etree.Element, **kwargs: Any) \
            -> model.AASReference[model.ConceptDescription]:
        """
        Helper function. Doesn't support the object_class parameter. Overwrite construct_aas_reference instead.
        """
        return cls.construct_aas_reference_expect_type(element, model.ConceptDescription, **kwargs)

    @classmethod
    def construct_key(cls, element: etree.Element, object_class=model.Key, **_kwargs: Any) \
            -> model.Key:
        return object_class(
            _get_attrib_mandatory_mapped(element, "type", KEY_ELEMENTS_INVERSE),
            _str_to_bool(_get_attrib_mandatory(element, "local")),
            _get_text_mandatory(element),
            _get_attrib_mandatory_mapped(element, "idType", KEY_TYPES_INVERSE)
        )

    @classmethod
    def construct_reference(cls, element: etree.Element, namespace: str = NS_AAS, object_class=model.Reference,
                            **_kwargs: Any) -> model.Reference:
        return object_class(cls._construct_key_tuple(element, namespace=namespace))

    @classmethod
    def construct_aas_reference(cls, element: etree.Element, object_class=model.AASReference, **_kwargs: Any) \
            -> model.AASReference:
        """
        This constructor for AASReference determines the type of the AASReference by its keys. If no keys are present,
        it will default to the type Referable. This behaviour is wanted in read_aas_xml_element().
        """
        keys = cls._construct_key_tuple(element)
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        type_: Type[model.Referable] = model.Referable  # type: ignore
        if len(keys) > 0:
            type_ = KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type, model.Referable)  # type: ignore
        return object_class(keys, type_)

    @classmethod
    def construct_aas_reference_expect_type(cls, element: etree.Element, type_: Type[model.base._RT],
                                            object_class=model.AASReference, **_kwargs: Any) \
            -> model.AASReference[model.base._RT]:
        """
        This constructor for AASReference allows passing an expected type, which is checked against the type of the last
        key of the reference. This constructor function is used by other constructor functions, since all expect a
        specific target type.
        """
        keys = cls._construct_key_tuple(element)
        if keys and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type, type(None)), type_):
            logger.warning("type %s of last key of reference to %s does not match reference type %s",
                           keys[-1].type.name, " / ".join(str(k) for k in keys), type_.__name__)
        return object_class(keys, type_)

    @classmethod
    def construct_administrative_information(cls, element: etree.Element, object_class=model.AdministrativeInformation,
                                             **_kwargs: Any) -> model.AdministrativeInformation:
        return object_class(
            _get_text_or_none(element.find(NS_AAS + "version")),
            _get_text_or_none(element.find(NS_AAS + "revision"))
        )

    @classmethod
    def construct_lang_string_set(cls, element: etree.Element, namespace: str = NS_AAS, **_kwargs: Any) \
            -> model.LangStringSet:
        """
        This function doesn't support the object_class parameter, because LangStringSet is just a generic type alias.
        """
        lss: model.LangStringSet = {}
        for lang_string in _get_all_children_expect_tag(element, namespace + "langString", cls.failsafe):
            lss[_get_attrib_mandatory(lang_string, "lang")] = _get_text_mandatory(lang_string)
        return lss

    @classmethod
    def construct_qualifier(cls, element: etree.Element, object_class=model.Qualifier, **_kwargs: Any) \
            -> model.Qualifier:
        qualifier = object_class(
            _child_text_mandatory(element, NS_AAS + "type"),
            _child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES)
        )
        value = _get_text_or_none(element.find(NS_AAS + "value"))
        if value is not None:
            qualifier.value = model.datatypes.from_xsd(value, qualifier.value_type)
        value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), cls.construct_reference, cls.failsafe)
        if value_id is not None:
            qualifier.value_id = value_id
        cls._amend_abstract_attributes(qualifier, element)
        return qualifier

    @classmethod
    def construct_formula(cls, element: etree.Element, object_class=model.Formula, **_kwargs: Any) -> model.Formula:
        formula = object_class()
        depends_on_refs = element.find(NS_AAS + "dependsOnRefs")
        if depends_on_refs is not None:
            for ref in _failsafe_construct_multiple(depends_on_refs.findall(NS_AAS + "reference"),
                                                    cls.construct_reference, cls.failsafe):
                formula.depends_on.add(ref)
        return formula

    @classmethod
    def construct_identifier(cls, element: etree.Element, object_class=model.Identifier, **_kwargs: Any) \
            -> model.Identifier:
        return object_class(
            _get_text_mandatory(element),
            _get_attrib_mandatory_mapped(element, "idType", IDENTIFIER_TYPES_INVERSE)
        )

    @classmethod
    def construct_security(cls, _element: etree.Element, object_class=model.Security, **_kwargs: Any) -> model.Security:
        """
        TODO: this is just a stub implementation
        """
        return object_class()

    @classmethod
    def construct_view(cls, element: etree.Element, object_class=model.View, **_kwargs: Any) -> model.View:
        view = object_class(_child_text_mandatory(element, NS_AAS + "idShort"))
        contained_elements = element.find(NS_AAS + "containedElements")
        if contained_elements is not None:
            for ref in _failsafe_construct_multiple(contained_elements.findall(NS_AAS + "containedElementRef"),
                                                    cls._construct_referable_reference, cls.failsafe):
                view.contained_element.add(ref)
        cls._amend_abstract_attributes(view, element)
        return view

    @classmethod
    def construct_concept_dictionary(cls, element: etree.Element, object_class=model.ConceptDictionary,
                                     **_kwargs: Any) -> model.ConceptDictionary:
        concept_dictionary = object_class(_child_text_mandatory(element, NS_AAS + "idShort"))
        concept_description = element.find(NS_AAS + "conceptDescriptionRefs")
        if concept_description is not None:
            for ref in _failsafe_construct_multiple(concept_description.findall(NS_AAS + "conceptDescriptionRef"),
                                                    cls._construct_concept_description_reference, cls.failsafe):
                concept_dictionary.concept_description.add(ref)
        cls._amend_abstract_attributes(concept_dictionary, element)
        return concept_dictionary

    @classmethod
    def construct_submodel_element(cls, element: etree.Element, **kwargs: Any) -> model.SubmodelElement:
        """
        This function doesn't support the object_class parameter.
        Overwrite each individual SubmodelElement/DataElement constructor function instead.
        """
        # unlike in construct_data_elements, we have to declare a submodel_elements dict without namespace here first
        # because mypy doesn't automatically infer Callable[..., model.SubmodelElement] for the functions, because
        # construct_submodel_element_collection doesn't have the object_class parameter, but object_class_ordered and
        # object_class_unordered
        submodel_elements: Dict[str, Callable[..., model.SubmodelElement]] = {
            "annotatedRelationshipElement": cls.construct_annotated_relationship_element,
            "basicEvent": cls.construct_basic_event,
            "capability": cls.construct_capability,
            "entity": cls.construct_entity,
            "operation": cls.construct_operation,
            "relationshipElement": cls.construct_relationship_element,
            "submodelElementCollection": cls.construct_submodel_element_collection
        }
        submodel_elements = {NS_AAS + k: v for k, v in submodel_elements.items()}
        if element.tag not in submodel_elements:
            return cls.construct_data_element(element, abstract_class_name="SubmodelElement", **kwargs)
        return submodel_elements[element.tag](element, **kwargs)

    @classmethod
    def construct_data_element(cls, element: etree.Element, abstract_class_name: str = "DataElement", **kwargs: Any) \
            -> model.DataElement:
        """
        This function does not support the object_class parameter.
        Overwrite each individual DataElement constructor function instead.
        """
        data_elements: Dict[str, Callable[..., model.DataElement]] = {NS_AAS + k: v for k, v in {
            "blob": cls.construct_blob,
            "file": cls.construct_file,
            "multiLanguageProperty": cls.construct_multi_language_property,
            "property": cls.construct_property,
            "range": cls.construct_range,
            "referenceElement": cls.construct_reference_element,
        }.items()}
        if element.tag not in data_elements:
            raise KeyError(_element_pretty_identifier(element) + f" is not a valid {abstract_class_name}!")
        return data_elements[element.tag](element, **kwargs)

    @classmethod
    def construct_constraint(cls, element: etree.Element, **kwargs: Any) -> model.Constraint:
        """
        This function does not support the object_class parameter.
        Overwrite construct_formula or construct_qualifier instead.
        """
        constraints: Dict[str, Callable[..., model.Constraint]] = {NS_AAS + k: v for k, v in {
            "formula": cls.construct_formula,
            "qualifier": cls.construct_qualifier
        }.items()}
        if element.tag not in constraints:
            raise KeyError(_element_pretty_identifier(element) + " is not a valid Constraint!")
        return constraints[element.tag](element, **kwargs)

    @classmethod
    def construct_operation_variable(cls, element: etree.Element, object_class=model.OperationVariable,
                                     **_kwargs: Any) -> model.OperationVariable:
        value = _get_child_mandatory(element, NS_AAS + "value")
        if len(value) == 0:
            raise KeyError(f"{_element_pretty_identifier(value)} has no submodel element!")
        if len(value) > 1:
            logger.warning(f"{_element_pretty_identifier(value)} has more than one submodel element, "
                           "using the first one...")
        return object_class(
            _failsafe_construct_mandatory(value[0], cls.construct_submodel_element)
        )

    @classmethod
    def construct_annotated_relationship_element(cls, element: etree.Element,
                                                 object_class=model.AnnotatedRelationshipElement, **_kwargs: Any) \
            -> model.AnnotatedRelationshipElement:
        annotated_relationship_element = cls._construct_relationship_element_internal(element, object_class)
        if not cls.stripped:
            for data_element in _get_child_mandatory(element, NS_AAS + "annotations"):
                if len(data_element) == 0:
                    raise KeyError(f"{_element_pretty_identifier(data_element)} has no data element!")
                if len(data_element) > 1:
                    logger.warning(f"{_element_pretty_identifier(data_element)} has more than one data element, "
                                   "which is invalid! Deserializing all data elements anyways...")
                for constructed in _failsafe_construct_multiple(data_element, cls.construct_data_element, cls.failsafe):
                    annotated_relationship_element.annotation.add(constructed)
        return annotated_relationship_element

    @classmethod
    def construct_basic_event(cls, element: etree.Element, object_class=model.BasicEvent, **_kwargs: Any) \
            -> model.BasicEvent:
        basic_event = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            _child_construct_mandatory(element, NS_AAS + "observed", cls._construct_referable_reference),
            kind=_get_modeling_kind(element)
        )
        cls._amend_abstract_attributes(basic_event, element)
        return basic_event

    @classmethod
    def construct_blob(cls, element: etree.Element, object_class=model.Blob, **_kwargs: Any) -> model.Blob:
        blob = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            _child_text_mandatory(element, NS_AAS + "mimeType"),
            kind=_get_modeling_kind(element)
        )
        value = _get_text_or_none(element.find(NS_AAS + "value"))
        if value is not None:
            blob.value = base64.b64decode(value)
        cls._amend_abstract_attributes(blob, element)
        return blob

    @classmethod
    def construct_capability(cls, element: etree.Element, object_class=model.Capability, **_kwargs: Any) \
            -> model.Capability:
        capability = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            kind=_get_modeling_kind(element)
        )
        cls._amend_abstract_attributes(capability, element)
        return capability

    @classmethod
    def construct_entity(cls, element: etree.Element, object_class=model.Entity, **_kwargs: Any) -> model.Entity:
        entity = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            _child_text_mandatory_mapped(element, NS_AAS + "entityType", ENTITY_TYPES_INVERSE),
            # pass the asset to the constructor, because self managed entities need asset references
            asset=_failsafe_construct(element.find(NS_AAS + "assetRef"), cls._construct_asset_reference, cls.failsafe),
            kind=_get_modeling_kind(element)
        )
        if not cls.stripped:
            # TODO: remove wrapping submodelElement, in accordance to future schemas
            # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
            statements = _get_child_mandatory(element, NS_AAS + "statements")
            for submodel_element in _get_all_children_expect_tag(statements, NS_AAS + "submodelElement", cls.failsafe):
                if len(submodel_element) == 0:
                    raise KeyError(f"{_element_pretty_identifier(submodel_element)} has no submodel element!")
                if len(submodel_element) > 1:
                    logger.warning(f"{_element_pretty_identifier(submodel_element)} has more than one submodel element,"
                                   " which is invalid! Deserializing all submodel elements anyways...")
                for constructed in _failsafe_construct_multiple(submodel_element, cls.construct_submodel_element,
                                                                cls.failsafe):
                    entity.statement.add(constructed)
        cls._amend_abstract_attributes(entity, element)
        return entity

    @classmethod
    def construct_file(cls, element: etree.Element, object_class=model.File, **_kwargs: Any) -> model.File:
        file = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            _child_text_mandatory(element, NS_AAS + "mimeType"),
            kind=_get_modeling_kind(element)
        )
        value = _get_text_or_none(element.find(NS_AAS + "value"))
        if value is not None:
            file.value = value
        cls._amend_abstract_attributes(file, element)
        return file

    @classmethod
    def construct_multi_language_property(cls, element: etree.Element, object_class=model.MultiLanguageProperty,
                                          **_kwargs: Any) -> model.MultiLanguageProperty:
        multi_language_property = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            kind=_get_modeling_kind(element)
        )
        value = _failsafe_construct(element.find(NS_AAS + "value"), cls.construct_lang_string_set, cls.failsafe)
        if value is not None:
            multi_language_property.value = value
        value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), cls.construct_reference, cls.failsafe)
        if value_id is not None:
            multi_language_property.value_id = value_id
        cls._amend_abstract_attributes(multi_language_property, element)
        return multi_language_property

    @classmethod
    def construct_operation(cls, element: etree.Element, object_class=model.Operation, **_kwargs: Any) \
            -> model.Operation:
        operation = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            kind=_get_modeling_kind(element)
        )
        for input_variable in _failsafe_construct_multiple(element.findall(NS_AAS + "inputVariable"),
                                                           cls.construct_operation_variable, cls.failsafe):
            operation.input_variable.append(input_variable)
        for output_variable in _failsafe_construct_multiple(element.findall(NS_AAS + "outputVariable"),
                                                            cls.construct_operation_variable, cls.failsafe):
            operation.output_variable.append(output_variable)
        for in_output_variable in _failsafe_construct_multiple(element.findall(NS_AAS + "inoutputVariable"),
                                                               cls.construct_operation_variable, cls.failsafe):
            operation.in_output_variable.append(in_output_variable)
        cls._amend_abstract_attributes(operation, element)
        return operation

    @classmethod
    def construct_property(cls, element: etree.Element, object_class=model.Property, **_kwargs: Any) -> model.Property:
        property_ = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            value_type=_child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES),
            kind=_get_modeling_kind(element)
        )
        value = _get_text_or_none(element.find(NS_AAS + "value"))
        if value is not None:
            property_.value = model.datatypes.from_xsd(value, property_.value_type)
        value_id = _failsafe_construct(element.find(NS_AAS + "valueId"), cls.construct_reference, cls.failsafe)
        if value_id is not None:
            property_.value_id = value_id
        cls._amend_abstract_attributes(property_, element)
        return property_

    @classmethod
    def construct_range(cls, element: etree.Element, object_class=model.Range, **_kwargs: Any) -> model.Range:
        range_ = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            value_type=_child_text_mandatory_mapped(element, NS_AAS + "valueType", model.datatypes.XSD_TYPE_CLASSES),
            kind=_get_modeling_kind(element)
        )
        max_ = _get_text_or_none(element.find(NS_AAS + "max"))
        if max_ is not None:
            range_.max = model.datatypes.from_xsd(max_, range_.value_type)
        min_ = _get_text_or_none(element.find(NS_AAS + "min"))
        if min_ is not None:
            range_.min = model.datatypes.from_xsd(min_, range_.value_type)
        cls._amend_abstract_attributes(range_, element)
        return range_

    @classmethod
    def construct_reference_element(cls, element: etree.Element, object_class=model.ReferenceElement, **_kwargs: Any) \
            -> model.ReferenceElement:
        reference_element = object_class(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            kind=_get_modeling_kind(element)
        )
        value = _failsafe_construct(element.find(NS_AAS + "value"), cls.construct_reference, cls.failsafe)
        if value is not None:
            reference_element.value = value
        cls._amend_abstract_attributes(reference_element, element)
        return reference_element

    @classmethod
    def construct_relationship_element(cls, element: etree.Element, object_class=model.RelationshipElement,
                                       **_kwargs: Any) -> model.RelationshipElement:
        return cls._construct_relationship_element_internal(element, object_class=object_class, **_kwargs)

    @classmethod
    def construct_submodel_element_collection(cls, element: etree.Element,
                                              object_class_ordered=model.SubmodelElementCollectionOrdered,
                                              object_class_unordered=model.SubmodelElementCollectionUnordered,
                                              **_kwargs: Any) -> model.SubmodelElementCollection:
        ordered = _str_to_bool(_child_text_mandatory(element, NS_AAS + "ordered"))
        collection_type = object_class_ordered if ordered else object_class_unordered
        collection = collection_type(
            _child_text_mandatory(element, NS_AAS + "idShort"),
            kind=_get_modeling_kind(element)
        )
        if not cls.stripped:
            value = _get_child_mandatory(element, NS_AAS + "value")
            # TODO: simplify this should our suggestion regarding the XML schema get accepted
            # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
            for submodel_element in _get_all_children_expect_tag(value, NS_AAS + "submodelElement", cls.failsafe):
                if len(submodel_element) == 0:
                    raise KeyError(f"{_element_pretty_identifier(submodel_element)} has no submodel element!")
                if len(submodel_element) > 1:
                    logger.warning(f"{_element_pretty_identifier(submodel_element)} has more than one submodel element,"
                                   " which is invalid! Deserializing all submodel elements anyways...")
                for constructed in _failsafe_construct_multiple(submodel_element, cls.construct_submodel_element,
                                                                cls.failsafe):
                    collection.value.add(constructed)
        cls._amend_abstract_attributes(collection, element)
        return collection

    @classmethod
    def construct_asset_administration_shell(cls, element: etree.Element, object_class=model.AssetAdministrationShell,
                                             **_kwargs: Any) -> model.AssetAdministrationShell:
        aas = object_class(
            _child_construct_mandatory(element, NS_AAS + "assetRef", cls._construct_asset_reference),
            _child_construct_mandatory(element, NS_AAS + "identification", cls.construct_identifier)
        )
        security = _failsafe_construct(element.find(NS_ABAC + "security"), cls.construct_security, cls.failsafe)
        if security is not None:
            aas.security = security
        if not cls.stripped:
            submodels = element.find(NS_AAS + "submodelRefs")
            if submodels is not None:
                for ref in _child_construct_multiple(submodels, NS_AAS + "submodelRef",
                                                     cls._construct_submodel_reference, cls.failsafe):
                    aas.submodel.add(ref)
            views = element.find(NS_AAS + "views")
            if views is not None:
                for view in _child_construct_multiple(views, NS_AAS + "view", cls.construct_view, cls.failsafe):
                    aas.view.add(view)
        concept_dictionaries = element.find(NS_AAS + "conceptDictionaries")
        if concept_dictionaries is not None:
            for cd in _child_construct_multiple(concept_dictionaries, NS_AAS + "conceptDictionary",
                                                cls.construct_concept_dictionary, cls.failsafe):
                aas.concept_dictionary.add(cd)
        derived_from = _failsafe_construct(element.find(NS_AAS + "derivedFrom"),
                                           cls._construct_asset_administration_shell_reference, cls.failsafe)
        if derived_from is not None:
            aas.derived_from = derived_from
        cls._amend_abstract_attributes(aas, element)
        return aas

    @classmethod
    def construct_asset(cls, element: etree.Element, object_class=model.Asset, **_kwargs: Any) -> model.Asset:
        asset = object_class(
            _child_text_mandatory_mapped(element, NS_AAS + "kind", ASSET_KIND_INVERSE),
            _child_construct_mandatory(element, NS_AAS + "identification", cls.construct_identifier)
        )
        asset_identification_model = _failsafe_construct(element.find(NS_AAS + "assetIdentificationModelRef"),
                                                         cls._construct_submodel_reference, cls.failsafe)
        if asset_identification_model is not None:
            asset.asset_identification_model = asset_identification_model
        bill_of_material = _failsafe_construct(element.find(NS_AAS + "billOfMaterialRef"),
                                               cls._construct_submodel_reference, cls.failsafe)
        if bill_of_material is not None:
            asset.bill_of_material = bill_of_material
        cls._amend_abstract_attributes(asset, element)
        return asset

    @classmethod
    def construct_submodel(cls, element: etree.Element, object_class=model.Submodel, **_kwargs: Any) \
            -> model.Submodel:
        submodel = object_class(
            _child_construct_mandatory(element, NS_AAS + "identification", cls.construct_identifier),
            kind=_get_modeling_kind(element)
        )
        if not cls.stripped:
            # TODO: simplify this should our suggestion regarding the XML schema get accepted
            # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
            for submodel_element in _get_all_children_expect_tag(
                    _get_child_mandatory(element, NS_AAS + "submodelElements"), NS_AAS + "submodelElement",
                    cls.failsafe):
                if len(submodel_element) == 0:
                    raise KeyError(f"{_element_pretty_identifier(submodel_element)} has no submodel element!")
                if len(submodel_element) > 1:
                    logger.warning(f"{_element_pretty_identifier(submodel_element)} has more than one submodel element,"
                                   " which is invalid! Deserializing all submodel elements anyways...")
                for constructed in _failsafe_construct_multiple(submodel_element, cls.construct_submodel_element,
                                                                cls.failsafe):
                    submodel.submodel_element.add(constructed)
        cls._amend_abstract_attributes(submodel, element)
        return submodel

    @classmethod
    def construct_value_reference_pair(cls, element: etree.Element, value_format: Optional[model.DataTypeDef] = None,
                                       object_class=model.ValueReferencePair, **_kwargs: Any) \
            -> model.ValueReferencePair:
        if value_format is None:
            raise ValueError("No value format given!")
        return object_class(
            value_format,
            model.datatypes.from_xsd(_child_text_mandatory(element, NS_IEC + "value"), value_format),
            _child_construct_mandatory(element, NS_IEC + "valueId", cls.construct_reference, namespace=NS_IEC)
        )

    @classmethod
    def construct_value_list(cls, element: etree.Element, value_format: Optional[model.DataTypeDef] = None,
                             **_kwargs: Any) -> model.ValueList:
        """
        This function doesn't support the object_class parameter, because ValueList is just a generic type alias.
        """
        return set(
            _child_construct_multiple(element, NS_IEC + "valueReferencePair", cls.construct_value_reference_pair,
                                      cls.failsafe, value_format=value_format)
        )

    @classmethod
    def construct_iec61360_concept_description(cls, element: etree.Element,
                                               identifier: Optional[model.Identifier] = None,
                                               object_class=model.IEC61360ConceptDescription, **_kwargs: Any) \
            -> model.IEC61360ConceptDescription:
        if identifier is None:
            raise ValueError("No identifier given!")
        cd = object_class(
            identifier,
            _child_construct_mandatory(element, NS_IEC + "preferredName", cls.construct_lang_string_set,
                                       namespace=NS_IEC)
        )
        data_type = _get_text_mapped_or_none(element.find(NS_IEC + "dataType"), IEC61360_DATA_TYPES_INVERSE)
        if data_type is not None:
            cd.data_type = data_type
        definition = _failsafe_construct(element.find(NS_IEC + "definition"), cls.construct_lang_string_set,
                                         cls.failsafe, namespace=NS_IEC)
        if definition is not None:
            cd.definition = definition
        short_name = _failsafe_construct(element.find(NS_IEC + "shortName"), cls.construct_lang_string_set,
                                         cls.failsafe, namespace=NS_IEC)
        if short_name is not None:
            cd.short_name = short_name
        unit = _get_text_or_none(element.find(NS_IEC + "unit"))
        if unit is not None:
            cd.unit = unit
        unit_id = _failsafe_construct(element.find(NS_IEC + "unitId"), cls.construct_reference, cls.failsafe,
                                      namespace=NS_IEC)
        if unit_id is not None:
            cd.unit_id = unit_id
        source_of_definition = _get_text_or_none(element.find(NS_IEC + "sourceOfDefinition"))
        if source_of_definition is not None:
            cd.source_of_definition = source_of_definition
        symbol = _get_text_or_none(element.find(NS_IEC + "symbol"))
        if symbol is not None:
            cd.symbol = symbol
        value_format = _get_text_mapped_or_none(element.find(NS_IEC + "valueFormat"),
                                                model.datatypes.XSD_TYPE_CLASSES)
        if value_format is not None:
            cd.value_format = value_format
        value_list = _failsafe_construct(element.find(NS_IEC + "valueList"), cls.construct_value_list, cls.failsafe,
                                         value_format=value_format)
        if value_list is not None:
            cd.value_list = value_list
        value = _get_text_or_none(element.find(NS_IEC + "value"))
        if value is not None and value_format is not None:
            cd.value = model.datatypes.from_xsd(value, value_format)
        value_id = _failsafe_construct(element.find(NS_IEC + "valueId"), cls.construct_reference, cls.failsafe,
                                       namespace=NS_IEC)
        if value_id is not None:
            cd.value_id = value_id
        for level_type_element in element.findall(NS_IEC + "levelType"):
            level_type = _get_text_mapped_or_none(level_type_element, IEC61360_LEVEL_TYPES_INVERSE)
            if level_type is None:
                error_message = f"{_element_pretty_identifier(level_type_element)} has invalid value: " \
                                + str(level_type_element.text)
                if not cls.failsafe:
                    raise ValueError(error_message)
                logger.warning(error_message)
                continue
            cd.level_types.add(level_type)
        return cd

    @classmethod
    def construct_concept_description(cls, element: etree.Element, object_class=model.ConceptDescription,
                                      **_kwargs: Any) -> model.ConceptDescription:
        cd: Optional[model.ConceptDescription] = None
        identifier = _child_construct_mandatory(element, NS_AAS + "identification", cls.construct_identifier)
        # Hack to detect IEC61360ConceptDescriptions, which are represented using dataSpecification according to DotAAS
        dspec_tag = NS_AAS + "embeddedDataSpecification"
        dspecs = element.findall(dspec_tag)
        if len(dspecs) > 1:
            logger.warning(f"{_element_pretty_identifier(element)} has more than one "
                           f"{_tag_replace_namespace(dspec_tag, element.nsmap)}. This model currently supports only one"
                           f" per {_tag_replace_namespace(element.tag, element.nsmap)}!")
        if len(dspecs) > 0:
            dspec = dspecs[0]
            dspec_content = dspec.find(NS_AAS + "dataSpecificationContent")
            if dspec_content is not None:
                dspec_ref = _failsafe_construct(dspec.find(NS_AAS + "dataSpecification"), cls.construct_reference,
                                                cls.failsafe)
                if dspec_ref is not None and len(dspec_ref.key) > 0 and dspec_ref.key[0].value == \
                        "http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0":
                    cd = _failsafe_construct(dspec_content.find(NS_AAS + "dataSpecificationIEC61360"),
                                             cls.construct_iec61360_concept_description, cls.failsafe,
                                             identifier=identifier)
        if cd is None:
            cd = object_class(identifier)
        for ref in _failsafe_construct_multiple(element.findall(NS_AAS + "isCaseOf"), cls.construct_reference,
                                                cls.failsafe):
            cd.is_case_of.add(ref)
        cls._amend_abstract_attributes(cd, element)
        return cd


class StrictAASFromXmlDecoder(AASFromXmlDecoder):
    """
    Non-failsafe XML decoder. Encountered errors won't be caught and abort parsing.
    """
    failsafe = False


class StrippedAASFromXmlDecoder(AASFromXmlDecoder):
    """
    Decoder for stripped XML elements. Used in the HTTP adapter.
    """
    stripped = True


class StrictStrippedAASFromXmlDecoder(StrictAASFromXmlDecoder, StrippedAASFromXmlDecoder):
    """
    Non-failsafe decoder for stripped XML elements.
    """
    pass


def _parse_xml_document(file: IO, failsafe: bool = True, **parser_kwargs: Any) -> Optional[etree.Element]:
    """
    Parse an XML document into an element tree

    :param file: A filename or file-like object to read the XML-serialized data from
    :param failsafe: If True, the file is parsed in a failsafe way: Instead of raising an Exception if the document
                     is malformed, parsing is aborted, an error is logged and None is returned
    :param parser_kwargs: Keyword arguments passed to the XMLParser constructor
    :return: The root element of the element tree
    """

    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True, **parser_kwargs)

    try:
        return etree.parse(file, parser).getroot()
    except etree.XMLSyntaxError as e:
        if failsafe:
            logger.error(e)
            return None
        raise e


def _select_decoder(failsafe: bool, stripped: bool, decoder: Optional[Type[AASFromXmlDecoder]]) \
        -> Type[AASFromXmlDecoder]:
    """
    Returns the correct decoder based on the parameters failsafe and stripped. If a decoder class is given, failsafe
    and stripped are ignored.

    :param failsafe: If true, a failsafe decoder is selected. Ignored if a decoder class is specified.
    :param stripped: If true, a decoder for parsing stripped XML elements is selected. Ignored if a decoder class is
                     specified.
    :param decoder: Is returned, if specified.
    :return: A AASFromXmlDecoder (sub)class.
    """
    if decoder is not None:
        return decoder
    if failsafe:
        if stripped:
            return StrippedAASFromXmlDecoder
        return AASFromXmlDecoder
    else:
        if stripped:
            return StrictStrippedAASFromXmlDecoder
        return StrictAASFromXmlDecoder


@enum.unique
class XMLConstructables(enum.Enum):
    """
    This enum is used to specify which type to construct in read_aas_xml_element().
    """
    KEY = enum.auto()
    REFERENCE = enum.auto()
    AAS_REFERENCE = enum.auto()
    ADMINISTRATIVE_INFORMATION = enum.auto()
    QUALIFIER = enum.auto()
    FORMULA = enum.auto()
    IDENTIFIER = enum.auto()
    SECURITY = enum.auto()
    VIEW = enum.auto()
    CONCEPT_DICTIONARY = enum.auto()
    OPERATION_VARIABLE = enum.auto()
    ANNOTATED_RELATIONSHIP_ELEMENT = enum.auto()
    BASIC_EVENT = enum.auto()
    BLOB = enum.auto()
    CAPABILITY = enum.auto()
    ENTITY = enum.auto()
    FILE = enum.auto()
    MULTI_LANGUAGE_PROPERTY = enum.auto()
    OPERATION = enum.auto()
    PROPERTY = enum.auto()
    RANGE = enum.auto()
    REFERENCE_ELEMENT = enum.auto()
    RELATIONSHIP_ELEMENT = enum.auto()
    SUBMODEL_ELEMENT_COLLECTION = enum.auto()
    ASSET_ADMINISTRATION_SHELL = enum.auto()
    ASSET = enum.auto()
    SUBMODEL = enum.auto()
    VALUE_REFERENCE_PAIR = enum.auto()
    IEC61360_CONCEPT_DESCRIPTION = enum.auto()
    CONCEPT_DESCRIPTION = enum.auto()
    CONSTRAINT = enum.auto()
    DATA_ELEMENT = enum.auto()
    SUBMODEL_ELEMENT = enum.auto()
    VALUE_LIST = enum.auto()
    LANG_STRING_SET = enum.auto()


def read_aas_xml_element(file: IO, construct: XMLConstructables, failsafe: bool = True, stripped: bool = False,
                         decoder: Optional[Type[AASFromXmlDecoder]] = None, **constructor_kwargs) -> Optional[object]:
    """
    Construct a single object from an XML string. The namespaces have to be declared on the object itself, since there
    is no surrounding aasenv element.

    :param file: A filename or file-like object to read the XML-serialized data from
    :param construct: A member of the enum :class:`~.XMLConstructables`, specifying which type to construct.
    :param failsafe: If true, the document is parsed in a failsafe way: missing attributes and elements are logged
                     instead of causing exceptions. Defect objects are skipped.
                     This parameter is ignored if a decoder class is specified.
    :param stripped: If true, stripped XML elements are parsed.
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if a decoder class is specified.
    :param decoder: The decoder class used to decode the XML elements
    :param constructor_kwargs: Keyword arguments passed to the constructor function
    :return: The constructed object or None, if an error occurred in failsafe mode.
    """
    decoder_ = _select_decoder(failsafe, stripped, decoder)
    constructor: Callable[..., object]

    if construct == XMLConstructables.KEY:
        constructor = decoder_.construct_key
    elif construct == XMLConstructables.REFERENCE:
        constructor = decoder_.construct_reference
    elif construct == XMLConstructables.AAS_REFERENCE:
        constructor = decoder_.construct_aas_reference
    elif construct == XMLConstructables.ADMINISTRATIVE_INFORMATION:
        constructor = decoder_.construct_administrative_information
    elif construct == XMLConstructables.QUALIFIER:
        constructor = decoder_.construct_qualifier
    elif construct == XMLConstructables.FORMULA:
        constructor = decoder_.construct_formula
    elif construct == XMLConstructables.IDENTIFIER:
        constructor = decoder_.construct_identifier
    elif construct == XMLConstructables.SECURITY:
        constructor = decoder_.construct_security
    elif construct == XMLConstructables.VIEW:
        constructor = decoder_.construct_view
    elif construct == XMLConstructables.CONCEPT_DICTIONARY:
        constructor = decoder_.construct_concept_dictionary
    elif construct == XMLConstructables.OPERATION_VARIABLE:
        constructor = decoder_.construct_operation_variable
    elif construct == XMLConstructables.ANNOTATED_RELATIONSHIP_ELEMENT:
        constructor = decoder_.construct_annotated_relationship_element
    elif construct == XMLConstructables.BASIC_EVENT:
        constructor = decoder_.construct_basic_event
    elif construct == XMLConstructables.BLOB:
        constructor = decoder_.construct_blob
    elif construct == XMLConstructables.CAPABILITY:
        constructor = decoder_.construct_capability
    elif construct == XMLConstructables.ENTITY:
        constructor = decoder_.construct_entity
    elif construct == XMLConstructables.FILE:
        constructor = decoder_.construct_file
    elif construct == XMLConstructables.MULTI_LANGUAGE_PROPERTY:
        constructor = decoder_.construct_multi_language_property
    elif construct == XMLConstructables.OPERATION:
        constructor = decoder_.construct_operation
    elif construct == XMLConstructables.PROPERTY:
        constructor = decoder_.construct_property
    elif construct == XMLConstructables.RANGE:
        constructor = decoder_.construct_range
    elif construct == XMLConstructables.REFERENCE_ELEMENT:
        constructor = decoder_.construct_reference_element
    elif construct == XMLConstructables.RELATIONSHIP_ELEMENT:
        constructor = decoder_.construct_relationship_element
    elif construct == XMLConstructables.SUBMODEL_ELEMENT_COLLECTION:
        constructor = decoder_.construct_submodel_element_collection
    elif construct == XMLConstructables.ASSET_ADMINISTRATION_SHELL:
        constructor = decoder_.construct_asset_administration_shell
    elif construct == XMLConstructables.ASSET:
        constructor = decoder_.construct_asset
    elif construct == XMLConstructables.SUBMODEL:
        constructor = decoder_.construct_submodel
    elif construct == XMLConstructables.VALUE_REFERENCE_PAIR:
        constructor = decoder_.construct_value_reference_pair
    elif construct == XMLConstructables.IEC61360_CONCEPT_DESCRIPTION:
        constructor = decoder_.construct_iec61360_concept_description
    elif construct == XMLConstructables.CONCEPT_DESCRIPTION:
        constructor = decoder_.construct_concept_description
    # the following constructors decide which constructor to call based on the elements tag
    elif construct == XMLConstructables.CONSTRAINT:
        constructor = decoder_.construct_constraint
    elif construct == XMLConstructables.DATA_ELEMENT:
        constructor = decoder_.construct_data_element
    elif construct == XMLConstructables.SUBMODEL_ELEMENT:
        constructor = decoder_.construct_submodel_element
    # type aliases
    elif construct == XMLConstructables.VALUE_LIST:
        constructor = decoder_.construct_value_list
    elif construct == XMLConstructables.LANG_STRING_SET:
        constructor = decoder_.construct_lang_string_set
    else:
        raise ValueError(f"{construct.name} cannot be constructed!")

    element = _parse_xml_document(file, failsafe=decoder_.failsafe)
    return _failsafe_construct(element, constructor, decoder_.failsafe, **constructor_kwargs)


def read_aas_xml_file_into(object_store: model.AbstractObjectStore[model.Identifiable], file: IO,
                           replace_existing: bool = False, ignore_existing: bool = False, failsafe: bool = True,
                           stripped: bool = False, decoder: Optional[Type[AASFromXmlDecoder]] = None,
                           **parser_kwargs: Any) -> Set[model.Identifier]:
    """
    Read an Asset Administration Shell XML file according to 'Details of the Asset Administration Shell', chapter 5.4
    into a given :class:`ObjectStore <aas.model.provider.AbstractObjectStore>`.

    :param object_store: The :class:`ObjectStore <aas.model.provider.AbstractObjectStore>` in which the
                         :class:`~aas.model.base.Identifiable` objects should be stored
    :param file: A filename or file-like object to read the XML-serialized data from
    :param replace_existing: Whether to replace existing objects with the same identifier in the object store or not
    :param ignore_existing: Whether to ignore existing objects (e.g. log a message) or raise an error.
                            This parameter is ignored if replace_existing is True.
    :param failsafe: If `True`, the document is parsed in a failsafe way: missing attributes and elements are logged
                     instead of causing exceptions. Defect objects are skipped.
                     This parameter is ignored if a decoder class is specified.
    :param stripped: If `True`, stripped XML elements are parsed.
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if a decoder class is specified.
    :param decoder: The decoder class used to decode the XML elements
    :param parser_kwargs: Keyword arguments passed to the XMLParser constructor
    :return: A set of :class:`Identifiers <aas.model.base.Identifier>` that were added to object_store
    """
    ret: Set[model.Identifier] = set()

    decoder_ = _select_decoder(failsafe, stripped, decoder)

    element_constructors: Dict[str, Callable[..., model.Identifiable]] = {
        "assetAdministrationShell": decoder_.construct_asset_administration_shell,
        "asset": decoder_.construct_asset,
        "submodel": decoder_.construct_submodel,
        "conceptDescription": decoder_.construct_concept_description
    }

    element_constructors = {NS_AAS + k: v for k, v in element_constructors.items()}

    root = _parse_xml_document(file, failsafe=decoder_.failsafe, **parser_kwargs)

    if root is None:
        return ret

    # Add AAS objects to ObjectStore
    for list_ in root:
        element_tag = list_.tag[:-1]
        if list_.tag[-1] != "s" or element_tag not in element_constructors:
            error_message = f"Unexpected top-level list {_element_pretty_identifier(list_)}!"
            if not decoder_.failsafe:
                raise TypeError(error_message)
            logger.warning(error_message)
            continue
        constructor = element_constructors[element_tag]
        for element in _child_construct_multiple(list_, element_tag, constructor, decoder_.failsafe):
            if element.identification in ret:
                error_message = f"{element} has a duplicate identifier already parsed in the document!"
                if not decoder_.failsafe:
                    raise KeyError(error_message)
                logger.error(error_message + " skipping it...")
                continue
            existing_element = object_store.get(element.identification)
            if existing_element is not None:
                if not replace_existing:
                    error_message = f"object with identifier {element.identification} already exists " \
                                    f"in the object store: {existing_element}!"
                    if not ignore_existing:
                        raise KeyError(error_message + f" failed to insert {element}!")
                    logger.info(error_message + f" skipping insertion of {element}...")
                    continue
                object_store.discard(existing_element)
            object_store.add(element)
            ret.add(element.identification)
    return ret


def read_aas_xml_file(file: IO, **kwargs: Any) -> model.DictObjectStore[model.Identifiable]:
    """
    A wrapper of :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_file_into`, that reads all objects in an
    empty :class:`~aas.model.provider.DictObjectStore`. This function supports
    the same keyword arguments as :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_file_into`.

    :param file: A filename or file-like object to read the XML-serialized data from
    :param kwargs: Keyword arguments passed to :meth:`~aas.adapter.xml.xml_deserialization.read_aas_xml_file_into`
    :return: A :class:`~aas.model.provider.DictObjectStore` containing all AAS objects from the XML file
    """
    object_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    read_aas_xml_file_into(object_store, file, **kwargs)
    return object_store
