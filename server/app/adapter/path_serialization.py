# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Implements the "Path" SerializationModifier
"""
from typing import List

from basyx.aas import model


def compute_id_short_paths(referable: model.Referable, deep: bool, include_self: bool) -> List[str]:
    """
    Computes the list of idShortPaths for ``referable``, as returned by the ``$path`` content modifier.

    :param referable: The requested element to compute idShortPaths for.
    :param deep: If True, all descendants on all sublevels are included (default). If False, only the requested element
     and its direct children are included.
    :param include_self: Whether the idShortPath of ``referable`` itself is included as the first entry.
        This should be false for Identifiables (e.g. Submodel), since idShortPaths are not defined for them
        as their idShort is optional.
    :return: The list of idShortPaths
    """
    paths: List[str] = []
    prefix: List[str] = []
    if include_self:
        if referable.id_short is None:
            raise ValueError(f"{referable!r} has no idShort, so no idShortPath can be computed for it!")
        prefix = [referable.id_short]
        paths.append(model.Referable.build_id_short_path(prefix))
    _append_child_paths(paths, referable, prefix, deep)
    return paths


def _append_child_paths(paths: List[str], element: object, prefix: List[str], deep: bool) -> None:
    if isinstance(element, model.SubmodelElementList):
        for index, child in enumerate(element.value):
            child_prefix = prefix + [str(index)]
            paths.append(model.Referable.build_id_short_path(child_prefix))
            if deep:
                _append_child_paths(paths, child, child_prefix, deep)
        return

    if isinstance(element, model.Submodel):
        children: model.NamespaceSet = element.submodel_element
    elif isinstance(element, model.SubmodelElementCollection):
        children = element.value
    elif isinstance(element, model.Entity):
        children = element.statement
    elif isinstance(element, model.AnnotatedRelationshipElement):
        children = element.annotation
    else:
        # Leaf elements dont have children to traverse into.
        return

    for child in children:
        child_prefix = prefix + [child.id_short]
        paths.append(model.Referable.build_id_short_path(child_prefix))
        if deep:
            _append_child_paths(paths, child, child_prefix, deep)
