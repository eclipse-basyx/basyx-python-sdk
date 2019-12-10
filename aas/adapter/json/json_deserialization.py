"""
Module for deserializing Asset Administration Shell data from the official JSON format

The module provides an custom JSONDecoder class `AASFromJsonDecoder` to be used with the Python standard `json` module.
It contains a custom `object_hook` function to detect encoded AAS objects within the JSON data and convert them to
PyAAS objects while parsing.

This job is performed in a bottom-up approach: The `object_hook()` function gets called for every parsed JSON object
(as dict) and checks for existence of the `modelType` attribute. If it is present, the `AAS_CLASS_PARSERS` dict defines,
which of the constructor functions in this module is to be used for converting the dict into an object. Embedded
objects that should have a `modelType` themselves are expected to be converted already. Other embedded objects are
converted using a number of helper constructor functions.
"""
import base64
import json
import logging
from typing import Dict, Callable, TypeVar, Type, List

from ... import model
from .json_serialization import MODELING_KIND, ASSET_KIND, KEY_ELEMENTS, KEY_TYPES, IDENTIFIER_TYPES, ENTITY_TYPES

logger = logging.getLogger(__name__)

MODELING_KIND_INVERSE: Dict[str, model.ModelingKind] = {v: k for k, v in MODELING_KIND.items()}
ASSET_KIND_INVERSE: Dict[str, model.AssetKind] = {v: k for k, v in ASSET_KIND.items()}
KEY_ELEMENTS_INVERSE: Dict[str, model.KeyElements] = {v: k for k, v in KEY_ELEMENTS.items()}
KEY_TYPES_INVERSE: Dict[str, model.KeyType] = {v: k for k, v in KEY_TYPES.items()}
IDENTIFIER_TYPES_INVERSE: Dict[str, model.IdentifierType] = {v: k for k, v in IDENTIFIER_TYPES.items()}
ENTITY_TYPES_INVERSE: Dict[str, model.EntityType] = {v: k for k, v in ENTITY_TYPES.items()}

KEY_ELEMENTS_CLASSES = {
    model.KeyElements.ASSET: model.Asset,
    model.KeyElements.ASSET_ADMINISTRATION_SHELL: model.AssetAdministrationShell,
    model.KeyElements.CONCEPT_DESCRIPTION: model.ConceptDescription,
    model.KeyElements.SUBMODEL: model. Submodel,
    model.KeyElements.ANNOTATION_RELATIONSHIP_ELEMENT: model.AnnotatedRelationshipElement,
    model.KeyElements.BASIC_EVENT: model.BasicEvent,
    model.KeyElements.BLOB: model.Blob,
    model.KeyElements.CAPABILITY: model.Capability,
    model.KeyElements.CONCEPT_DICTIONARY: model.ConceptDictionary,
    model.KeyElements.DATA_ELEMENT: model.DataElement,
    model.KeyElements.ENTITY: model.Entity,
    model.KeyElements.EVENT: model.Event,
    model.KeyElements.FILE: model.File,
    model.KeyElements.MULTI_LANGUAGE_PROPERTY: model.MultiLanguageProperty,
    model.KeyElements.OPERATION: model.Operation,
    model.KeyElements.PROPERTY: model.Property,
    model.KeyElements.RANGE: model.Range,
    model.KeyElements.REFERENCE_ELEMENT: model.ReferenceElement,
    model.KeyElements.RELATIONSHIP_ELEMENT: model.RelationshipElement,
    model.KeyElements.SUBMODEL_ELEMENT: model.SubmodelElement,
    model.KeyElements.SUBMODEL_ELEMENT_COLLECTION: model.SubmodelElementCollection,
    model.KeyElements.VIEW: model.View,
}


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


