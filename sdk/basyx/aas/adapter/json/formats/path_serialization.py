# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, List, Tuple

from basyx.aas import model

from ..json_serialization import AASToJsonEncoder


# Types for which the $path content modifier returns the idShort of the requested element and a list
# of idShort paths to its child elements (AAS API Part 2).
_PATH_SUPPORTED_TYPES: Tuple[type, ...] = (
    model.Submodel,
    model.SubmodelElementCollection,
    model.SubmodelElementList,
    model.AnnotatedRelationshipElement,
    model.Entity,
)


class PathJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes selected AAS objects as the list of idShortPaths reachable
    from them (``$path`` content modifier). Supported inputs are :class:`~basyx.aas.model.Submodel`,
    :class:`~basyx.aas.model.SubmodelElementCollection`, :class:`~basyx.aas.model.SubmodelElementList`,
    :class:`~basyx.aas.model.AnnotatedRelationshipElement`, and :class:`~basyx.aas.model.Entity`.
    Any other type raises :class:`TypeError`.

    :param deep: If True (default), all descendants on all sublevels are included. If False, only
                 the requested element and its direct children are included. Compare to
                 SerializationModifier level.
    """

    def __init__(self, *args, deep: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.deep = deep

    def default(self, obj: object) -> object:
        if isinstance(obj, _PATH_SUPPORTED_TYPES):
            return self._referable_to_path(obj)
        raise TypeError(
            f"Object of type {type(obj).__name__} has no $path representation; "
            f"supported types are: {', '.join(t.__name__ for t in _PATH_SUPPORTED_TYPES)}."
        )

    def _referable_to_path(self, obj: model.Referable) -> List[str]:
        if isinstance(obj, model.Submodel):
            # Submodel is Identifiable; its idShort is optional and never part of an idShortPath.
            paths: List[str] = []
            self._append_children(paths, obj.submodel_element, prefix=[])
            return paths
        # For the remaining supported types the idShort of the requested element is the root of
        # every returned idShortPath. If it is missing, no path can be computed from this element.
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
        return paths

    def _append_children(
        self, paths: List[str], children: Iterable[model.SubmodelElement], prefix: List[str]
    ) -> None:
        for child in children:
            if child.id_short is None:
                raise ValueError(
                    f"{child!r} has no idShort, so no idShortPath can be computed for it!"
                )
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
