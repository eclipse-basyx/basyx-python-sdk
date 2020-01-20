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

The module provides custom JSONDecoder classes `AASFromJsonDecoder` and `StrictAASFromJsonDecoder` to be used with
the Python standard `json` module. They contain a custom `object_hook` function to detect encoded AAS objects within the
JSON data and convert them to PyAAS objects while parsing. Additionally, there's the `read_json_aas_file()` function,
that takes a complete AAS JSON file, reads its contents and returns the contained AAS objects as DictObjectStore.

This job is performed in a bottom-up approach: The `object_hook()` method gets called for every parsed JSON object
(as dict) and checks for existence of the `modelType` attribute. If it is present, the `AAS_CLASS_PARSERS` dict defines,
which of the constructor methods of the class is to be used for converting the dict into an object. Embedded
objects that should have a `modelType` themselves are expected to be converted already. Other embedded objects are
converted using a number of helper constructor methods.
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
        raise TypeError("Dict entry '{}' has unexpected type {}".format(key, type(val).__name__))
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


class AASFromJsonDecoder(json.JSONDecoder):
    """
    Custom JSONDecoder class to use the `json` module for deserializing Asset Administration Shell data from the
    official JSON format

    The class contains a custom `object_hook` function to detect encoded AAS objects within the JSON data and convert
    them to PyAAS objects while parsing. Typical usage:

        data = json.loads(json_string, cls=AASFromJsonDecoder)

    The `object_hook` function uses a set of `_construct_*()` methods, one for each
    AAS object type to transform the JSON objects in to PyAAS objects. These constructor methods are divided into two
    parts: "Helper Constructor Methods", that are used to construct PyAAS types without a `modelType` attribute as
    embedded objects within other PyAAS objects, and "Direct Constructor Methods" for PyAAS types *with* `modelType`
    attribute. The former are called from other constructor methods or utility methods based on the expected type of an
    attribute, the latter are called directly from the `object_hook()` function based on the `modelType` attribute.

    This class may be subclassed to override some of the constructor functions, e.g. to construct objects of specialized
    subclasses of the PyAAS object classes instead of these normal classes from the `model` package. To simplify this
    tasks, (nearly) all the constructor methods take a parameter `object_type` defaulting to the normal PyAAS object
    class, that can be overridden in a derived function:

        class EnhancedAsset(model.Asset):
            pass

        class EnhancedAASDecoder(AASFromJsonDecoder):
            @classmethod
            def _construct_asset(cls, dct):
                return super()._construct_asset(dct, object_class=EnhancedAsset)

    :cvar failsafe: If True (the default), don't raise Exceptions for missing attributes and wrong types, but instead
                    skip defective objects and use logger to output warnings. Use StrictAASFromJsonDecoder for a
                    non-failsafe version.
    """
    failsafe = True

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @classmethod
    def object_hook(cls, dct: Dict[str, object]) -> object:
        # Check if JSON object seems to be a deserializable AAS object (i.e. it has a modelType). Otherwise, the JSON
        #   object is returned as is, so it's possible to mix AAS objects with other data within a JSON structure.
        if 'modelType' not in dct:
            return dct

        # The following dict specifies a constructor method for all AAS classes that may be identified using the
        # `modelType` attribute in their JSON representation. Each of those constructor functions takes the JSON
        # representation of an object and tries to construct a Python object from it. Embedded objects that have a
        # modelType themselves are expected to be converted to the correct PythonType already. Additionally, each
        # function takes a bool parameter `failsafe`, which indicates weather to log errors and skip defective objects
        # instead of raising an Exception.
        AAS_CLASS_PARSERS: Dict[str, Callable[[Dict[str, object]], object]] = {
            'Asset': cls._construct_asset,
            'AssetAdministrationShell': cls._construct_asset_administration_shell,
            'View': cls._construct_view,
            'ConceptDescription': cls._construct_concept_description,
            'Qualifier': cls._construct_qualifier,
            'Formula': cls._construct_formula,
            'Submodel': cls._construct_submodel,
            'ConceptDictionary': cls._construct_concept_dictionary,
            'Capability': cls._construct_capability,
            'Entity': cls._construct_entity,
            'BasicEvent': cls._construct_basic_event,
            'Operation': cls._construct_operation,
            'RelationshipElement': cls._construct_relationship_element,
            'AnnotatedRelationshipElement': cls._construct_annotated_relationship_element,
            'SubmodelElementCollection': cls._construct_submodel_element_collection,
            'Blob': cls._construct_blob,
            'File': cls._construct_file,
            'MultiLanguageProperty': cls._construct_multi_language_property,
            'Property': cls._construct_property,
            'Range': cls._construct_range,
            'ReferenceElement': cls._construct_reference_element,
        }

        # Get modelType and constructor function
        if not isinstance(dct['modelType'], dict) or 'name' not in dct['modelType']:
            logger.warning("JSON object has unexpected format of modelType: %s", dct['modelType'])
            # Even in strict mode, we consider 'modelType' attributes of wrong type as non-AAS objects instead of
            #   raising an exception. However, the object's type will probably checked later by read_json_aas_file() or
            #   _expect_type()
            return dct
        model_type = dct['modelType']['name']
        if model_type not in AAS_CLASS_PARSERS:
            if not cls.failsafe:
                raise TypeError("Found JSON object with modelType=\"%s\", which is not a known AAS class" % model_type)
            logger.error("Found JSON object with modelType=\"%s\", which is not a known AAS class", model_type)
            return dct

        # Use constructor function to transform JSON representation into PyAAS model object
        try:
            return AAS_CLASS_PARSERS[model_type](dct)
        except (KeyError, TypeError) as e:
            error_message = "Error while trying to convert JSON object into {}: {} >>> {}".format(
                model_type, e, pprint.pformat(dct, depth=2, width=2**14, compact=True))
            if cls.failsafe:
                logger.error(error_message, exc_info=e)
                # In failsafe mode, we return the raw JSON object dict, if there were errors while parsing an object, so
                #   a client application is able to handle this data. The read_json_aas_file() function and all
                #   constructors for complex objects will skip those items by using _expect_type().
                return dct
            else:
                raise type(e)(error_message) from e

    # ##################################################################################################
    # Utility Methods used in constructor methods to add general attributes (from abstract base classes)
    # ##################################################################################################

    @classmethod
    def _amend_abstract_attributes(cls, obj: object, dct: Dict[str, object]) -> None:
        """
        Utility method to add the optional attributes of the abstract meta classes Referable, Identifiable,
        HasSemantics, HasKind and Qualifiable to an object inheriting from any of these classes, if present

        :param obj: The object to amend its attributes
        :param dct: The object's dict representation from JSON
        """
        if isinstance(obj, model.Referable):
            if 'category' in dct:
                obj.category = _get_ts(dct, 'category', str)
            if 'description' in dct:
                obj.description = cls._construct_lang_string_set(_get_ts(dct, 'description', list))
        if isinstance(obj, model.Identifiable):
            if 'idShort' in dct:
                obj.id_short = _get_ts(dct, 'idShort', str)
            if 'administration' in dct:
                obj.administration = cls._construct_administrative_information(_get_ts(dct, 'administration', dict))
        if isinstance(obj, model.HasSemantics):
            if 'semanticId' in dct:
                obj.semantic_id = cls._construct_reference(_get_ts(dct, 'semanticId', dict))
        # `HasKind` provides only mandatory, immutable attributes; so we cannot do anything here, after object creation.
        # However, the `cls._get_kind()` function may assist by retreiving them from the JSON object
        if isinstance(obj, model.Qualifiable):
            if 'qualifiers' in dct:
                for constraint in _get_ts(dct, 'qualifiers', list):
                    if _expect_type(constraint, model.Constraint, str(obj), cls.failsafe):
                        obj.qualifier.add(constraint)

    @classmethod
    def _get_kind(cls, dct: Dict[str, object]) -> model.ModelingKind:
        """
        Utility method to get the kind of an HasKind object from its JSON representation.

        :param dct: The object's dict representation from JSON
        :return: The object's `kind` value
        """
        return MODELING_KIND_INVERSE[_get_ts(dct, "kind", str)] if 'kind' in dct else model.ModelingKind.INSTANCE

    # #############################################################################
    # Helper Constructor Methods starting from here
    # #############################################################################

    # These constructor methods create objects that are not identified by a 'modelType' JSON attribute, so they can not
    # be called from the object_hook() method. Instead, they are called by other constructor functions to transform
    # embedded JSON data into the expected type at their location in the outer JSON object.

    @classmethod
    def _construct_key(cls, dct: Dict[str, object], object_class=model.Key) -> model.Key:
        return object_class(type_=KEY_ELEMENTS_INVERSE[_get_ts(dct, 'type', str)],
                            id_type=KEY_TYPES_INVERSE[_get_ts(dct, 'idType', str)],
                            value=_get_ts(dct, 'value', str),
                            local=_get_ts(dct, 'local', bool))

    @classmethod
    def _construct_reference(cls, dct: Dict[str, object], object_class=model.Reference) -> model.Reference:
        keys = [cls._construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
        return model.Reference(tuple(keys))

    @classmethod
    def _construct_aas_reference(cls, dct: Dict[str, object], type_: Type[T], object_class=model.AASReference)\
            -> model.AASReference:
        keys = [cls._construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
        if keys and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type_, type(None)), type_):
            logger.warning("type %s of last key of reference to %s does not match reference type %s",
                           keys[-1].type_.name, " / ".join(str(k) for k in keys), type_.__name__)
        return object_class(tuple(keys), type_)

    @classmethod
    def _construct_identifier(cls, dct: Dict[str, object], object_class=model.Identifier) -> model.Identifier:
        return object_class(_get_ts(dct, 'id', str),
                            IDENTIFIER_TYPES_INVERSE[_get_ts(dct, 'idType', str)])

    @classmethod
    def _construct_administrative_information(
            cls, dct: Dict[str, object], object_class=model.AdministrativeInformation)\
            -> model.AdministrativeInformation:
        ret = object_class()
        if 'version' in dct:
            ret.version = _get_ts(dct, 'version', str)
            if 'revision' in dct:
                ret.revision = _get_ts(dct, 'revision', str)
        elif 'revision' in dct:
            logger.warning("Ignoring 'revision' attribute of AdministrativeInformation object due to missing 'version'")
        return ret

    @classmethod
    def _construct_security(cls, _dct: Dict[str, object], object_class=model.Security) -> model.Security:
        return object_class()

    @classmethod
    def _construct_operation_variable(
            cls, dct: Dict[str, object], object_class=model.OperationVariable) -> model.OperationVariable:
        ret = object_class(value=_get_ts(dct, 'value', model.SubmodelElement))
        return ret

    @classmethod
    def _construct_lang_string_set(cls, lst: List[Dict[str, object]]) -> model.LangStringSet:
        ret = {}
        for desc in lst:
            try:
                ret[_get_ts(desc, 'language', str)] = _get_ts(desc, 'text', str)
            except (KeyError, TypeError) as e:
                error_message = "Error while trying to convert JSON object into LangString: {} >>> {}".format(
                    e, pprint.pformat(lst, depth=2, width=2 ** 14, compact=True))
                if cls.failsafe:
                    logger.error(error_message, exc_info=e)
                else:
                    raise type(e)(error_message) from e
        return ret

    # #############################################################################
    # Direct Constructor Methods (for classes with `modelType`) starting from here
    # #############################################################################

    # These constructor methods create objects that *are* identified by a 'modelType' JSON attribute, so they can be
    # be called from the object_hook() method directly.

    @classmethod
    def _construct_asset(cls, dct: Dict[str, object], object_class=model.Asset) -> model.Asset:
        ret = object_class(kind=ASSET_KIND_INVERSE[_get_ts(dct, 'kind', str)],
                           identification=cls._construct_identifier(_get_ts(dct, "identification", dict)))
        cls._amend_abstract_attributes(ret, dct)
        if 'assetIdentificationModel' in dct:
            ret.asset_identification_model = cls._construct_aas_reference(
                _get_ts(dct, 'assetIdentificationModel', dict), model.Submodel)
        if 'billOfMaterial' in dct:
            ret.bill_of_material = cls._construct_aas_reference(_get_ts(dct, 'billOfMaterial', dict), model.Submodel)
        return ret

    @classmethod
    def _construct_asset_administration_shell(
            cls, dct: Dict[str, object], object_class=model.AssetAdministrationShell) -> model.AssetAdministrationShell:
        ret = object_class(
            asset=cls._construct_aas_reference(_get_ts(dct, 'asset', dict), model.Asset),
            identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)))
        cls._amend_abstract_attributes(ret, dct)
        if 'submodels' in dct:
            for sm_data in _get_ts(dct, 'submodels', list):
                ret.submodel_.add(cls._construct_aas_reference(sm_data, model.Submodel))
        if 'views' in dct:
            for view in _get_ts(dct, 'views', list):
                if _expect_type(view, model.View, str(ret), cls.failsafe):
                    ret.view.add(view)
        if 'conceptDictionaries' in dct:
            for concept_dictionary in _get_ts(dct, 'conceptDictionaries', list):
                if _expect_type(concept_dictionary, model.ConceptDictionary, str(ret), cls.failsafe):
                    ret.concept_dictionary.add(concept_dictionary)
        if 'security' in dct:
            ret.security_ = cls._construct_security(_get_ts(dct, 'security', dict))
        if 'derivedFrom' in dct:
            ret.derived_from = cls._construct_aas_reference(_get_ts(dct, 'derivedFrom', dict),
                                                            model.AssetAdministrationShell)
        return ret

    @classmethod
    def _construct_view(cls, dct: Dict[str, object], object_class=model.View) -> model.View:
        ret = object_class(_get_ts(dct, 'idShort', str))
        cls._amend_abstract_attributes(ret, dct)
        if 'containedElements' in dct:
            for element_data in _get_ts(dct, 'containedElements', list):
                ret.contained_element.add(cls._construct_aas_reference(element_data, model.Referable))
        return ret

    @classmethod
    def _construct_concept_description(cls, dct: Dict[str, object], object_class=model.ConceptDescription)\
            -> model.ConceptDescription:
        ret = object_class(identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)))
        cls._amend_abstract_attributes(ret, dct)
        if 'isCaseOf' in dct:
            for case_data in _get_ts(dct, "isCaseOf", list):
                ret.is_case_of.add(cls._construct_reference(case_data))
        return ret

    @classmethod
    def _construct_concept_dictionary(cls, dct: Dict[str, object], object_class=model.ConceptDictionary)\
            -> model.ConceptDictionary:
        ret = object_class(_get_ts(dct, "idShort", str))
        cls._amend_abstract_attributes(ret, dct)
        if 'conceptDescriptions' in dct:
            for desc_data in _get_ts(dct, "conceptDescriptions", list):
                ret.concept_description.add(cls._construct_aas_reference(desc_data, model.ConceptDescription))
        return ret

    @classmethod
    def _construct_entity(cls, dct: Dict[str, object], object_class=model.Entity) -> model.Entity:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           entity_type=ENTITY_TYPES_INVERSE[_get_ts(dct, "entityType", str)],
                           asset=(cls._construct_aas_reference(_get_ts(dct, 'asset', dict), model.Asset)
                                  if 'asset' in dct else None),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'statements' in dct:
            for element in _get_ts(dct, "statements", list):
                if _expect_type(element, model.SubmodelElement, str(ret), cls.failsafe):
                    ret.statement.add(element)
        return ret

    @classmethod
    def _construct_qualifier(cls, dct: Dict[str, object], object_class=model.Qualifier) -> model.Qualifier:
        ret = object_class(type_=_get_ts(dct, 'type', str),
                           value_type=_get_ts(dct, 'valueType', str))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct:
            ret.value = _get_ts(dct, 'value', str)
        if 'valueId' in dct:
            ret.value_id = cls._construct_reference(_get_ts(dct, 'valueId', dict))
        return ret

    @classmethod
    def _construct_formula(cls, dct: Dict[str, object], object_class=model.Formula) -> model.Formula:
        ret = object_class()
        cls._amend_abstract_attributes(ret, dct)
        if 'dependsOn' in dct:
            for dependency_data in _get_ts(dct, 'dependsOn', list):
                try:
                    ret.depends_on.add(cls._construct_reference(dependency_data))
                except (KeyError, TypeError) as e:
                    error_message = \
                        "Error while trying to convert JSON object into dependency Reference for {}: {} >>> {}".format(
                            ret, e, pprint.pformat(dct, depth=2, width=2 ** 14, compact=True))
                    if cls.failsafe:
                        logger.error(error_message, exc_info=e)
                    else:
                        raise type(e)(error_message) from e
        return ret

    @classmethod
    def _construct_submodel(cls, dct: Dict[str, object], object_class=model.Submodel) -> model.Submodel:
        ret = object_class(identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'submodelElements' in dct:
            for element in _get_ts(dct, "submodelElements", list):
                if _expect_type(element, model.SubmodelElement, str(ret), cls.failsafe):
                    ret.submodel_element.add(element)
        return ret

    @classmethod
    def _construct_capability(cls, dct: Dict[str, object], object_class=model.Capability) -> model.Capability:
        ret = object_class(id_short=_get_ts(dct, "idShort", str), kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_basic_event(cls, dct: Dict[str, object], object_class=model.BasicEvent) -> model.BasicEvent:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           observed=cls._construct_aas_reference(_get_ts(dct, 'observed', dict), model.Referable),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_operation(cls, dct: Dict[str, object], object_class=model.Operation) -> model.Operation:
        ret = object_class(_get_ts(dct, "idShort", str), kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)

        # Deserialize variables (they are not Referable, thus we don't
        for json_name, target in (('inputVariable', ret.input_variable),
                                  ('outputVariable', ret.output_variable),
                                  ('inoutputVariable', ret.in_output_variable)):
            if json_name in dct:
                for variable_data in _get_ts(dct, json_name, list):
                    try:
                        target.append(cls._construct_operation_variable(variable_data))
                    except (KeyError, TypeError) as e:
                        error_message = "Error while trying to convert JSON object into {} of {}: {}".format(
                            json_name, ret, pprint.pformat(variable_data, depth=2, width=2 ** 14, compact=True))
                        if cls.failsafe:
                            logger.error(error_message, exc_info=e)
                        else:
                            raise type(e)(error_message) from e
        return ret

    @classmethod
    def _construct_relationship_element(
            cls, dct: Dict[str, object], object_class=model.RelationshipElement) -> model.RelationshipElement:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           first=cls._construct_aas_reference(_get_ts(dct, 'first', dict), model.Referable),
                           second=cls._construct_aas_reference(_get_ts(dct, 'second', dict), model.Referable),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_annotated_relationship_element(
            cls, dct: Dict[str, object], object_class=model.AnnotatedRelationshipElement)\
            -> model.AnnotatedRelationshipElement:
        ret = object_class(
            id_short=_get_ts(dct, "idShort", str),
            first=cls._construct_aas_reference(_get_ts(dct, 'first', dict), model.Referable),
            second=cls._construct_aas_reference(_get_ts(dct, 'second', dict), model.Referable),
            kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'annotation' in dct:
            for annotation_data in _get_ts(dct, 'annotation', list):
                try:
                    ret.annotation.add(cls._construct_aas_reference(annotation_data, model.DataElement))
                except (KeyError, TypeError) as e:
                    error_message = \
                        "Error while trying to convert JSON object into annotation Reference for {}: {} >>> {}".format(
                            ret, e, pprint.pformat(dct, depth=2, width=2 ** 14, compact=True))
                    if cls.failsafe:
                        logger.error(error_message, exc_info=e)
                    else:
                        raise type(e)(error_message) from e
        return ret

    @classmethod
    def _construct_submodel_element_collection(
            cls,
            dct: Dict[str, object],
            object_class_ordered=model.SubmodelElementCollectionOrdered,
            object_class_unordered=model.SubmodelElementCollectionUnordered)\
            -> model.SubmodelElementCollection:
        ret: model.SubmodelElementCollection
        if 'ordered' in dct and _get_ts(dct, 'ordered', bool):
            ret = object_class_ordered(
                id_short=_get_ts(dct, "idShort", str), kind=cls._get_kind(dct))
        else:
            ret = object_class_unordered(
                id_short=_get_ts(dct, "idShort", str), kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct:
            for element in _get_ts(dct, "value", list):
                if _expect_type(element, model.SubmodelElement, str(ret), cls.failsafe):
                    ret.value.add(element)
        return ret

    @classmethod
    def _construct_blob(cls, dct: Dict[str, object], object_class=model.Blob) -> model.Blob:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           mime_type=_get_ts(dct, "mimeType", str),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct:
            ret.value = base64.b64decode(_get_ts(dct, 'value', str))
        return ret

    @classmethod
    def _construct_file(cls, dct: Dict[str, object], object_class=model.File) -> model.File:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value=None,
                           mime_type=_get_ts(dct, "mimeType", str),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = _get_ts(dct, 'value', str)
        return ret

    @classmethod
    def _construct_multi_language_property(
            cls, dct: Dict[str, object], object_class=model.MultiLanguageProperty) -> model.MultiLanguageProperty:
        ret = object_class(id_short=_get_ts(dct, "idShort", str), kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = cls._construct_lang_string_set(_get_ts(dct, 'value', list))
        if 'valueId' in dct:
            ret.value_id = cls._construct_reference(_get_ts(dct, 'valueId', dict))
        return ret

    @classmethod
    def _construct_property(cls, dct: Dict[str, object], object_class=model.Property) -> model.Property:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value_type=_get_ts(dct, 'valueType', str),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = _get_ts(dct, 'value', str)
        if 'valueId' in dct:
            ret.value_id = cls._construct_reference(_get_ts(dct, 'valueId', dict))
        return ret

    @classmethod
    def _construct_range(cls, dct: Dict[str, object], object_class=model.Range) -> model.Range:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value_type=_get_ts(dct, 'valueType', str),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'min' in dct and dct['min'] is not None:
            ret.min_ = _get_ts(dct, 'min', str)
        if 'max' in dct and dct['max'] is not None:
            ret.max_ = _get_ts(dct, 'max', str)
        return ret

    @classmethod
    def _construct_reference_element(
            cls, dct: Dict[str, object], object_class=model.ReferenceElement) -> model.ReferenceElement:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value=None,
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = cls._construct_aas_reference(_get_ts(dct, 'value', dict), model.Referable)
        return ret


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