def _expect_type(object: object, type: Type, context: str, failsafe: bool) -> bool:
    """
    Helper function to check type of an embedded object.

    This function may be used in any constructor function for an AAS object that expects to find already constructed
    AAS objects of a certain type within its data dict. In this case, we want to ensure that the object has this kind
    and raise a TypeError if not. In failsafe mode, we want to log the error and prevent the object from being added
    to the parent object. A typical use of this function would look like this:

      if _expect_type(element, model.SubmodelElement, str(submodel), failsafe):
          submodel.submodel_element.add(element)

    :param object: The object to by type-checked
    :param type: The expected type
    :param context: A string to add to the exception message / log message, that describes the context in that the
                    object has been found
    :param failsafe: Log error and return false instead of rasing a TypeError
    :return: True if the
    :raises TypeError: If the object is not of the expected type and the failsafe mode is not active
    """
    if isinstance(object, type):
        return True
    if failsafe:
        logger.warning("Expected a %s in %s.inputVariable, but found %s", type.__name__, context, object)
    else:
        raise TypeError("Expected a %s in %s.inputVariable, but found %s" % (type.__name__, context, object))
    return False


def _amend_abstract_attributes(obj: object, dct: Dict[str, object]) -> None:
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
            obj.description = _construct_lang_string_set(_get_ts(dct, 'description', list))
    if isinstance(obj, model.Identifiable):
        if 'idShort' in dct:
            obj.id_short = _get_ts(dct, 'idShort', str)
        if 'administration' in dct:
            obj.administration = _construct_administrative_information(_get_ts(dct, 'administration', dict))
    if isinstance(obj, model.HasDataSpecification):
        if 'embeddedDataSpecification' in dct:
            for data_spec_data in _get_ts(dct, 'embeddedDataSpecification', list):
                # TODO add failsafe-mode (catch TypeError, KeyError, log them and skip element)
                obj.data_specification.add(_construct_reference(data_spec_data))
    if isinstance(obj, model.HasSemantics):
        if 'semantic_id' in dct:
            obj.semantic_id = _construct_reference(_get_ts(dct, 'semanticId', dict))
    # HasKind provides only mandatory, immutable attributes
    if isinstance(obj, model.Qualifiable):
        if 'qualifiers' in dct:
            for qualifier_data in _get_ts(dct, 'qualifiers', list):
                # TODO add failsafe-mode (catch TypeError, KeyError, log them and skip element)
                obj.qualifier.add(_construct_qualifier(qualifier_data))


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
    # TODO remove type here
    return model.Reference(keys, model.Referable)


def _construct_aas_reference(dct: Dict[str, object], type_: Type[T]) -> model.Reference:
    keys = [_construct_key(key_data) for key_data in _get_ts(dct, "keys", list)]
    if keys and KEY_ELEMENTS_CLASSES.get(keys[-1].type_, None) != type_:
        logger.warning("type %s of last key of reference to %s does not match reference type %s",
                       keys[-1].type_.name, " / ".join(str(k) for k in keys), type_.__name__)
    # TODO use AASReference here
    return model.Reference(keys, type_)


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


def _construct_qualifier(dct: Dict[str, object]) -> model.Qualifier:
    ret = model.Qualifier(type_=_get_ts(dct, 'type', str),
                          value_type=_get_ts(dct, 'valueType', str))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = _get_ts(dct, 'value', str)
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'value', dict))
    return ret


def _construct_view(dct: Dict[str, object]) -> model.View:
    # TODO idShort needs to be added
    ret = model.View()
    _amend_abstract_attributes(ret, dct)
    # TODO semanticId needs to be added
    return ret


def _construct_security(dct: Dict[str, object]) -> model.Security:
    return model.Security()


def _construct_lang_string_set(lst: List[Dict[str, object]]) -> model.LangStringSet:
    # TODO add failsafe-mode (catch TypeError, KeyError, log them and skip single LangString)
    return {_get_ts(desc, 'language', str): _get_ts(desc, 'text', str)
            for desc in lst}


# #############################################################################
# Constructor Functions (for classes with `modelType`) starting from here
# #############################################################################

def construct_asset(dct: Dict[str, object]) -> model.Asset:
    return model.Asset(kind=ASSET_KIND_INVERSE[_get_ts(dct, 'kind', str)],
                       identification=_construct_identifier(_get_ts(dct, "identification", dict)))


