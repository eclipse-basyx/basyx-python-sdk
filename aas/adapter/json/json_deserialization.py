# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
.. _adapter.json.json_deserialization:

Module for deserializing Asset Administration Shell data from the official JSON format

The module provides custom JSONDecoder classes :class:`~.AASFromJsonDecoder` and :class:`~.StrictAASFromJsonDecoder` to
be used with the Python standard `json` module.

Furthermore it provides two classes :class:`~aas.adapter.json.json_deserialization.StrippedAASFromJsonDecoder` and
:class:`~aas.adapter.json.json_deserialization.StrictStrippedAASFromJsonDecoder` for parsing stripped JSON objects,
which are used in the http adapter (see https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91).
The classes contain a custom :meth:`~aas.adapter.json.json_deserialization.AASFromJsonDecoder.object_hook` function
to detect encoded AAS objects within the JSON data and convert them to PyI40AAS objects while parsing. Additionally,
there's the :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file_into` function, that takes a complete
AAS JSON file, reads its contents and stores the objects in the provided
:class:`~aas.model.provider.AbstractObjectStore`. :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file` is
a wrapper for this function. Instead of storing the objects in a given :class:`~aas.model.provider.AbstractObjectStore`,
it returns a :class:`~aas.model.provider.DictObjectStore` containing parsed objects.

The deserialization is performed in a bottom-up approach: The `object_hook()` method gets called for every parsed JSON
object (as dict) and checks for existence of the `modelType` attribute. If it is present, the `AAS_CLASS_PARSERS` dict
defines, which of the constructor methods of the class is to be used for converting the dict into an object. Embedded
objects that should have a `modelType` themselves are expected to be converted already. Other embedded objects are
converted using a number of helper constructor methods.
"""
import base64
import json
import logging
import pprint
from typing import Dict, Callable, TypeVar, Type, List, IO, Optional, Set

from aas import model
from .._generic import MODELING_KIND_INVERSE, ASSET_KIND_INVERSE, KEY_ELEMENTS_INVERSE, KEY_TYPES_INVERSE,\
    IDENTIFIER_TYPES_INVERSE, ENTITY_TYPES_INVERSE, IEC61360_DATA_TYPES_INVERSE, IEC61360_LEVEL_TYPES_INVERSE,\
    KEY_ELEMENTS_CLASSES_INVERSE

logger = logging.getLogger(__name__)


# #############################################################################
# Helper functions (for simplifying implementation of constructor functions)
# #############################################################################

T = TypeVar('T')


def _get_ts(dct: Dict[str, object], key: str, type_: Type[T]) -> T:
    """
    Helper function for getting an item from a (str→object) dict in a typesafe way.

    The type of the object is checked at runtime and a TypeError is raised, if the object has not the expected type.

    :param dct: The dict
    :param key: The key of the item to retrieve
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
    :param failsafe: Log error and return false instead of raising a TypeError
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

    The class contains a custom :meth:`~.AASFromJsonDecoder.object_hook` function to detect encoded AAS objects within
    the JSON data and convert them to PyI40AAS objects while parsing.

    Typical usage:

    .. code-block:: python

        data = json.loads(json_string, cls=AASFromJsonDecoder)

    The `object_hook` function uses a set of `_construct_*()` methods, one for each
    AAS object type to transform the JSON objects in to PyI40AAS objects. These constructor methods are divided into two
    parts: "Helper Constructor Methods", that are used to construct PyI40AAS types without a `modelType` attribute as
    embedded objects within other PyI40AAS objects, and "Direct Constructor Methods" for PyI40AAS type
    *with* `modelType` attribute. The former are called from other constructor methods or utility methods based on
    the expected type of an attribute, the latter are called directly from the `object_hook()` function based on
    the `modelType` attribute.

    This class may be subclassed to override some of the constructor functions, e.g. to construct objects of specialized
    subclasses of the PyI40AAS object classes instead of these normal classes from the `model` package. To simplify this
    tasks, (nearly) all the constructor methods take a parameter `object_type` defaulting to the normal PyI40AAS object
    class, that can be overridden in a derived function:

    .. code-block:: python

        class EnhancedAsset(model.Asset):
            pass

        class EnhancedAASDecoder(AASFromJsonDecoder):
            @classmethod
            def _construct_asset(cls, dct):
                return super()._construct_asset(dct, object_class=EnhancedAsset)


    :cvar failsafe: If `True` (the default), don't raise Exceptions for missing attributes and wrong types, but instead
                    skip defective objects and use logger to output warnings. Use StrictAASFromJsonDecoder for a
                    non-failsafe version.
    :cvar stripped: If `True`, the JSON objects will be parsed in a stripped manner, excluding some attributes.
                    Defaults to `False`.
                    See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
    """
    failsafe = True
    stripped = False

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
            'AssetAdministrationShell': cls._construct_asset_administration_shell,
            'Asset': cls._construct_asset,
            'AssetInformation': cls._construct_asset_information,
            'IdentifierKeyValuePair': cls._construct_identifier_key_value_pair,
            'View': cls._construct_view,
            'ConceptDescription': cls._construct_concept_description,
            'Qualifier': cls._construct_qualifier,
            'Extension': cls._construct_extension,
            'Submodel': cls._construct_submodel,
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

        # Use constructor function to transform JSON representation into PyI40AAS model object
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
            if 'displayName' in dct:
                obj.display_name = cls._construct_lang_string_set(_get_ts(dct, 'displayName', list))
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
        # However, the `cls._get_kind()` function may assist by retrieving them from the JSON object
        if isinstance(obj, model.Qualifiable) and not cls.stripped:
            if 'qualifiers' in dct:
                for constraint in _get_ts(dct, 'qualifiers', list):
                    if _expect_type(constraint, model.Constraint, str(obj), cls.failsafe):
                        obj.qualifier.add(constraint)

        if isinstance(obj, model.HasExtension) and not cls.stripped:
            if 'extensions' in dct:
                for extension in _get_ts(dct, 'extensions', list):
                    obj.extension.add(cls._construct_extension(extension))

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
                            value=_get_ts(dct, 'value', str))

    @classmethod
    def _construct_identifier_key_value_pair(cls, dct: Dict[str, object], object_class=model.IdentifierKeyValuePair) \
            -> model.IdentifierKeyValuePair:
        return object_class(key=_get_ts(dct, 'key', str),
                            value=_get_ts(dct, 'value', str),
                            external_subject_id=cls._construct_reference(_get_ts(dct, 'subjectId', dict)))

    @classmethod
    def _construct_reference(cls, dct: Dict[str, object], object_class=model.Reference) -> model.Reference:
        keys = [cls._construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
        return object_class(tuple(keys))

    @classmethod
    def _construct_aas_reference(cls, dct: Dict[str, object], type_: Type[T], object_class=model.AASReference)\
            -> model.AASReference:
        keys = [cls._construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
        if keys and not issubclass(KEY_ELEMENTS_CLASSES_INVERSE.get(keys[-1].type, type(None)), type_):
            logger.warning("type %s of last key of reference to %s does not match reference type %s",
                           keys[-1].type.name, " / ".join(str(k) for k in keys), type_.__name__)
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
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        ret = object_class(value=_get_ts(dct, 'value', model.SubmodelElement))  # type: ignore
        return ret

    @classmethod
    def _construct_lang_string_set(cls, lst: List[Dict[str, object]]) -> Optional[model.LangStringSet]:
        ret = {}
        for desc in lst:
            try:
                ret[_get_ts(desc, 'language', str)] = _get_ts(desc, 'text', str)
            except (KeyError, TypeError) as e:
                error_message = "Error while trying to convert JSON object into LangString: {} >>> {}".format(
                    e, pprint.pformat(desc, depth=2, width=2 ** 14, compact=True))
                if cls.failsafe:
                    logger.error(error_message, exc_info=e)
                else:
                    raise type(e)(error_message) from e
        return ret

    @classmethod
    def _construct_value_list(cls, dct: Dict[str, object]) -> model.ValueList:
        ret: model.ValueList = set()
        for element in _get_ts(dct, 'valueReferencePairTypes', list):
            try:
                ret.add(cls._construct_value_reference_pair(element))
            except (KeyError, TypeError) as e:
                error_message = "Error while trying to convert JSON object into ValueReferencePair: {} >>> {}".format(
                    e, pprint.pformat(element, depth=2, width=2 ** 14, compact=True))
                if cls.failsafe:
                    logger.error(error_message, exc_info=e)
                else:
                    raise type(e)(error_message) from e
        return ret

    @classmethod
    def _construct_value_reference_pair(cls, dct: Dict[str, object], object_class=model.ValueReferencePair) -> \
            model.ValueReferencePair:
        value_type = model.datatypes.XSD_TYPE_CLASSES[_get_ts(dct, 'valueType', str)]
        return object_class(value_type=value_type,
                            value=model.datatypes.from_xsd(_get_ts(dct, 'value', str), value_type),
                            value_id=cls._construct_reference(_get_ts(dct, 'valueId', dict)))

    # #############################################################################
    # Direct Constructor Methods (for classes with `modelType`) starting from here
    # #############################################################################

    # These constructor methods create objects that *are* identified by a 'modelType' JSON attribute, so they can be
    # be called from the object_hook() method directly.

    @classmethod
    def _construct_asset_information(cls, dct: Dict[str, object], object_class=model.AssetInformation)\
            -> model.AssetInformation:
        ret = object_class(asset_kind=ASSET_KIND_INVERSE[_get_ts(dct, 'assetKind', str)])
        cls._amend_abstract_attributes(ret, dct)
        if 'globalAssetId' in dct:
            ret.global_asset_id = cls._construct_reference(_get_ts(dct, 'globalAssetId', dict))
        if 'externalAssetIds' in dct:
            for desc_data in _get_ts(dct, "externalAssetIds", list):
                ret.specific_asset_id.add(cls._construct_identifier_key_value_pair(desc_data,
                                                                                   model.IdentifierKeyValuePair))
        if 'billOfMaterial' in dct:
            for desc_data in _get_ts(dct, "billOfMaterial", list):
                ret.bill_of_material.add(cls._construct_aas_reference(desc_data, model.Submodel))
        if 'thumbnail' in dct:
            ret.default_thumbnail = _get_ts(dct, 'thumbnail', model.File)
        return ret

    @classmethod
    def _construct_asset(cls, dct: Dict[str, object], object_class=model.Asset) -> model.Asset:
        ret = object_class(identification=cls._construct_identifier(_get_ts(dct, "identification", dict)))
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_asset_administration_shell(
            cls, dct: Dict[str, object], object_class=model.AssetAdministrationShell) -> model.AssetAdministrationShell:
        ret = object_class(
            asset_information=cls._construct_asset_information(_get_ts(dct, 'assetInformation', dict),
                                                               model.AssetInformation),
            identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)))
        cls._amend_abstract_attributes(ret, dct)
        if not cls.stripped and 'submodels' in dct:
            for sm_data in _get_ts(dct, 'submodels', list):
                ret.submodel.add(cls._construct_aas_reference(sm_data, model.Submodel))
        if not cls.stripped and 'views' in dct:
            for view in _get_ts(dct, 'views', list):
                if _expect_type(view, model.View, str(ret), cls.failsafe):
                    ret.view.add(view)
        if 'security' in dct:
            ret.security = cls._construct_security(_get_ts(dct, 'security', dict))
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
                # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
                # see https://github.com/python/mypy/issues/5374
                ret.contained_element.add(cls._construct_aas_reference(element_data, model.Referable))  # type: ignore
        return ret

    @classmethod
    def _construct_concept_description(cls, dct: Dict[str, object], object_class=model.ConceptDescription)\
            -> model.ConceptDescription:
        # Hack to detect IEC61360ConceptDescriptions, which are represented using dataSpecification according to DotAAS
        ret = None
        if 'embeddedDataSpecifications' in dct:
            for dspec in _get_ts(dct, 'embeddedDataSpecifications', list):
                dspec_ref = cls._construct_reference(_get_ts(dspec, 'dataSpecification', dict))
                if dspec_ref.key and (dspec_ref.key[0].value ==
                                      "http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0"):
                    ret = cls._construct_iec61360_concept_description(
                        dct, _get_ts(dspec, 'dataSpecificationContent', dict))
        # If this is not a special ConceptDescription, just construct one of the default object_class
        if ret is None:
            ret = object_class(identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)))
        cls._amend_abstract_attributes(ret, dct)
        if 'isCaseOf' in dct:
            for case_data in _get_ts(dct, "isCaseOf", list):
                ret.is_case_of.add(cls._construct_reference(case_data))
        return ret

    @classmethod
    def _construct_iec61360_concept_description(cls, dct: Dict[str, object], data_spec: Dict[str, object],
                                                object_class=model.concept.IEC61360ConceptDescription)\
            -> model.concept.IEC61360ConceptDescription:
        ret = object_class(identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)),
                           preferred_name=cls._construct_lang_string_set(_get_ts(data_spec, 'preferredName', list)))
        if 'dataType' in data_spec:
            ret.data_type = IEC61360_DATA_TYPES_INVERSE[_get_ts(data_spec, 'dataType', str)]
        if 'definition' in data_spec:
            ret.definition = cls._construct_lang_string_set(_get_ts(data_spec, 'definition', list))
        if 'shortName' in data_spec:
            ret.short_name = cls._construct_lang_string_set(_get_ts(data_spec, 'shortName', list))
        if 'unit' in data_spec:
            ret.unit = _get_ts(data_spec, 'unit', str)
        if 'unitId' in data_spec:
            ret.unit_id = cls._construct_reference(_get_ts(data_spec, 'unitId', dict))
        if 'sourceOfDefinition' in data_spec:
            ret.source_of_definition = _get_ts(data_spec, 'sourceOfDefinition', str)
        if 'symbol' in data_spec:
            ret.symbol = _get_ts(data_spec, 'symbol', str)
        if 'valueFormat' in data_spec:
            ret.value_format = model.datatypes.XSD_TYPE_CLASSES[_get_ts(data_spec, 'valueFormat', str)]
        if 'valueList' in data_spec:
            ret.value_list = cls._construct_value_list(_get_ts(data_spec, 'valueList', dict))
        if 'value' in data_spec:
            ret.value = model.datatypes.from_xsd(_get_ts(data_spec, 'value', str), ret.value_format)
        if 'valueId' in data_spec:
            ret.value_id = cls._construct_reference(_get_ts(data_spec, 'valueId', dict))
        if 'levelType' in data_spec:
            ret.level_types = set(IEC61360_LEVEL_TYPES_INVERSE[level_type]
                                  for level_type in _get_ts(data_spec, 'levelType', list))
        return ret

    @classmethod
    def _construct_entity(cls, dct: Dict[str, object], object_class=model.Entity) -> model.Entity:
        global_asset_id = None
        if 'globalAssetId' in dct:
            global_asset_id = cls._construct_reference(_get_ts(dct, 'globalAssetId', dict))
        specific_asset_id = None
        if 'externalAssetId' in dct:
            specific_asset_id = cls._construct_identifier_key_value_pair(_get_ts(dct, 'externalAssetId', dict))

        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           entity_type=ENTITY_TYPES_INVERSE[_get_ts(dct, "entityType", str)],
                           global_asset_id=global_asset_id,
                           specific_asset_id=specific_asset_id)
        cls._amend_abstract_attributes(ret, dct)
        if not cls.stripped and 'statements' in dct:
            for element in _get_ts(dct, "statements", list):
                if _expect_type(element, model.SubmodelElement, str(ret), cls.failsafe):
                    ret.statement.add(element)
        return ret

    @classmethod
    def _construct_qualifier(cls, dct: Dict[str, object], object_class=model.Qualifier) -> model.Qualifier:
        ret = object_class(type_=_get_ts(dct, 'type', str),
                           value_type=model.datatypes.XSD_TYPE_CLASSES[_get_ts(dct, 'valueType', str)])
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct:
            ret.value = model.datatypes.from_xsd(_get_ts(dct, 'value', str), ret.value_type)
        if 'valueId' in dct:
            ret.value_id = cls._construct_reference(_get_ts(dct, 'valueId', dict))
        return ret

    @classmethod
    def _construct_extension(cls, dct: Dict[str, object], object_class=model.Extension) -> model.Extension:
        ret = object_class(name=_get_ts(dct, 'name', str))
        cls._amend_abstract_attributes(ret, dct)
        if 'valueType' in dct:
            ret.value_type = model.datatypes.XSD_TYPE_CLASSES[_get_ts(dct, 'valueType', str)]
        if 'value' in dct:
            ret.value = model.datatypes.from_xsd(_get_ts(dct, 'value', str), ret.value_type)
        if 'refersTo' in dct:
            ret.refers_to = cls._construct_reference(_get_ts(dct, 'refersTo', dict))
        return ret

    @classmethod
    def _construct_submodel(cls, dct: Dict[str, object], object_class=model.Submodel) -> model.Submodel:
        ret = object_class(identification=cls._construct_identifier(_get_ts(dct, 'identification', dict)),
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if not cls.stripped and 'submodelElements' in dct:
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
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           observed=cls._construct_aas_reference(_get_ts(dct, 'observed', dict),
                                                                 model.Referable),  # type: ignore
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
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           first=cls._construct_aas_reference(_get_ts(dct, 'first', dict),
                                                              model.Referable),  # type: ignore
                           second=cls._construct_aas_reference(_get_ts(dct, 'second', dict),
                                                               model.Referable),  # type: ignore
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_annotated_relationship_element(
            cls, dct: Dict[str, object], object_class=model.AnnotatedRelationshipElement)\
            -> model.AnnotatedRelationshipElement:
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        ret = object_class(
            id_short=_get_ts(dct, "idShort", str),
            first=cls._construct_aas_reference(_get_ts(dct, 'first', dict), model.Referable),  # type: ignore
            second=cls._construct_aas_reference(_get_ts(dct, 'second', dict), model.Referable),  # type: ignore
            kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if not cls.stripped and 'annotation' in dct:
            for element in _get_ts(dct, "annotation", list):
                if _expect_type(element, model.DataElement, str(ret), cls.failsafe):
                    ret.annotation.add(element)
        return ret

    @classmethod
    def _construct_submodel_element_collection(
            cls,
            dct: Dict[str, object])\
            -> model.SubmodelElementCollection:
        ret: model.SubmodelElementCollection
        ordered = False
        allow_duplicates = False
        if 'ordered' in dct:
            ordered = _get_ts(dct, "ordered", bool)
        if 'allowDuplicates' in dct:
            allow_duplicates = _get_ts(dct, "allowDuplicates", bool)
        ret = model.SubmodelElementCollection.create(id_short=_get_ts(dct, "idShort", str),
                                                     kind=cls._get_kind(dct),
                                                     ordered=ordered,
                                                     allow_duplicates=allow_duplicates)
        cls._amend_abstract_attributes(ret, dct)
        if not cls.stripped and 'value' in dct:
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
                           value_type=model.datatypes.XSD_TYPE_CLASSES[_get_ts(dct, 'valueType', str)],
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = model.datatypes.from_xsd(_get_ts(dct, 'value', str), ret.value_type)
        if 'valueId' in dct:
            ret.value_id = cls._construct_reference(_get_ts(dct, 'valueId', dict))
        return ret

    @classmethod
    def _construct_range(cls, dct: Dict[str, object], object_class=model.Range) -> model.Range:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value_type=model.datatypes.XSD_TYPE_CLASSES[_get_ts(dct, 'valueType', str)],
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'min' in dct and dct['min'] is not None:
            ret.min = model.datatypes.from_xsd(_get_ts(dct, 'min', str), ret.value_type)
        if 'max' in dct and dct['max'] is not None:
            ret.max = model.datatypes.from_xsd(_get_ts(dct, 'max', str), ret.value_type)
        return ret

    @classmethod
    def _construct_reference_element(
            cls, dct: Dict[str, object], object_class=model.ReferenceElement) -> model.ReferenceElement:
        ret = object_class(id_short=_get_ts(dct, "idShort", str),
                           value=None,
                           kind=cls._get_kind(dct))
        cls._amend_abstract_attributes(ret, dct)
        if 'value' in dct and dct['value'] is not None:
            ret.value = cls._construct_reference(_get_ts(dct, 'value', dict))
        return ret


class StrictAASFromJsonDecoder(AASFromJsonDecoder):
    """
    A strict version of the AASFromJsonDecoder class for deserializing Asset Administration Shell data from the
    official JSON format

    This version has set `failsafe = False`, which will lead to Exceptions raised for every missing attribute or wrong
    object type.
    """
    failsafe = False


class StrippedAASFromJsonDecoder(AASFromJsonDecoder):
    """
    Decoder for stripped JSON objects. Used in the HTTP adapter.
    """
    stripped = True


class StrictStrippedAASFromJsonDecoder(StrictAASFromJsonDecoder, StrippedAASFromJsonDecoder):
    """
    Non-failsafe decoder for stripped JSON objects.
    """
    pass


def _select_decoder(failsafe: bool, stripped: bool, decoder: Optional[Type[AASFromJsonDecoder]]) \
        -> Type[AASFromJsonDecoder]:
    """
    Returns the correct decoder based on the parameters failsafe and stripped. If a decoder class is given, failsafe
    and stripped are ignored.

    :param failsafe: If true, a failsafe decoder is selected. Ignored if a decoder class is specified.
    :param stripped: If true, a decoder for parsing stripped JSON objects is selected. Ignored if a decoder class is
                     specified.
    :param decoder: Is returned, if specified.
    :return: A AASFromJsonDecoder (sub)class.
    """
    if decoder is not None:
        return decoder
    if failsafe:
        if stripped:
            return StrippedAASFromJsonDecoder
        return AASFromJsonDecoder
    else:
        if stripped:
            return StrictStrippedAASFromJsonDecoder
        return StrictAASFromJsonDecoder


def read_aas_json_file_into(object_store: model.AbstractObjectStore, file: IO, replace_existing: bool = False,
                            ignore_existing: bool = False, failsafe: bool = True, stripped: bool = False,
                            decoder: Optional[Type[AASFromJsonDecoder]] = None) -> Set[model.Identifier]:
    """
    Read an Asset Administration Shell JSON file according to 'Details of the Asset Administration Shell', chapter 5.5
    into a given object store.

    :param object_store: The :class:`ObjectStore <aas.model.provider.AbstractObjectStore>` in which the identifiable
                         objects should be stored
    :param file: A file-like object to read the JSON-serialized data from
    :param replace_existing: Whether to replace existing objects with the same identifier in the object store or not
    :param ignore_existing: Whether to ignore existing objects (e.g. log a message) or raise an error.
                            This parameter is ignored if replace_existing is `True`.
    :param failsafe: If `True`, the document is parsed in a failsafe way: Missing attributes and elements are logged
                     instead of causing exceptions. Defect objects are skipped.
                     This parameter is ignored if a decoder class is specified.
    :param stripped: If `True`, stripped JSON objects are parsed.
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if a decoder class is specified.
    :param decoder: The decoder class used to decode the JSON objects
    :return: A set of :class:`Identifiers <aas.model.base.Identifier>` that were added to object_store
    """
    ret: Set[model.Identifier] = set()
    decoder_ = _select_decoder(failsafe, stripped, decoder)

    # read, parse and convert JSON file
    data = json.load(file, cls=decoder_)

    for name, expected_type in (('assetAdministrationShells', model.AssetAdministrationShell),
                                ('assets', model.Asset),
                                ('submodels', model.Submodel),
                                ('conceptDescriptions', model.ConceptDescription)):
        try:
            lst = _get_ts(data, name, list)
        except (KeyError, TypeError) as e:
            error_message = "Could not find list '{}' in AAS JSON file".format(name)
            if decoder_.failsafe:
                logger.warning(error_message)
                continue
            else:
                raise type(e)(error_message) from e

        for item in lst:
            error_message = "Expected a {} in list '{}', but found {}".format(
                expected_type.__name__, name, repr(item))
            if isinstance(item, model.Identifiable):
                if not isinstance(item, expected_type):
                    if decoder_.failsafe:
                        logger.warning("{} was in wrong list '{}'; nevertheless, we'll use it".format(item, name))
                    else:
                        raise TypeError(error_message)
                if item.identification in ret:
                    error_message = f"{item} has a duplicate identifier already parsed in the document!"
                    if not decoder_.failsafe:
                        raise KeyError(error_message)
                    logger.error(error_message + " skipping it...")
                    continue
                existing_element = object_store.get(item.identification)
                if existing_element is not None:
                    if not replace_existing:
                        error_message = f"object with identifier {item.identification} already exists " \
                                        f"in the object store: {existing_element}!"
                        if not ignore_existing:
                            raise KeyError(error_message + f" failed to insert {item}!")
                        logger.info(error_message + f" skipping insertion of {item}...")
                        continue
                    object_store.discard(existing_element)
                object_store.add(item)
                ret.add(item.identification)
            elif decoder_.failsafe:
                logger.error(error_message)
            else:
                raise TypeError(error_message)
    return ret


def read_aas_json_file(file: IO, **kwargs) -> model.DictObjectStore[model.Identifiable]:
    """
    A wrapper of :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file_into`, that reads all objects in an
    empty :class:`~aas.model.provider.DictObjectStore`. This function supports the same keyword arguments as
    :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file_into`.

    :param file: A filename or file-like object to read the JSON-serialized data from
    :param kwargs: Keyword arguments passed to :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file_into`
    :return: A :class:`~aas.model.provider.DictObjectStore` containing all AAS objects from the JSON file
    """
    object_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    read_aas_json_file_into(object_store, file, **kwargs)
    return object_store
