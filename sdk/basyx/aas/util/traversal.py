# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
A module with helper functions for traversing AAS object structures.
"""

from typing import Iterable, Iterator, Union

from .. import model


def _walk_submodel_helper(elements: Iterable[model.SubmodelElement]) -> Iterator[model.SubmodelElement]:
    for element in elements:
        if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
            yield from _walk_submodel_helper(element.value)
        elif isinstance(element, model.Operation):
            for var_list in (element.input_variable, element.output_variable, element.in_output_variable):
                yield from _walk_submodel_helper(var_list)
        elif isinstance(element, model.Entity):
            yield from _walk_submodel_helper(element.statement)
        yield element


def walk_submodel(collection: Union[model.Submodel, model.SubmodelElementCollection, model.SubmodelElementList]) \
        -> Iterator[model.SubmodelElement]:
    """
    Traverse the :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` in a
    :class:`~basyx.aas.model.submodel.Submodel`, :class:`~basyx.aas.model.submodel.SubmodelElementCollection`,
    :class:`~basyx.aas.model.submodel.SubmodelElementList`, :class:`~basyx.aas.model.submodel.Entity`
    (via ``statement``) or :class:`~basyx.aas.model.submodel.Operation` (via ``input_variable``, ``output_variable``,
    ``in_output_variable``) recursively in post-order tree-traversal.

    This is a generator function, yielding all the :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>`.
    No :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    elements = collection.submodel_element if isinstance(collection, model.Submodel) else collection.value
    yield from _walk_submodel_helper(elements)


def walk_semantic_ids_recursive(root: model.Referable) -> Iterator[model.Reference]:
    """
    Traverse an AAS object hierarchy (e.g. a :class:`~basyx.aas.model.submodel.Submodel` with all recursively contained
    :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>`) recursively and return all non-empty (!= None)
    semanticIds.

    This is a generator function, yielding all the semanticIds. No :class:`~basyx.aas.model.base.Referable` objects
    should be added, removed or moved to/from/in the AAS object hierarchy while iterating, as this could result
    in undefined behaviour.
    """
    if isinstance(root, model.HasSemantics):
        if root.semantic_id is not None:
            yield root.semantic_id
    # Qualifier is the only non-Referable class which HasSemantics
    if isinstance(root, model.Qualifiable):
        for qualifier in root.qualifier:
            if isinstance(qualifier, model.Qualifier) and qualifier.semantic_id is not None:
                yield qualifier.semantic_id
    if isinstance(root, model.UniqueIdShortNamespace):
        for element in root:  # iterates Referable objects in Namespace
            yield from walk_semantic_ids_recursive(element)
