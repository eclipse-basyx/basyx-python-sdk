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
Module for deserializing Asset Administration Shell data from the official JSON format

The module provides an custom JSONDecoder classes `AASFromJsonDecoder` and `StrictAASFromJsonDecoder` to be used with
the Python standard `json` module. They contain a custom `object_hook` function to detect encoded AAS objects within the
JSON data and convert them to PyAAS objects while parsing. Additionally, there's the `read_json_aas_file()` function,
that takes a complete AAS JSON file, reads its contents and returns the contained AAS objects as DictObjectStore.

This job is performed in a bottom-up approach: The `object_hook()` function gets called for every parsed JSON object
(as dict) and checks for existence of the `modelType` attribute. If it is present, the `AAS_CLASS_PARSERS` dict defines,
which of the constructor functions in this module is to be used for converting the dict into an object. Embedded
objects that should have a `modelType` themselves are expected to be converted already. Other embedded objects are
converted using a number of helper constructor functions.
"""
import base64
import json
import logging
import pprint
from typing import Dict, Callable, TypeVar, Type, List, IO

from ... import model
from .json_serialization import MODELING_KIND, ASSET_KIND, KEY_ELEMENTS, KEY_TYPES, IDENTIFIER_TYPES, ENTITY_TYPES

logger = logging.getLogger(__name__)

MODELING_KIND_INVERSE: Dict[str, model.ModelingKind] = {v: k for k, v in MODELING_KIND.items()}
ASSET_KIND_INVERSE: Dict[str, model.AssetKind] = {v: k for k, v in ASSET_KIND.items()}
KEY_ELEMENTS_INVERSE: Dict[str, model.KeyElements] = {v: k for k, v in KEY_ELEMENTS.items()}
KEY_TYPES_INVERSE: Dict[str, model.KeyType] = {v: k for k, v in KEY_TYPES.items()}
IDENTIFIER_TYPES_INVERSE: Dict[str, model.IdentifierType] = {v: k for k, v in IDENTIFIER_TYPES.items()}
ENTITY_TYPES_INVERSE: Dict[str, model.EntityType] = {v: k for k, v in ENTITY_TYPES.items()}
KEY_ELEMENTS_CLASSES_INVERSE: Dict[model.KeyElements, type] = {v: k for k, v in model.KEY_ELEMENTS_CLASSES.items()}


# #############################################################################
# Helper functions (for simplifying implementation of constructor functions)
# #############################################################################

T = TypeVar('T')


def _get_ts(dct: Dict[str, object], key: str, type_: Type[T]) -> T:
    """
    Helper function for getting an item from a (str→object) dict in a typesafe way.

    The type of the object is checked at runtime and a TypeError is raised, if the object has not the expected type.

    :param dct: The dict
    :param key: The key of the item to retreive
    :param type_: The expected type of the item
    :return: The item
    :raises TypeError: If the item has an unexpected type
    :raises KeyError: If the key is not found in the dict (just as usual)
    """
    val = dct[key]
    if not isinstance(val, type_):
        raise TypeError("Dict entry {} has unexpected type {}".format(key, type(val).__name__))
    return val


def _expect_type(object_: object, type_: Type, context: str, failsafe: bool) -> bool:
    """
    Helper function to check type of an embedded object.

    This function may be used in any constructor function for an AAS object that expects to find already constructed
    AAS objects of a certain type within its data dict. In this case, we want to ensure that the object has this kind
    and raise a TypeError if not. In failsafe mode, we want to log the error and prevent the object from being added
    to the parent object. A typical use of this function would look like this:

      if _expect_type(element, model.SubmodelElement, str(submodel), failsafe):
          submodel.submodel_element.add(element)

    :param object_: The object to by type-checked
    :param type_: The expected type
    :param context: A string to add to the exception message / log message, that describes the context in that the
                    object has been found
    :param failsafe: Log error and return false instead of rasing a TypeError
    :return: True if the
    :raises TypeError: If the object is not of the expected type and the failsafe mode is not active
    """
    if isinstance(object_, type_):
        return True
    if failsafe:
        logger.error("Expected a %s in %s, but found %s", type_.__name__, context, repr(object_))
    else:
        raise TypeError("Expected a %s in %s, but found %s" % (type_.__name__, context, repr(object_)))
    return False


def _amend_abstract_attributes(obj: object, dct: Dict[str, object], failsafe: bool) -> None:
    """
    Helper function to add the optional attributes of the abstract meta classes Referable, Identifiable,
    HasDataSpecification, HasSemantics, HasKind and Qualifiable to an object inheriting from any of these classes, if
    present

    :param obj: The object to amend its attributes
    :param dct: The object's dict representation from JSON
    """
    if isinstance(obj, model.Referable):
        if 'category' in dct:
            obj.category = _get_ts(dct, 'category', str)
        if 'description' in dct:
            obj.description = _construct_lang_string_set(_get_ts(dct, 'description', list), failsafe)
    if isinstance(obj, model.Identifiable):
        if 'idShort' in dct:
            obj.id_short = _get_ts(dct, 'idShort', str)
        if 'administration' in dct:
            obj.administration = _construct_administrative_information(_get_ts(dct, 'administration', dict))
    if isinstance(obj, model.HasDataSpecification):
        if 'embeddedDataSpecification' in dct:
            for data_spec_data in _get_ts(dct, 'embeddedDataSpecification', list):
                try:
                    obj.data_specification.add(_construct_reference(data_spec_data))
                except (KeyError, TypeError) as e:
                    error_message = \
                        "Error while trying to convert JSON object into DataSpecification for {}: {}".format(
                            obj, pprint.pformat(dct, depth=2, width=2**14, compact=True))
                    if failsafe:
                        logger.error(error_message, exc_info=e)
                    else:
                        raise type(e)(error_message) from e
    if isinstance(obj, model.HasSemantics):
        if 'semanticId' in dct:
            obj.semantic_id = _construct_reference(_get_ts(dct, 'semanticId', dict))
    # `HasKind` provides only mandatory, immutable attributes; so we cannot do anything here, after object creation.
    # However, the `_get_kind()` function may assist by retreiving them from the JSON object
    if isinstance(obj, model.Qualifiable):
        if 'qualifiers' in dct:
            for constraint in _get_ts(dct, 'qualifiers', list):
                if _expect_type(constraint, model.Constraint, str(obj), failsafe):
                    obj.qualifier.add(constraint)


def _get_kind(dct: Dict[str, object]) -> model.ModelingKind:
    """
    Helper function to get the kind of an HasKind object from its JSON representation.

    :param dct: The object's dict representation from JSON
    :return: The object's `kind` value
    """
    return MODELING_KIND_INVERSE[_get_ts(dct, "kind", str)] if 'kind' in dct else model.ModelingKind.INSTANCE


# #############################################################################
# Helper constructor functions starting from here
# #############################################################################

def _construct_key(dct: Dict[str, object]) -> model.Key:
    return model.Key(type_=KEY_ELEMENTS_INVERSE[_get_ts(dct, 'type', str)],
                     id_type=KEY_TYPES_INVERSE[_get_ts(dct, 'idType', str)],
                     value=_get_ts(dct, 'value', str),
                     local=_get_ts(dct, 'local', bool))


def _construct_reference(dct: Dict[str, object]) -> model.Reference:
    keys = [_construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
    return model.Reference(keys)


def _construct_aas_reference(dct: Dict[str, object], type_: Type[T]) -> model.AASReference:
    keys = [_construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
    if keys and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type_, type(None)), type_):
        logger.warning("type %s of last key of reference to %s does not match reference type %s",
                       keys[-1].type_.name, " / ".join(str(k) for k in keys), type_.__name__)
    return model.AASReference(keys, type_)


def _construct_identifier(dct: Dict[str, object]) -> model.Identifier:
    return model.Identifier(_get_ts(dct, 'id', str),
                            IDENTIFIER_TYPES_INVERSE[_get_ts(dct, 'idType', str)])


def _construct_administrative_information(dct: Dict[str, object]) -> model.AdministrativeInformation:
    ret = model.AdministrativeInformation()
    if 'version' in dct:
        ret.version = _get_ts(dct, 'version', str)
        if 'revision' in dct:
            ret.revision = _get_ts(dct, 'revision', str)
    elif 'revision' in dct:
        logger.warning("Ignoring 'revision' attribute of AdministrativeInformation object due to missing 'version'")
    return ret


def _construct_security(_dct: Dict[str, object]) -> model.Security:
    return model.Security()


def _construct_lang_string_set(lst: List[Dict[str, object]], failsafe: bool) -> model.LangStringSet:
    ret = {}
    for desc in lst:
        try:
            ret[_get_ts(desc, 'language', str)] = _get_ts(desc, 'text', str)
        except (KeyError, TypeError) as e:
            error_message = "Error while trying to convert JSON object into LangString: {}".format(
                pprint.pformat(lst, depth=2, width=2**14, compact=True))
            if failsafe:
                logger.error(error_message, exc_info=e)
            else:
                raise type(e)(error_message) from e
    return ret


# #############################################################################
# Constructor Functions (for classes with `modelType`) starting from here
# #############################################################################

def construct_asset(dct: Dict[str, object], failsafe: bool) -> model.Asset:
    ret = model.Asset(kind=ASSET_KIND_INVERSE[_get_ts(dct, 'kind', str)],
                      identification=_construct_identifier(_get_ts(dct, "identification", dict)))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_asset_administration_shell(dct: Dict[str, object], failsafe: bool) -> model.AssetAdministrationShell:
    ret = model.AssetAdministrationShell(
        asset=_construct_aas_reference(_get_ts(dct, 'asset', dict), model.Asset),
        identification=_construct_identifier(_get_ts(dct, 'identification', dict)))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'submodels' in dct:
        for sm_data in _get_ts(dct, 'submodels', list):
            ret.submodel_.add(_construct_aas_reference(sm_data, model.Submodel))
    if 'views' in dct:
        for view in _get_ts(dct, 'views', list):
            if _expect_type(view, model.View, str(ret), failsafe):
                ret.view.add(view)
    if 'conceptDictionaries' in dct:
        for concept_dictionary in _get_ts(dct, 'conceptDictionaries', list):
            if _expect_type(concept_dictionary, model.ConceptDictionary, str(ret), failsafe):
                ret.concept_dictionary.add(concept_dictionary)
    if 'security' in dct:
        ret.security_ = _construct_security(_get_ts(dct, 'security', dict))
    return ret


def construct_view(dct: Dict[str, object], failsafe: bool) -> model.View:
    ret = model.View(_get_ts(dct, 'idShort', str))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_concept_description(dct: Dict[str, object], failsafe: bool) -> model.ConceptDescription:
    ret = model.ConceptDescription(identification=_construct_identifier(_get_ts(dct, 'identification', dict)))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'isCaseOf' in dct:
        for case_data in _get_ts(dct, "isCaseOf", list):
            ret.is_case_of.add(_construct_reference(case_data))
    return ret


def construct_concept_dictionary(dct: Dict[str, object], failsafe: bool) -> model.ConceptDictionary:
    ret = model.ConceptDictionary(_get_ts(dct, "idShort", str))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'conceptDescriptions' in dct:
        for desc_data in _get_ts(dct, "conceptDescriptions", list):
            ret.concept_description.add(_construct_aas_reference(desc_data, model.ConceptDescription))
    return ret


def construct_entity(dct: Dict[str, object], failsafe: bool) -> model.Entity:
    ret = model.Entity(id_short=_get_ts(dct, "idShort", str),
                       entity_type=ENTITY_TYPES_INVERSE[_get_ts(dct, "entityType", str)],
                       asset=(_construct_aas_reference(_get_ts(dct, 'asset', dict), model.Asset)
                              if 'asset' in dct else None),
                       kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'statements' in dct:
        for element in _get_ts(dct, "statements", list):
            if _expect_type(element, model.SubmodelElement, str(ret), failsafe):
                ret.statement.add(element)
    return ret


def construct_qualifier(dct: Dict[str, object], failsafe: bool) -> model.Qualifier:
    ret = model.Qualifier(type_=_get_ts(dct, 'type', str),
                          value_type=_get_ts(dct, 'valueType', str))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct:
        ret.value = _get_ts(dct, 'value', str)
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'valueId', dict))
    return ret


def construct_formula(dct: Dict[str, object], failsafe: bool) -> model.Formula:
    ret = model.Formula()
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'dependsOn' in dct:
        for dependency_data in _get_ts(dct, 'dependsOn', list):
            try:
                ret.depends_on.add(_construct_reference(dependency_data))
            except (KeyError, TypeError) as e:
                error_message = \
                    "Error while trying to convert JSON object into dependency Reference for {}: {}".format(
                        ret, pprint.pformat(dct, depth=2, width=2 ** 14, compact=True))
                if failsafe:
                    logger.error(error_message, exc_info=e)
                else:
                    raise type(e)(error_message) from e
    return ret


def construct_submodel(dct: Dict[str, object], failsafe: bool) -> model.Submodel:
    ret = model.Submodel(identification=_construct_identifier(_get_ts(dct, 'identification', dict)),
                         kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'submodelElements' in dct:
        for element in _get_ts(dct, "submodelElements", list):
            if _expect_type(element, model.SubmodelElement, str(ret), failsafe):
                ret.submodel_element.add(element)
    return ret


def construct_capability(dct: Dict[str, object], failsafe: bool) -> model.Capability:
    ret = model.Capability(id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_basic_event(dct: Dict[str, object], failsafe: bool) -> model.BasicEvent:
    ret = model.BasicEvent(id_short=_get_ts(dct, "idShort", str),
                           observed=_construct_aas_reference(_get_ts(dct, 'observed', dict), model.Referable),
                           kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_operation(dct: Dict[str, object], failsafe: bool) -> model.Operation:
    ret = model.Operation(_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'inputVariable' in dct:
        for variable in _get_ts(dct, "inputVariable", list):
            if _expect_type(variable, model.OperationVariable, "{}.inputVariable".format(ret), failsafe):
                ret.input_variable.add(variable)
    if 'outputVariable' in dct:
        for variable in _get_ts(dct, "outputVariable", list):
            if _expect_type(variable, model.OperationVariable, "{}.outputVariable".format(ret), failsafe):
                ret.output_variable.add(variable)
    if 'inoutputVariable' in dct:
        for variable in _get_ts(dct, "inoutputVariable", list):
            if _expect_type(variable, model.OperationVariable, "{}.inoutputVariable".format(ret), failsafe):
                ret.in_output_variable.add(variable)
    return ret


def construct_operation_variable(dct: Dict[str, object], failsafe: bool) -> model.OperationVariable:
    ret = model.OperationVariable(id_short=_get_ts(dct, "idShort", str),
                                  value=_get_ts(dct, 'value', model.SubmodelElement),
                                  kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_relationship_element(dct: Dict[str, object], failsafe: bool) -> model.RelationshipElement:
    ret = model.RelationshipElement(id_short=_get_ts(dct, "idShort", str),
                                    first=_construct_aas_reference(_get_ts(dct, 'first', dict), model.Referable),
                                    second=_construct_aas_reference(_get_ts(dct, 'second', dict), model.Referable),
                                    kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    return ret


def construct_annotated_relationship_element(dct: Dict[str, object], failsafe: bool)\
        -> model.AnnotatedRelationshipElement:
    ret = model.AnnotatedRelationshipElement(
        id_short=_get_ts(dct, "idShort", str),
        first=_construct_aas_reference(_get_ts(dct, 'first', dict), model.Referable),
        second=_construct_aas_reference(_get_ts(dct, 'second', dict), model.Referable),
        kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'annotation' in dct:
        for annotation_data in _get_ts(dct, 'annotation', list):
            try:
                ret.annotation.add(_construct_aas_reference(annotation_data, model.DataElement))
            except (KeyError, TypeError) as e:
                error_message = \
                    "Error while trying to convert JSON object into annotation Reference for {}: {}".format(
                        ret, pprint.pformat(dct, depth=2, width=2**14, compact=True))
                if failsafe:
                    logger.error(error_message, exc_info=e)
                else:
                    raise type(e)(error_message) from e
    return ret


def construct_submodel_element_collection(dct: Dict[str, object], failsafe: bool) -> model.SubmodelElementCollection:
    ret: model.SubmodelElementCollection
    if 'ordered' in dct and _get_ts(dct, 'ordered', bool):
        ret = model.SubmodelElementCollectionOrdered(
            id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    else:
        ret = model.SubmodelElementCollectionUnordered(
            id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct:
        for element in _get_ts(dct, "value", list):
            if _expect_type(element, model.SubmodelElement, str(ret), failsafe):
                ret.value.add(element)
    return ret


def construct_blob(dct: Dict[str, object], failsafe: bool) -> model.Blob:
    ret = model.Blob(id_short=_get_ts(dct, "idShort", str),
                     mime_type=_get_ts(dct, "mimeType", str),
                     kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct:
        ret.value = base64.b64decode(_get_ts(dct, 'value', str))
    return ret


def construct_file(dct: Dict[str, object], failsafe: bool) -> model.File:
    ret = model.File(id_short=_get_ts(dct, "idShort", str),
                     value=None,
                     mime_type=_get_ts(dct, "mimeType", str),
                     kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct and dct['value'] is not None:
        ret.value = _get_ts(dct, 'value', str)
    return ret


def construct_multi_language_property(dct: Dict[str, object], failsafe: bool) -> model.MultiLanguageProperty:
    ret = model.MultiLanguageProperty(id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct and dct['value'] is not None:
        ret.value = _construct_lang_string_set(_get_ts(dct, 'value', list), failsafe)
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'valueId', dict))
    return ret


def construct_property(dct: Dict[str, object], failsafe: bool) -> model.Property:
    ret = model.Property(id_short=_get_ts(dct, "idShort", str),
                         value_type=_get_ts(dct, 'valueType', str),
                         kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct and dct['value'] is not None:
        ret.value = _get_ts(dct, 'value', str)
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'valueId', dict))
    return ret


def construct_range(dct: Dict[str, object], failsafe: bool) -> model.Range:
    ret = model.Range(id_short=_get_ts(dct, "idShort", str),
                      value_type=_get_ts(dct, 'valueType', str),
                      kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'min' in dct and dct['min'] is not None:
        ret.min_ = _get_ts(dct, 'min', str)
    if 'max' in dct and dct['max'] is not None:
        ret.max_ = _get_ts(dct, 'max', str)
    return ret


def construct_reference_element(dct: Dict[str, object], failsafe: bool) -> model.ReferenceElement:
    ret = model.ReferenceElement(id_short=_get_ts(dct, "idShort", str),
                                 value=None,
                                 kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct, failsafe)
    if 'value' in dct and dct['value'] is not None:
        ret.value = _construct_aas_reference(_get_ts(dct, 'value', dict), model.Referable)
    return ret


# The following dict specifies a constructor function for all AAS classes that may be identified using the `modelType`
# attribute in their JSON representation. Each of those constructor functions takes the JSON representation of an object
# and tries to construct a Python object from it. Embedded objects that have a modelType themselves are expected to be
# converted to the correct PythonType already. Additionally, each function takes a bool parameter `failsafe`, which
# indicates weather to log errors and skip defective objects instead of raising an Exception.
AAS_CLASS_PARSERS: Dict[str, Callable[[Dict[str, object], bool], object]] = {
    'Asset': construct_asset,
    'AssetAdministrationShell': construct_asset_administration_shell,
    'View': construct_view,
    'ConceptDescription': construct_concept_description,
    'Qualifier': construct_qualifier,
    'Formula': construct_formula,
    'Submodel': construct_submodel,
    'ConceptDictionary': construct_concept_dictionary,
    'Capability': construct_capability,
    'Entity': construct_entity,
    'BasicEvent': construct_basic_event,
    'Operation': construct_operation,
    'OperationVariable': construct_operation_variable,
    'RelationshipElement': construct_relationship_element,
    'AnnotatedRelationshipElement': construct_annotated_relationship_element,
    'SubmodelElementCollection': construct_submodel_element_collection,
    'Blob': construct_blob,
    'File': construct_file,
    'MultiLanguageProperty': construct_multi_language_property,
    'Property': construct_property,
    'Range': construct_range,
    'ReferenceElement': construct_reference_element,
}


class AASFromJsonDecoder(json.JSONDecoder):
    """
    Custom JSONDecoder class to use the `json` module for deserializing Asset Administration Shell data from the
    official JSON format

    It contains a custom `object_hook` function to detect encoded AAS objects within the JSON data and convert them to
    PyAAS objects while parsing.

    :cvar failsafe: If True (the default), don't raise Exceptions for missing attributes and wrong types, but instead
                    skip defective objects and use logger to output warnings. Use StrictAASFromJsonDecoder for a
                    non-failsafe version.
    """
    failsafe = True

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @classmethod
    def object_hook(cls, dct: Dict[str, object]) -> object:
        # Check if JSON object seems to be a deserializable AAS object (i.e. it has a modelType)
        if 'modelType' not in dct:
            return dct

        # Get modelType and constructor function
        if not isinstance(dct['modelType'], dict) or 'name' not in dct['modelType']:
            logger.warning("JSON object has unexpected format of modelType: %s", dct['modelType'])
            return dct
        model_type = dct['modelType']['name']
        if model_type not in AAS_CLASS_PARSERS:
            if not cls.failsafe:
                raise TypeError("Found JSON object with modelType=\"%s\", which is not a known AAS class" % model_type)
            logger.error("Found JSON object with modelType=\"%s\", which is not a known AAS class", model_type)
            return dct

        # Use constructor function to transform JSON representation into PyAAS model object
        try:
            return AAS_CLASS_PARSERS[model_type](dct, cls.failsafe)
        except (KeyError, TypeError) as e:
            error_message = "Error while trying to convert JSON object into {}: {}".format(
                model_type, pprint.pformat(dct, depth=2, width=2**14, compact=True))
            if cls.failsafe:
                logger.error(error_message, exc_info=e)
                return dct
            else:
                raise type(e)(error_message) from e


class StrictAASFromJsonDecoder(AASFromJsonDecoder):
    """
    A strict version of the AASFromJsonDecoder class for deserializing Asset Administration Shell data from the
    official JSON format

    This version has set failsafe = False, which will lead to Exceptions raised for every missing attribute or wrong
    object type.
    """
    failsafe = False


def read_json_aas_file(file: IO, failsafe: bool = True) -> model.DictObjectStore:
    """
    Read an Asset Adminstration Shell JSON file according to 'Details of the Asset Administration Shell', chapter 5.5

    :param file: A file-like object to read the JSON-serialized data from
    :param failsafe: If True, the file is parsed in a failsafe way: Instead of raising an Exception for missing
                     attributes and wrong types, errors are logged and defective objects are skipped
    :return: A DictObjectStore containing all AAS objects from the JSON file
    """
    # read, parse and convert JSON file
    data = json.load(file, cls=AASFromJsonDecoder if failsafe else StrictAASFromJsonDecoder)

    # Add AAS objects to ObjectStore
    ret: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    for name, expected_type in (('assetAdministrationShells', model.AssetAdministrationShell),
                                ('assets', model.Asset),
                                ('submodels', model.Submodel),
                                ('conceptDescriptions', model.ConceptDescription)):
        try:
            lst = _get_ts(data, name, list)
        except (KeyError, TypeError) as e:
            error_message = "Could not find list '{}' in AAS JSON file".format(name)
            if failsafe:
                logger.warning(error_message)
                continue
            else:
                raise type(e)(error_message) from e

        for item in lst:
            error_message = "Expected a {} in list '{}', but found {}".format(
                expected_type.__name__, name, repr(item))
            if isinstance(item, model.Identifiable):
                if not isinstance(item, expected_type):
                    if failsafe:
                        logger.warning("{} was in wrong list '{}'; nevertheless, we'll use it".format(item, name))
                    else:
                        raise TypeError(error_message)
                ret.add(item)
            elif failsafe:
                logger.error(error_message)
            else:
                raise TypeError(error_message)

    return ret
