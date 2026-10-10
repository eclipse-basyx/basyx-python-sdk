# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Iterable, List

from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder


class PathJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes :class:`~basyx.aas.model.Referable` objects as the list of
    idShortPaths reachable from them (``$path`` content modifier).

    :cvar deep: If True (default), all descendants on all sublevels are included. If False, only
                the requested element and its direct children are included. Compare to
                SerializationModifier level.
    """

    deep: bool = True

    @classmethod
    def _get_aas_class_serializers(cls) -> dict[type, Callable]:
        serializers = super()._get_aas_class_serializers()
        serializers.update(
            {
                model.Submodel: cls._submodel_to_path,
                model.SubmodelElementCollection: cls._submodel_element_collection_to_path,
                model.SubmodelElementList: cls._submodel_element_list_to_path,
                model.Entity: cls._entity_to_path,
                model.AnnotatedRelationshipElement: cls._annotated_relationship_element_to_path,
                model.Property: cls._leaf_to_path,
                model.MultiLanguageProperty: cls._leaf_to_path,
                model.Range: cls._leaf_to_path,
                model.Blob: cls._leaf_to_path,
                model.File: cls._leaf_to_path,
                model.ReferenceElement: cls._leaf_to_path,
                model.RelationshipElement: cls._leaf_to_path,
                model.BasicEventElement: cls._leaf_to_path,
                model.Capability: cls._leaf_to_path,
                model.Operation: cls._leaf_to_path,
            }
        )
        return serializers

    @classmethod
    def _submodel_to_path(cls, obj: model.Submodel) -> List[str]:
        paths: List[str] = []
        cls._append_children(paths, obj.submodel_element, prefix=[])
        return paths

    @classmethod
    def _submodel_element_collection_to_path(cls, obj: model.SubmodelElementCollection) -> List[str]:
        paths, prefix = cls._self_path(obj)
        cls._append_children(paths, obj.value, prefix)
        return paths

    @classmethod
    def _submodel_element_list_to_path(cls, obj: model.SubmodelElementList) -> List[str]:
        paths, prefix = cls._self_path(obj)
        cls._append_indexed_children(paths, obj.value, prefix)
        return paths

    @classmethod
    def _entity_to_path(cls, obj: model.Entity) -> List[str]:
        paths, prefix = cls._self_path(obj)
        cls._append_children(paths, obj.statement, prefix)
        return paths

    @classmethod
    def _annotated_relationship_element_to_path(cls, obj: model.AnnotatedRelationshipElement) -> List[str]:
        paths, prefix = cls._self_path(obj)
        cls._append_children(paths, obj.annotation, prefix)
        return paths

    @classmethod
    def _leaf_to_path(cls, obj: model.Referable) -> List[str]:
        paths, _ = cls._self_path(obj)
        return paths

    @staticmethod
    def _self_path(obj: model.Referable) -> tuple[List[str], List[str]]:
        """Return (initial paths list containing the element's own path, prefix for children)."""
        if obj.id_short is None:
            raise ValueError(f"{obj!r} has no idShort, so no idShortPath can be computed for it!")
        prefix = [obj.id_short]
        return [model.Referable.build_id_short_path(prefix)], prefix

    @classmethod
    def _append_children(
        cls, paths: List[str], children: Iterable[model.SubmodelElement], prefix: List[str]
    ) -> None:
        for child in children:
            child_prefix = prefix + [child.id_short]
            paths.append(model.Referable.build_id_short_path(child_prefix))
            if cls.deep:
                cls._recurse(paths, child, child_prefix)

    @classmethod
    def _append_indexed_children(
        cls, paths: List[str], children: Iterable[model.SubmodelElement], prefix: List[str]
    ) -> None:
        for index, child in enumerate(children):
            child_prefix = prefix + [str(index)]
            paths.append(model.Referable.build_id_short_path(child_prefix))
            if cls.deep:
                cls._recurse(paths, child, child_prefix)

    @classmethod
    def _recurse(cls, paths: List[str], element: object, prefix: List[str]) -> None:
        if isinstance(element, model.SubmodelElementList):
            cls._append_indexed_children(paths, element.value, prefix)
        elif isinstance(element, model.SubmodelElementCollection):
            cls._append_children(paths, element.value, prefix)
        elif isinstance(element, model.Entity):
            cls._append_children(paths, element.statement, prefix)
        elif isinstance(element, model.AnnotatedRelationshipElement):
            cls._append_children(paths, element.annotation, prefix)
        # Leaf elements have no children to traverse into.


class ShallowPathJsonEncoder(PathJsonEncoder):
    """
    :class:`PathJsonEncoder` variant that emits only the requested element and its direct children
    (matches ``?level=core``).
    """

    deep: bool = False
