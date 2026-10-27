# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
from typing import Dict

from basyx.aas import model

from ..json_serialization import AASToJsonEncoder


class MetadataJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes BaSyx Python SDK objects into the JSON format "Metadata". This equals
    the normal serialization format but omits certain keys.
    """

    @classmethod
    def _asset_administration_shell_to_json(
        cls, obj: model.AssetAdministrationShell
    ) -> Dict[str, object]:
        data = super()._asset_administration_shell_to_json(obj)
        data.pop("assetInformation", None)
        data.pop("submodels", None)
        return data

    @classmethod
    def _submodel_to_json(
        cls, obj: model.Submodel
    ) -> Dict[str, object]:
        data = super()._submodel_to_json(obj)
        data.pop("submodelElements", None)
        return data

    @classmethod
    def _submodel_element_collection_to_json(
        cls, obj: model.SubmodelElementCollection
    ) -> Dict[str, object]:
        data = super()._submodel_element_collection_to_json(obj)
        data.pop("value", None)
        return data

    @classmethod
    def _submodel_element_list_to_json(
        cls, obj: model.SubmodelElementList
    ) -> Dict[str, object]:
        data = super()._submodel_element_list_to_json(obj)
        data.pop("value", None)
        return data

    @classmethod
    def _entity_to_json(cls, obj: model.Entity) -> Dict[str, object]:
        data = super()._entity_to_json(obj)
        data.pop("statements", None)
        data.pop("globalAssetId", None)
        data.pop("specificAssetIds", None)
        return data

    @classmethod
    def _basic_event_element_to_json(
        cls, obj: model.BasicEventElement
    ) -> Dict[str, object]:
        data = super()._basic_event_element_to_json(obj)
        data.pop("observed", None)
        return data

    @classmethod
    def _property_to_json(cls, obj: model.Property) -> Dict[str, object]:
        data = super()._property_to_json(obj)
        data.pop("value", None)
        data.pop("valueId", None)
        return data

    @classmethod
    def _multi_language_property_to_json(cls, obj: model.MultiLanguageProperty) -> Dict[str, object]:
        data = super()._multi_language_property_to_json(obj)
        data.pop("value", None)
        data.pop("valueId", None)
        return data

    @classmethod
    def _range_to_json(cls, obj: model.Range) -> Dict[str, object]:
        data = super()._range_to_json(obj)
        data.pop("min", None)
        data.pop("max", None)
        return data

    @classmethod
    def _reference_element_to_json(
        cls, obj: model.ReferenceElement
    ) -> Dict[str, object]:
        data = super()._reference_element_to_json(obj)
        data.pop("value", None)
        return data

    @classmethod
    def _relationship_element_to_json(
        cls, obj: model.RelationshipElement
    ) -> Dict[str, object]:
        data = super()._relationship_element_to_json(obj)
        data.pop("first", None)
        data.pop("second", None)
        return data

    @classmethod
    def _annotated_relationship_element_to_json(
        cls, obj: model.AnnotatedRelationshipElement
    ) -> Dict[str, object]:
        data = super()._annotated_relationship_element_to_json(obj)
        data.pop("first", None)
        data.pop("second", None)
        data.pop("annotations", None)
        return data

    @classmethod
    def _blob_to_json(cls, obj: model.Blob) -> Dict[str, object]:
        data = super()._blob_to_json(obj)
        data.pop("value", None)
        data.pop("contentType", None)
        return data

    @classmethod
    def _file_to_json(cls, obj: model.File) -> Dict[str, object]:
        data = super()._file_to_json(obj)
        data.pop("value", None)
        data.pop("contentType", None)
        return data
