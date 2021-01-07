# Copyright 2020 PyI40AAS Contributors
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
Module for serializing Asset Administration Shell objects to the official JSON format

The module provides an custom JSONEncoder class `AASToJsonEncoder` to be used with the Python standard `json` module.
It contains a custom `default` function which converts PyI40AAS objects to simple python types for an automatic
JSON serialization. Additionally, there's the `write_aas_json_file()` function, that takes a complete ObjectStore and
writes all contained AAS objects into a JSON file.

This job is performed in an iterative approach: The `default()` function gets called for every object and checks if an
object is an PyI40AAS object. In this case, it calls a special function for the respective PyI40AAS class which converts
the object (but not the contained objects) into a simple Python dict, which is serializable. Any contained
PyI40AAS objects are included into the dict as they are to be converted later on. The special helper function
`abstract_classes_to_json()` is called by most of the conversion functions to handle all the attributes of abstract base
classes.
"""
import base64
import inspect
from typing import List, Dict, IO, Optional, Type
import json

from aas import model
from .. import _generic


class AASToJsonEncoder(json.JSONEncoder):
    """
    Custom JSONDecoder class to use the `json` module for serializing Asset Administration Shell data into the
    official JSON format

    The class overrides the `default()` method to transform PyI40AAS objects into dicts that may be serialized by the
    standard encode method. Typical usage:

        json_string = json.dumps(data, cls=AASToJsonEncoder)

    :cvar stripped: If True, the JSON objects will be serialized in a stripped manner, excluding some attributes.
                    Defaults to False.
                    See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
    """
    stripped = False

    def default(self, obj: object) -> object:
        if isinstance(obj, model.AssetAdministrationShell):
            return self._asset_administration_shell_to_json(obj)
        if isinstance(obj, model.Asset):
            return self._asset_to_json(obj)
        if isinstance(obj, model.Identifier):
            return self._identifier_to_json(obj)
        if isinstance(obj, model.AdministrativeInformation):
            return self._administrative_information_to_json(obj)
        if isinstance(obj, model.Reference):
            return self._reference_to_json(obj)
        if isinstance(obj, model.Key):
            return self._key_to_json(obj)
        if isinstance(obj, model.ValueReferencePair):
            return self._value_reference_pair_to_json(obj)
        if isinstance(obj, model.AssetInformation):
            return self._asset_information_to_json(obj)
        if isinstance(obj, model.IdentifierKeyValuePair):
            return self._identifier_key_value_pair_to_json(obj)
        if isinstance(obj, model.Submodel):
            return self._submodel_to_json(obj)
        if isinstance(obj, model.Operation):
            return self._operation_to_json(obj)
        if isinstance(obj, model.OperationVariable):
            return self._operation_variable_to_json(obj)
        if isinstance(obj, model.Capability):
            return self._capability_to_json(obj)
        if isinstance(obj, model.BasicEvent):
            return self._basic_event_to_json(obj)
        if isinstance(obj, model.Entity):
            return self._entity_to_json(obj)
        if isinstance(obj, model.View):
            return self._view_to_json(obj)
        if isinstance(obj, model.ConceptDescription):
            return self._concept_description_to_json(obj)
        if isinstance(obj, model.Property):
            return self._property_to_json(obj)
        if isinstance(obj, model.Range):
            return self._range_to_json(obj)
        if isinstance(obj, model.MultiLanguageProperty):
            return self._multi_language_property_to_json(obj)
        if isinstance(obj, model.File):
            return self._file_to_json(obj)
        if isinstance(obj, model.Blob):
            return self._blob_to_json(obj)
        if isinstance(obj, model.ReferenceElement):
            return self._reference_element_to_json(obj)
        if isinstance(obj, model.SubmodelElementCollection):
            return self._submodel_element_collection_to_json(obj)
        if isinstance(obj, model.AnnotatedRelationshipElement):
            return self._annotated_relationship_element_to_json(obj)
        if isinstance(obj, model.RelationshipElement):
            return self._relationship_element_to_json(obj)
        if isinstance(obj, model.Qualifier):
            return self._qualifier_to_json(obj)
        if isinstance(obj, model.Extension):
            return self._extension_to_json(obj)
        return super().default(obj)

    @classmethod
    def _abstract_classes_to_json(cls, obj: object) -> Dict[str, object]:
        """
        transformation function to serialize abstract classes from model.base which are inherited by many classes

        :param obj: object which must be serialized
        :return: dict with the serialized attributes of the abstract classes this object inherits from
        """
        data: Dict[str, object] = {}
        if isinstance(obj, model.HasExtension) and not cls.stripped:
            if obj.extension:
                data['extensions'] = list(obj.extension)
        if isinstance(obj, model.Referable):
            if obj.id_short:
                data['idShort'] = obj.id_short
            if obj.display_name:
                data['displayName'] = cls._lang_string_set_to_json(obj.display_name)
            if obj.category:
                data['category'] = obj.category
            if obj.description:
                data['description'] = cls._lang_string_set_to_json(obj.description)
            try:
                ref_type = next(iter(t for t in inspect.getmro(type(obj)) if t in model.KEY_ELEMENTS_CLASSES))
            except StopIteration as e:
                raise TypeError("Object of type {} is Referable but does not inherit from a known AAS type"
                                .format(obj.__class__.__name__)) from e
            data['modelType'] = {'name': ref_type.__name__}
        if isinstance(obj, model.Identifiable):
            data['identification'] = obj.identification
            if obj.administration:
                data['administration'] = obj.administration
        if isinstance(obj, model.HasSemantics):
            if obj.semantic_id:
                data['semanticId'] = obj.semantic_id
        if isinstance(obj, model.HasKind):
            if obj.kind is model.ModelingKind.TEMPLATE:
                data['kind'] = _generic.MODELING_KIND[obj.kind]
        if isinstance(obj, model.Qualifiable) and not cls.stripped:
            if obj.qualifier:
                data['qualifiers'] = list(obj.qualifier)
        return data

    # #############################################################
    # transformation functions to serialize classes from model.base
    # #############################################################

    @classmethod
    def _lang_string_set_to_json(cls, obj: model.LangStringSet) -> List[Dict[str, object]]:
        return [{'language': k, 'text': v}
                for k, v in obj.items()]

    @classmethod
    def _key_to_json(cls, obj: model.Key) -> Dict[str, object]:
        """
        serialization of an object from class Key to json

        :param obj: object of class Key
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'type': _generic.KEY_ELEMENTS[obj.type],
                     'idType': _generic.KEY_TYPES[obj.id_type],
                     'value': obj.value})
        return data

    @classmethod
    def _administrative_information_to_json(cls, obj: model.AdministrativeInformation) -> Dict[str, object]:
        """
        serialization of an object from class AdministrativeInformation to json

        :param obj: object of class AdministrativeInformation
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.version:
            data['version'] = obj.version
            if obj.revision:
                data['revision'] = obj.revision
        return data

    @classmethod
    def _identifier_to_json(cls, obj: model.Identifier) -> Dict[str, object]:
        """
        serialization of an object from class Identifier to json

        :param obj: object of class Identifier
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['id'] = obj.id
        data['idType'] = _generic.IDENTIFIER_TYPES[obj.id_type]
        return data

    @classmethod
    def _reference_to_json(cls, obj: model.Reference) -> Dict[str, object]:
        """
        serialization of an object from class Reference to json

        :param obj: object of class Reference
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['keys'] = list(obj.key)
        return data

    @classmethod
    def _constraint_to_json(cls, obj: model.Constraint) -> Dict[str, object]:  # TODO check if correct for each class
        """
        serialization of an object from class Constraint to json

        :param obj: object of class Constraint
        :return: dict with the serialized attributes of this object
        """
        CONSTRAINT_CLASSES = [model.Qualifier]
        try:
            const_type = next(iter(t for t in inspect.getmro(type(obj)) if t in CONSTRAINT_CLASSES))
        except StopIteration as e:
            raise TypeError("Object of type {} is a Constraint but does not inherit from a known AAS Constraint type"
                            .format(obj.__class__.__name__)) from e
        return {'modelType': {'name': const_type.__name__}}

    @classmethod
    def _namespace_to_json(cls, obj):  # not in specification yet
        """
        serialization of an object from class Namespace to json

        :param obj: object of class Namespace
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        return data

    @classmethod
    def _qualifier_to_json(cls, obj: model.Qualifier) -> Dict[str, object]:
        """
        serialization of an object from class Qualifier to json

        :param obj: object of class Qualifier
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update(cls._constraint_to_json(obj))
        if obj.value:
            data['value'] = model.datatypes.xsd_repr(obj.value) if obj.value is not None else None
        if obj.value_id:
            data['valueId'] = obj.value_id
        data['valueType'] = model.datatypes.XSD_TYPE_NAMES[obj.value_type]
        data['type'] = obj.type
        return data

    @classmethod
    def _extension_to_json(cls, obj: model.Extension) -> Dict[str, object]:
        """
        serialization of an object from class Extension to json

        :param obj: object of class Extension
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.value:
            data['value'] = model.datatypes.xsd_repr(obj.value) if obj.value is not None else None
        if obj.refers_to:
            data['refersTo'] = obj.refers_to
        if obj.value_type:
            data['valueType'] = model.datatypes.XSD_TYPE_NAMES[obj.value_type]
        data['name'] = obj.name
        return data

    @classmethod
    def _value_reference_pair_to_json(cls, obj: model.ValueReferencePair) -> Dict[str, object]:
        """
        serialization of an object from class ValueReferencePair to json

        :param obj: object of class ValueReferencePair
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'value': model.datatypes.xsd_repr(obj.value),
                     'valueId': obj.value_id,
                     'valueType': model.datatypes.XSD_TYPE_NAMES[obj.value_type]})
        return data

    @classmethod
    def _value_list_to_json(cls, obj: model.ValueList) -> Dict[str, object]:
        """
        serialization of an object from class ValueList to json

        :param obj: object of class ValueList
        :return: dict with the serialized attributes of this object
        """
        return {'valueReferencePairTypes': list(obj)}

    # ############################################################
    # transformation functions to serialize classes from model.aas
    # ############################################################

    @classmethod
    def _view_to_json(cls, obj: model.View) -> Dict[str, object]:
        """
        serialization of an object from class View to json

        :param obj: object of class View
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.contained_element:
            data['containedElements'] = list(obj.contained_element)
        return data

    @classmethod
    def _asset_to_json(cls, obj: model.Asset) -> Dict[str, object]:
        """
        serialization of an object from class Asset to json

        :param obj: object of class Asset
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        return data

    @classmethod
    def _identifier_key_value_pair_to_json(cls, obj: model.IdentifierKeyValuePair) -> Dict[str, object]:
        """
        serialization of an object from class IdentifierKeyValuePair to json

        :param obj: object of class IdentifierKeyValuePair
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['key'] = obj.key
        data['value'] = obj.value
        data['subjectId'] = obj.external_subject_id
        return data

    @classmethod
    def _asset_information_to_json(cls, obj: model.AssetInformation) -> Dict[str, object]:
        """
        serialization of an object from class AssetInformation to json

        :param obj: object of class AssetInformation
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['assetKind'] = _generic.ASSET_KIND[obj.asset_kind]
        if obj.global_asset_id:
            data['globalAssetId'] = obj.global_asset_id
        if obj.specific_asset_id:
            data['externalAssetIds'] = list(obj.specific_asset_id)
        if obj.bill_of_material:
            data['billOfMaterial'] = list(obj.bill_of_material)
        if obj.default_thumbnail:
            data['thumbnail'] = obj.default_thumbnail
        return data

    @classmethod
    def _concept_description_to_json(cls, obj: model.ConceptDescription) -> Dict[str, object]:
        """
        serialization of an object from class ConceptDescription to json

        :param obj: object of class ConceptDescription
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.is_case_of:
            data['isCaseOf'] = list(obj.is_case_of)

        if isinstance(obj, model.concept.IEC61360ConceptDescription):
            cls._append_iec61360_concept_description_attrs(obj, data)

        return data

    @classmethod
    def _append_iec61360_concept_description_attrs(cls, obj: model.concept.IEC61360ConceptDescription,
                                                   data: Dict[str, object]) -> None:
        """
        Add the 'embeddedDataSpecifications' attribute to IEC61360ConceptDescription's JSON representation.

        `IEC61360ConceptDescription` is not a distinct class according DotAAS, but instead is built by referencing
        "DataSpecificationIEC61360" as dataSpecification. However, we implemented it as an explicit class, inheriting
        from ConceptDescription, but we want to generate compliant JSON documents. So, we fake the JSON structure of an
        object with dataSpecifications.
        """
        data_spec: Dict[str, object] = {
            'preferredName': cls._lang_string_set_to_json(obj.preferred_name)
        }
        if obj.data_type is not None:
            data_spec['dataType'] = _generic.IEC61360_DATA_TYPES[obj.data_type]
        if obj.definition is not None:
            data_spec['definition'] = cls._lang_string_set_to_json(obj.definition)
        if obj.short_name is not None:
            data_spec['shortName'] = cls._lang_string_set_to_json(obj.short_name)
        if obj.unit is not None:
            data_spec['unit'] = obj.unit
        if obj.unit_id is not None:
            data_spec['unitId'] = obj.unit_id
        if obj.source_of_definition is not None:
            data_spec['sourceOfDefinition'] = obj.source_of_definition
        if obj.symbol is not None:
            data_spec['symbol'] = obj.symbol
        if obj.value_format is not None:
            data_spec['valueFormat'] = model.datatypes.XSD_TYPE_NAMES[obj.value_format]
        if obj.value_list is not None:
            data_spec['valueList'] = cls._value_list_to_json(obj.value_list)
        if obj.value is not None:
            data_spec['value'] = model.datatypes.xsd_repr(obj.value) if obj.value is not None else None
        if obj.value_id is not None:
            data_spec['valueId'] = obj.value_id
        if obj.level_types:
            data_spec['levelType'] = [_generic.IEC61360_LEVEL_TYPES[lt] for lt in obj.level_types]
        data['embeddedDataSpecifications'] = [
            {'dataSpecification': model.Reference((
                model.Key(model.KeyElements.GLOBAL_REFERENCE,
                          "http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0",
                          model.KeyType.IRI),)),
             'dataSpecificationContent': data_spec}
        ]

    @classmethod
    def _asset_administration_shell_to_json(cls, obj: model.AssetAdministrationShell) -> Dict[str, object]:
        """
        serialization of an object from class AssetAdministrationShell to json

        :param obj: object of class AssetAdministrationShell
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update(cls._namespace_to_json(obj))
        if obj.derived_from:
            data["derivedFrom"] = obj.derived_from
        if obj.asset_information:
            data["assetInformation"] = obj.asset_information
        if not cls.stripped and obj.submodel:
            data["submodels"] = list(obj.submodel)
        if not cls.stripped and obj.view:
            data["views"] = list(obj.view)
        if obj.security:
            data["security"] = obj.security
        return data

    # #################################################################
    # transformation functions to serialize classes from model.security
    # #################################################################

    @classmethod
    def _security_to_json(cls, obj: model.Security) -> Dict[str, object]:  # has no attributes in our implementation
        """
        serialization of an object from class Security to json

        :param obj: object of class Security
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        return data

    # #################################################################
    # transformation functions to serialize classes from model.submodel
    # #################################################################

    @classmethod
    def _submodel_to_json(cls, obj: model.Submodel) -> Dict[str, object]:  # TODO make kind optional
        """
        serialization of an object from class Submodel to json

        :param obj: object of class Submodel
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if not cls.stripped and obj.submodel_element != set():
            data['submodelElements'] = list(obj.submodel_element)
        return data

    @classmethod
    def _data_element_to_json(cls, obj: model.DataElement) -> Dict[str, object]:  # no attributes in specification yet
        """
        serialization of an object from class DataElement to json

        :param obj: object of class DataElement
        :return: dict with the serialized attributes of this object
        """
        return {}

    @classmethod
    def _property_to_json(cls, obj: model.Property) -> Dict[str, object]:
        """
        serialization of an object from class Property to json

        :param obj: object of class Property
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['value'] = model.datatypes.xsd_repr(obj.value) if obj.value is not None else None
        if obj.value_id:
            data['valueId'] = obj.value_id
        data['valueType'] = model.datatypes.XSD_TYPE_NAMES[obj.value_type]
        return data

    @classmethod
    def _multi_language_property_to_json(cls, obj: model.MultiLanguageProperty) -> Dict[str, object]:
        """
        serialization of an object from class MultiLanguageProperty to json

        :param obj: object of class MultiLanguageProperty
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.value:
            data['value'] = cls._lang_string_set_to_json(obj.value)
        if obj.value_id:
            data['valueId'] = obj.value_id
        return data

    @classmethod
    def _range_to_json(cls, obj: model.Range) -> Dict[str, object]:
        """
        serialization of an object from class Range to json

        :param obj: object of class Range
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'valueType': model.datatypes.XSD_TYPE_NAMES[obj.value_type],
                     'min': model.datatypes.xsd_repr(obj.min) if obj.min is not None else None,
                     'max': model.datatypes.xsd_repr(obj.max) if obj.max is not None else None})
        return data

    @classmethod
    def _blob_to_json(cls, obj: model.Blob) -> Dict[str, object]:
        """
        serialization of an object from class Blob to json

        :param obj: object of class Blob
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['mimeType'] = obj.mime_type
        if obj.value is not None:
            data['value'] = base64.b64encode(obj.value).decode()
        return data

    @classmethod
    def _file_to_json(cls, obj: model.File) -> Dict[str, object]:
        """
        serialization of an object from class File to json

        :param obj: object of class File
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'value': obj.value, 'mimeType': obj.mime_type})
        return data

    @classmethod
    def _reference_element_to_json(cls, obj: model.ReferenceElement) -> Dict[str, object]:
        """
        serialization of an object from class Reference to json

        :param obj: object of class Reference
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.value:
            data['value'] = obj.value
        return data

    @classmethod
    def _submodel_element_collection_to_json(cls, obj: model.SubmodelElementCollection) -> Dict[str, object]:
        """
        serialization of an object from class SubmodelElementCollectionOrdered and SubmodelElementCollectionUnordered to
        json

        :param obj: object of class SubmodelElementCollectionOrdered and SubmodelElementCollectionUnordered
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if not cls.stripped and obj.value:
            data['value'] = list(obj.value)
        data['ordered'] = obj.ordered
        return data

    @classmethod
    def _relationship_element_to_json(cls, obj: model.RelationshipElement) -> Dict[str, object]:
        """
        serialization of an object from class RelationshipElement to json

        :param obj: object of class RelationshipElement
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'first': obj.first, 'second': obj.second})
        return data

    @classmethod
    def _annotated_relationship_element_to_json(cls, obj: model.AnnotatedRelationshipElement) -> Dict[str, object]:
        """
        serialization of an object from class AnnotatedRelationshipElement to json

        :param obj: object of class AnnotatedRelationshipElement
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update({'first': obj.first, 'second': obj.second})
        if not cls.stripped and obj.annotation:
            data['annotation'] = list(obj.annotation)
        return data

    @classmethod
    def _operation_variable_to_json(cls, obj: model.OperationVariable) -> Dict[str, object]:
        """
        serialization of an object from class OperationVariable to json

        :param obj: object of class OperationVariable
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['value'] = obj.value
        return data

    @classmethod
    def _operation_to_json(cls, obj: model.Operation) -> Dict[str, object]:
        """
        serialization of an object from class Operation to json

        :param obj: object of class Operation
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if obj.input_variable:
            data['inputVariable'] = list(obj.input_variable)
        if obj.output_variable:
            data['outputVariable'] = list(obj.output_variable)
        if obj.in_output_variable:
            data['inoutputVariable'] = list(obj.in_output_variable)
        return data

    @classmethod
    def _capability_to_json(cls, obj: model.Capability) -> Dict[str, object]:
        """
        serialization of an object from class Capability to json

        :param obj: object of class Capability
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        # no attributes in specification yet
        return data

    @classmethod
    def _entity_to_json(cls, obj: model.Entity) -> Dict[str, object]:
        """
        serialization of an object from class Entity to json

        :param obj: object of class Entity
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        if not cls.stripped and obj.statement:
            data['statements'] = list(obj.statement)
        data['entityType'] = _generic.ENTITY_TYPES[obj.entity_type]
        if obj.global_asset_id:
            data['globalAssetId'] = obj.global_asset_id
        if obj.specific_asset_id:
            data['externalAssetId'] = obj.specific_asset_id
        return data

    @classmethod
    def _event_to_json(cls, obj: model.Event) -> Dict[str, object]:  # no attributes in specification yet
        """
        serialization of an object from class Event to json

        :param obj: object of class Event
        :return: dict with the serialized attributes of this object
        """
        return {}

    @classmethod
    def _basic_event_to_json(cls, obj: model.BasicEvent) -> Dict[str, object]:
        """
        serialization of an object from class BasicEvent to json

        :param obj: object of class BasicEvent
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['observed'] = obj.observed
        return data


class StrippedAASToJsonEncoder(AASToJsonEncoder):
    """
    AASToJsonEncoder for stripped objects. Used in the HTTP API.
    See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
    """
    stripped = True


def _select_encoder(stripped: bool, encoder: Optional[Type[AASToJsonEncoder]] = None) -> Type[AASToJsonEncoder]:
    """
    Returns the correct encoder based on the stripped parameter. If an encoder class is given, stripped is ignored.

    :param stripped: If true, an encoder for parsing stripped JSON objects is selected. Ignored if an encoder class is
                     specified.
    :param encoder: Is returned, if specified.
    :return: A AASToJsonEncoder (sub)class.
    """
    if encoder is not None:
        return encoder
    return AASToJsonEncoder if not stripped else StrippedAASToJsonEncoder


def _create_dict(data: model.AbstractObjectStore) -> dict:
    # separate different kind of objects
    assets = []
    asset_administration_shells = []
    submodels = []
    concept_descriptions = []
    for obj in data:
        if isinstance(obj, model.Asset):
            assets.append(obj)
        if isinstance(obj, model.AssetAdministrationShell):
            asset_administration_shells.append(obj)
        if isinstance(obj, model.Submodel):
            submodels.append(obj)
        if isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)
    dict_ = {
        'assetAdministrationShells': asset_administration_shells,
        'submodels': submodels,
        'assets': assets,
        'conceptDescriptions': concept_descriptions,
    }
    return dict_


def object_store_to_json(data: model.AbstractObjectStore, stripped: bool = False,
                         encoder: Optional[Type[AASToJsonEncoder]] = None, **kwargs) -> str:
    """
    Create a json serialization of a set of AAS objects according to 'Details of the Asset Administration Shell',
    chapter 5.5

    :param data: ObjectStore which contains different objects of the AAS meta model which should be serialized to a
                 JSON file
    :param stripped: If true, objects are serialized to stripped json objects..
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if an encoder class is specified.
    :param encoder: The encoder class used to encoder the JSON objects
    :param kwargs: Additional keyword arguments to be passed to json.dump()
    """
    encoder_ = _select_encoder(stripped, encoder)
    # serialize object to json
    return json.dumps(_create_dict(data), cls=encoder_, **kwargs)


def write_aas_json_file(file: IO, data: model.AbstractObjectStore, stripped: bool = False,
                        encoder: Optional[Type[AASToJsonEncoder]] = None, **kwargs) -> None:
    """
    Write a set of AAS objects to an Asset Administration Shell JSON file according to 'Details of the Asset
    Administration Shell', chapter 5.5

    :param file: A file-like object to write the JSON-serialized data to
    :param data: ObjectStore which contains different objects of the AAS meta model which should be serialized to a
                 JSON file
    :param stripped: If true, objects are serialized to stripped json objects..
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if an encoder class is specified.
    :param encoder: The encoder class used to encoder the JSON objects
    :param kwargs: Additional keyword arguments to be passed to json.dumps()
    """
    encoder_ = _select_encoder(stripped, encoder)
    # serialize object to json
    json.dump(_create_dict(data), file, cls=encoder_, **kwargs)
