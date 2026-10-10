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

class AASToValueOnlyJsonEncoder(AASToJsonEncoder):

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
            return obj.global_asset_id is not None or bool(obj.specific_asset_id)
        if isinstance(obj, (model.SubmodelElementList, model.SubmodelElementCollection)):
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