def construct_asset_administration_shell(dct: Dict[str, object]) -> model.AssetAdministrationShell:
    ret = model.AssetAdministrationShell(
        asset=_construct_aas_reference(_get_ts(dct, 'asset', dict), model.Asset),
        identification=_construct_identifier(_get_ts(dct, 'identification', dict)))
    _amend_abstract_attributes(ret, dct)
    if 'submodels' in dct:
        for sm_data in _get_ts(dct, 'submodels', list):
            ret.submodel_.add(_construct_aas_reference(sm_data, model.Submodel))
    if 'view' in dct:
        for view_data in _get_ts(dct, 'views', list):
            ret.view.add(_construct_view(view_data))
    if 'conceptDictionaries' in dct:
        for concept_dictionary in _get_ts(dct, 'conceptDictionaries', list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(concept_dictionary, model.ConceptDictionary, str(ret), True):
                ret.concept_dictionary.add(concept_dictionary)
    if 'security' in dct:
        ret.security_ = _construct_security(_get_ts(dct, 'security', dict))
    return ret


def construct_concept_description(dct: Dict[str, object]) -> model.ConceptDescription:
    ret = model.ConceptDescription(identification=_construct_identifier(_get_ts(dct, 'identification', dict)))
    _amend_abstract_attributes(ret, dct)
    if 'isCaseOf' in dct:
        for case_data in _get_ts(dct, "inCaseOf", list):
            ret.is_case_of.add(_construct_reference(case_data))
    return ret


def construct_concept_dictionary(dct: Dict[str, object]) -> model.ConceptDictionary:
    ret = model.ConceptDictionary(_get_ts(dct, "idShort", str))
    _amend_abstract_attributes(ret, dct)
    if 'conceptDescriptions' in dct:
        for desc_data in _get_ts(dct, "conceptDescriptions", list):
            ret.concept_description.add(_construct_aas_reference(desc_data, model.ConceptDescription))
    return ret


def construct_entity(dct: Dict[str, object]) -> model.Entity:
    ret = model.Entity(id_short=_get_ts(dct, "idShort", str),
                       entity_type=ENTITY_TYPES_INVERSE[_get_ts(dct, "entityType", str)],
                       kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'statements' in dct:
        for element in _get_ts(dct, "statements", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(element, model.SubmodelElement, str(ret), True):
                ret.statement.add(element)
    return ret


def construct_submodel(dct: Dict[str, object]) -> model.Submodel:
    ret = model.Submodel(identification=_construct_identifier(_get_ts(dct, 'identification', dict)),
                         kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'submodelElements' in dct:
        for element in _get_ts(dct, "submodelElements", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(element, model.SubmodelElement, str(ret), True):
                ret.submodel_element.add(element)
    return ret


def construct_capability(dct: Dict[str, object]) -> model.Capability:
    ret = model.Capability(id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    return ret


def construct_basic_event(dct: Dict[str, object]) -> model.BasicEvent:
    ret = model.BasicEvent(id_short=_get_ts(dct, "idShort", str),
                           observed=_construct_reference(_get_ts(dct, 'observed', dict)),
                           kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    return ret


def construct_operation(dct: Dict[str, object]) -> model.Operation:
    ret = model.Operation(_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'inputVariable' in dct:
        for variable in _get_ts(dct, "inputVariable", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(variable, model.OperationVariable, "{}.inputVariable".format(ret), True):
                ret.input_variable.add(variable)
    if 'outputVariable' in dct:
        for variable in _get_ts(dct, "outputVariable", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(variable, model.OperationVariable, "{}.outputVariable".format(ret), True):
                ret.output_variable.add(variable)
    if 'inoutputVariable' in dct:
        for variable in _get_ts(dct, "inoutputVariable", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(variable, model.OperationVariable, "{}.inoutputVariable".format(ret), True):
                ret.in_output_variable.add(variable)
    return ret


def construct_operation_variable(dct: Dict[str, object]) -> model.OperationVariable:
    ret = model.OperationVariable(id_short=_get_ts(dct, "idShort", str),
                                  value=_get_ts(dct, 'value', model.SubmodelElement),
                                  kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    return ret


def construct_relationship_element(dct: Dict[str, object]) -> model.RelationshipElement:
    ret = model.RelationshipElement(id_short=_get_ts(dct, "idShort", str),
                                    first=_construct_reference(_get_ts(dct, 'first', dict)),
                                    second=_construct_reference(_get_ts(dct, 'second', dict)),
                                    kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    return ret


def construct_submodel_element_collection(dct: Dict[str, object]) -> model.SubmodelElementCollection:
    ret: model.SubmodelElementCollection
    if _get_ts(dct, 'ordered', bool):
        ret = model.SubmodelElementCollectionOrdered(
            id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    else:
        ret = model.SubmodelElementCollectionUnordered(
            id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        for element in _get_ts(dct, "value", list):
            # TODO add non-failsafe-mode (failsafe=False)
            if _expect_type(element, model.SubmodelElement, str(ret), True):
                ret.value.add(element)
    return ret


def construct_blob(dct: Dict[str, object]) -> model.Blob:
    ret = model.Blob(id_short=_get_ts(dct, "idShort", str),
                     mime_type=_get_ts(dct, "mimeType", str),
                     kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = base64.b64decode(_get_ts(dct, 'value', str))
    return ret


def construct_file(dct: Dict[str, object]) -> model.File:
    ret = model.File(id_short=_get_ts(dct, "idShort", str),
                     value=None,
                     mime_type=_get_ts(dct, "mimeType", str),
                     kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = _get_ts(dct, 'value', str)
    return ret


def construct_multi_language_property(dct: Dict[str, object]) -> model.MultiLanguageProperty:
    ret = model.MultiLanguageProperty(id_short=_get_ts(dct, "idShort", str), kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = _construct_lang_string_set(_get_ts(dct, 'value', list))
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'valueId', dict))
    return ret


def construct_property(dct: Dict[str, object]) -> model.Property:
    ret = model.Property(id_short=_get_ts(dct, "idShort", str),
                         value_type=_get_ts(dct, 'valueType', str),
                         kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = _get_ts(dct, 'value', str)
    if 'valueId' in dct:
        ret.value_id = _construct_reference(_get_ts(dct, 'valueId', dict))
    return ret


def construct_range(dct: Dict[str, object]) -> model.Range:
    ret = model.Range(id_short=_get_ts(dct, "idShort", str),
                      value_type=_get_ts(dct, 'valueType', str),
                      kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'min' in dct:
        ret.min_ = _get_ts(dct, 'min', str)
    if 'max' in dct:
        ret.max_ = _get_ts(dct, 'max', str)
    return ret


def construct_reference_element(dct: Dict[str, object]) -> model.ReferenceElement:
    ret = model.ReferenceElement(id_short=_get_ts(dct, "idShort", str),
                                 value=None,
                                 kind=_get_kind(dct))
    _amend_abstract_attributes(ret, dct)
    if 'value' in dct:
        ret.value = _construct_reference(_get_ts(dct, 'value', dict))
    return ret


# The following dict specifies a constructor function for all AAS classes that may be identified using the `modelType`
# attribute in their JSON representation. Each of those constructor functions takes the JSON representation of an object
# and tries to construct a Python object from it. Embedded objects that have a modelType themselves are expected to be
# converted to the correct PythonType already.
AAS_CLASS_PARSERS: Dict[str, Callable[[Dict[str, object]], object]] = {
    'Asset': construct_asset,
    'AssetAdministrationShell': construct_asset_administration_shell,
    'ConceptDescription': construct_concept_description,
    'Submodel': construct_submodel,
    'ConceptDictionary': construct_concept_dictionary,
    'Capability': construct_capability,
    'Entity': construct_entity,
    'BasicEvent': construct_basic_event,
    'Operation': construct_operation,
    'OperationVariable': construct_operation_variable,
    'RelationshipElement': construct_relationship_element,
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
    """
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(dct: Dict[str, object]) -> object:
        # TODO add non-failsafe mode, that raises an Exception instead of logging and continuing?
        if 'modelType' not in dct:
            return dct
        if not isinstance(dct['modelType'], dict) or 'name' not in dct['modelType']:
            logger.warning("JSON object has unexpected format of modelType: %s",
                           dct['modelType'])
            return dct
        model_type = dct['modelType']['name']
        if model_type not in AAS_CLASS_PARSERS:
            logger.warning("Found JSON object with modelType=\"%s\", which is not a known AAS class",
                           model_type)
            return dct
        # TODO add failsafe-mode (catch KeyErrors and TypeErrors, log them and return dct)
        return AAS_CLASS_PARSERS[model_type](dct)
