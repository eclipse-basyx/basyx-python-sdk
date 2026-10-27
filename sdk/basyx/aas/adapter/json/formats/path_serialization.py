# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, List

from basyx.aas import model

from ..json_serialization import AASToJsonEncoder


class PathJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes :class:`~basyx.aas.model.Referable` objects as the list of
    idShortPaths reachable from them (``$path`` content modifier).

    :param deep: If True (default), all descendants on all sublevels are included. If False, only
                 the requested element and its direct children are included. Compare to
                 SerializationModifier level.
    """

    def __init__(self, *args, deep: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.deep = deep

    def default(self, obj: object) -> object:
        if isinstance(obj, model.Referable):
            return self._referable_to_path(obj)
        return super().default(obj)

    def _referable_to_path(self, obj: model.Referable) -> List[str]:
        if isinstance(obj, model.Submodel):
            # Submodel is Identifiable; its idShort is optional and never part of an idShortPath.
            paths: List[str] = []
            self._append_children(paths, obj.submodel_element, prefix=[])
            return paths
        if obj.id_short is None:
            raise ValueError(f"{obj!r} has no idShort, so no idShortPath can be computed for it!")
        prefix = [obj.id_short]
        paths = [model.Referable.build_id_short_path(prefix)]
        if isinstance(obj, model.SubmodelElementList):
            self._append_indexed_children(paths, obj.value, prefix)
        elif isinstance(obj, model.SubmodelElementCollection):
            self._append_children(paths, obj.value, prefix)
        elif isinstance(obj, model.Entity):
            self._append_children(paths, obj.statement, prefix)
        elif isinstance(obj, model.AnnotatedRelationshipElement):
            self._append_children(paths, obj.annotation, prefix)
        # Other Referables are leaves with no further idShortPaths beyond self.
        return paths

    def _append_children(
        self, paths: List[str], children: Iterable[model.SubmodelElement], prefix: List[str]
    ) -> None:
        for child in children:
            child_prefix = prefix + [child.id_short]
            paths.append(model.Referable.build_id_short_path(child_prefix))
            if self.deep:
                self._recurse(paths, child, child_prefix)

    def _append_indexed_children(
        self, paths: List[str], children: Iterable[model.SubmodelElement], prefix: List[str]
    ) -> None:
        for index, child in enumerate(children):
            child_prefix = prefix + [str(index)]
            paths.append(model.Referable.build_id_short_path(child_prefix))
            if self.deep:
                self._recurse(paths, child, child_prefix)

    def _recurse(self, paths: List[str], element: object, prefix: List[str]) -> None:
        if isinstance(element, model.SubmodelElementList):
            self._append_indexed_children(paths, element.value, prefix)
        elif isinstance(element, model.SubmodelElementCollection):
            self._append_children(paths, element.value, prefix)
        elif isinstance(element, model.Entity):
            self._append_children(paths, element.statement, prefix)
        elif isinstance(element, model.AnnotatedRelationshipElement):
            self._append_children(paths, element.annotation, prefix)
        # Leaf elements have no children to traverse into.
