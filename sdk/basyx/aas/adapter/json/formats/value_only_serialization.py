# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import base64
import math
from typing import Callable, Iterable, Union

from basyx.aas import model
from basyx.aas.adapter import _generic
from basyx.aas.adapter.json import AASToJsonEncoder

TYPES_WITHOUT_VALUE_ONLY = (model.Capability, model.Operation)
CONTAINER_TYPES = (model.SubmodelElementCollection, model.SubmodelElementList)


class ValueOnlyJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes BaSyx Python SDK objects into the JSON format "ValueOnly" as defined by the
    specification.

    .. note::

        The specification contradicts itself at some points. In these cases the following assumptions were made:

        * ``annotations`` of an AnnotatedRelationshipElement and ``statements`` of an Entity are serialized as JSON
          object with the idShorts as names, as defined in the schema and the Entity example, instead of an array,
          as stated in the text.
        * ``specificAssetIds`` of an Entity are serialized as array of SpecificAssetIds in format "Normal", as stated
          in the text, instead of objects with string values only, as defined in the schema.
        * ``globalAssetId`` of an Entity is serialized as string, as defined in the schema and the metamodel, instead
          of a Reference, as shown in the Entity example.

    :param deep: If True (default), all children of the serialized object are included on all sublevels. If False,
                 only the serialized object and its direct children are included without their values. Compare to
                 serialization level ``core``.
    """

    @classmethod
    def _get_aas_class_serializers(cls) -> dict[type, Callable]:
        serializers = super()._get_aas_class_serializers()

        serializers.update(
            {
                model.Submodel: cls._submodel_to_value_only,
                model.SubmodelElementList: cls._submodel_element_list_to_value_only,
                model.SubmodelElementCollection: cls._submodel_element_collection_to_value_only,
                model.Property: cls._property_to_value_only,
                model.MultiLanguageProperty: cls._multi_language_property_to_value_only,
                model.Range: cls._range_to_value_only,
                model.File: cls._file_or_blob_to_value_only,
                model.Blob: cls._file_or_blob_to_value_only,
                model.ReferenceElement: cls._reference_element_to_value_only,
                model.RelationshipElement: cls._relationship_element_to_value_only,
                model.AnnotatedRelationshipElement: cls._annotated_relationship_element_to_value_only,
                model.Entity: cls._entity_to_value_only,
                model.BasicEventElement: cls._basic_event_element_to_value_only,
            }
        )
        # Capability and Operation have no ValueOnly representation
        for key in TYPES_WITHOUT_VALUE_ONLY:
            serializers.pop(key, None)

        return serializers

    @classmethod
    def _get_aas_class_no_children_serializers(cls) -> dict[type, Callable]:
        serializers = super()._get_aas_class_no_children_serializers()

        serializers.update(
            {
                model.Submodel: cls._submodel_to_value_only_no_children,
                model.SubmodelElementList: cls._submodel_element_list_to_value_only_no_children,
                model.SubmodelElementCollection: cls._submodel_element_collection_to_value_only_no_children,
                model.AnnotatedRelationshipElement: cls._annotated_relationship_element_to_value_only_no_children,
                model.Entity: cls._entity_to_value_only_no_children,
            }
        )

        return serializers

    @classmethod
    def _has_value(cls, obj: model.SubmodelElement) -> bool:
        if isinstance(obj, TYPES_WITHOUT_VALUE_ONLY):
            return False
        if isinstance(obj, model.Property):
            return obj.value is not None
        if isinstance(obj, model.MultiLanguageProperty):
            return bool(obj.value)
        if isinstance(obj, model.Range):
            return obj.min is not None or obj.max is not None
        if isinstance(obj, model.File):
            return obj.value is not None and obj.content_type is not None
        if isinstance(obj, model.Blob):
            return obj.content_type is not None
        if isinstance(obj, model.ReferenceElement):
            return obj.value is not None
        if isinstance(obj, model.RelationshipElement):
            return obj.first is not None or obj.second is not None
        if isinstance(obj, model.Entity):
            return (obj.global_asset_id is not None or bool(obj.specific_asset_id)
                    or any(cls._has_value(statement) for statement in obj.statement))
        if isinstance(obj, CONTAINER_TYPES):
            return any(cls._has_value(element) for element in obj.value)
        return True

    @classmethod
    def _submodel_to_value_only(cls, obj: model.Submodel) -> dict[str, object]:
        data: dict[str, object] = {}

        for element in obj.submodel_element:
            if cls._has_value(element):
                data[element.id_short] = element

        return data

    @classmethod
    def _submodel_element_list_to_value_only(
            cls, obj: model.SubmodelElementList
    ) -> list[object]:
        return [element for element in obj.value]

    @classmethod
    def _submodel_element_iterable_to_value_only(cls, it: Iterable[model.SubmodelElement]) -> dict[str, object]:
        return {
            element.id_short: element
            for element in it
            if cls._has_value(element) and element.id_short is not None
        }

    @classmethod
    def _submodel_element_collection_to_value_only(cls, obj: model.SubmodelElementCollection) -> dict[str, object]:
        data: dict[str, object] = cls._submodel_element_iterable_to_value_only(obj.value)
        return data

    @classmethod
    def _value_to_json_type(cls, value: model.datatypes.AnyXSDType) -> Union[bool, str, int, float]:
        if isinstance(value, (bool, model.datatypes.Boolean)):
            return bool(value)
        if isinstance(value, int):
            return value
        if isinstance(value, (float, model.datatypes.Decimal)):
            if not math.isfinite(float(value)):
                return model.datatypes.xsd_repr(value)
            return float(value)
        return model.datatypes.xsd_repr(value)

    @classmethod
    def _property_to_value_only(cls, obj: model.Property) -> object:
        if obj.value is not None:
            return cls._value_to_json_type(obj.value)
        return None

    @classmethod
    def _multi_language_property_to_value_only(cls, obj: model.MultiLanguageProperty) -> list[object]:
        value = obj.value
        if not value:
            return []
        return [{language: text} for language, text in sorted(value.items())]

    @classmethod
    def _range_to_value_only(cls, obj: model.Range) -> Union[object, dict[str, object]]:
        data: dict[str, object] = {}
        if obj.min is not None:
            data["min"] = cls._value_to_json_type(obj.min)
        if obj.max is not None:
            data["max"] = cls._value_to_json_type(obj.max)
        return data

    @classmethod
    def _file_or_blob_to_value_only(cls, obj: Union[model.Blob, model.File]) -> dict[str, object]:
        data: dict[str, object] = {}
        data["contentType"] = obj.content_type
        if obj.value is not None:
            data["value"] = base64.b64encode(obj.value).decode() if isinstance(obj, model.Blob) else obj.value
        return data

    @classmethod
    def _reference_element_to_value_only(cls, obj: model.ReferenceElement) -> object:
        return obj.value

    @classmethod
    def _relationship_element_to_value_only(cls, obj: model.RelationshipElement) -> dict[str, object]:
        data: dict[str, object] = {}
        if obj.first is not None:
            data["first"] = obj.first
        if obj.second is not None:
            data["second"] = obj.second
        return data

    @classmethod
    def _annotated_relationship_element_to_value_only(
            cls, obj: model.AnnotatedRelationshipElement
    ) -> dict[str, object]:
        data = cls._relationship_element_to_value_only(obj)
        if obj.annotation:
            data["annotations"] = cls._submodel_element_iterable_to_value_only(obj.annotation)
        return data

    @classmethod
    def _entity_to_value_only(cls, obj: model.Entity) -> object:
        data: dict[str, object] = {}
        if obj.statement:
            data["statements"] = cls._submodel_element_iterable_to_value_only(obj.statement)
        if obj.global_asset_id:
            data["globalAssetId"] = obj.global_asset_id
        if obj.specific_asset_id:
            data["specificAssetIds"] = list(obj.specific_asset_id)
        if obj.entity_type:
            data["entityType"] = _generic.ENTITY_TYPES[obj.entity_type]
        return data

    @classmethod
    def _basic_event_element_to_value_only(cls, obj: model.BasicEventElement) -> dict[str, object]:
        data: dict[str, object] = {"observed": obj.observed}
        return data

    # #############################################################
    # transformation functions to serialize with deep=False
    # #############################################################

    @classmethod
    def _remove_children(cls, obj: object) -> object:
        # The ValueOnly representation of SubmodelElementCollections and SubmodelElementLists consists only of their
        # children
        if isinstance(obj, model.SubmodelElementCollection):
            return {}
        if isinstance(obj, model.SubmodelElementList):
            return []
        return super()._remove_children(obj)

    @classmethod
    def _remove_children_of_elements(cls, data: dict[str, object]) -> dict[str, object]:
        return {id_short: cls._remove_children(element) for id_short, element in data.items()}

    @classmethod
    def _submodel_to_value_only_no_children(cls, obj: model.Submodel) -> dict[str, object]:
        data = cls._get_aas_class_serializers()[model.Submodel](obj)
        # Direct child SubmodelElementCollections and SubmodelElementLists are always serialized with an empty value,
        # even if they contain no elements with a value
        for element in obj.submodel_element:
            if isinstance(element, CONTAINER_TYPES) and element.id_short is not None:
                data.setdefault(element.id_short, element)
        return cls._remove_children_of_elements(data)

    @classmethod
    def _submodel_element_list_to_value_only_no_children(cls, obj: model.SubmodelElementList) -> list[object]:
        data = cls._get_aas_class_serializers()[model.SubmodelElementList](obj)
        return [cls._remove_children(element) for element in data]

    @classmethod
    def _submodel_element_collection_to_value_only_no_children(
            cls, obj: model.SubmodelElementCollection
    ) -> dict[str, object]:
        data = cls._get_aas_class_serializers()[model.SubmodelElementCollection](obj)
        # Direct child SubmodelElementCollections and SubmodelElementLists are always serialized with an empty value,
        # even if they contain no elements with a value
        for element in obj.value:
            if isinstance(element, CONTAINER_TYPES) and element.id_short is not None:
                data.setdefault(element.id_short, element)
        return cls._remove_children_of_elements(data)

    @classmethod
    def _annotated_relationship_element_to_value_only_no_children(
            cls, obj: model.AnnotatedRelationshipElement
    ) -> dict[str, object]:
        data = cls._get_aas_class_serializers()[model.AnnotatedRelationshipElement](obj)
        annotations = data.get("annotations")
        if isinstance(annotations, dict):
            # No checking for child SubmodelElementCollections and SubmodelElementLists neccessary
            data["annotations"] = cls._remove_children_of_elements(annotations)
        return data

    @classmethod
    def _entity_to_value_only_no_children(cls, obj: model.Entity) -> dict[str, object]:
        data = cls._get_aas_class_serializers()[model.Entity](obj)
        statements = data.get("statements")
        if isinstance(statements, dict):
            # Direct child SubmodelElementCollections and SubmodelElementLists are always serialized with an empty
            # value, even if they contain no elements with a value
            for element in obj.statement:
                if isinstance(element, CONTAINER_TYPES) and element.id_short is not None:
                    statements.setdefault(element.id_short, element)
            data["statements"] = cls._remove_children_of_elements(statements)
        return data
