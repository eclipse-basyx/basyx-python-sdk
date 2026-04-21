# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
A module with helper functions for traversing AAS object structures.
"""

from typing import Iterator

from .. import model


def walk_submodel_element(element: model.SubmodelElement) -> Iterator[model.SubmodelElement]:
    """
    Traverse all :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` contained within the given
    element recursively, i.e. the children of:
    :class:`~basyx.aas.model.submodel.SubmodelElementCollection`,
    :class:`~basyx.aas.model.submodel.SubmodelElementList`,
    :class:`~basyx.aas.model.submodel.Entity` (via ``statement``) or
    :class:`~basyx.aas.model.submodel.Operation` (via ``input_variable``, ``output_variable``, ``in_output_variable``).

    The given element itself is not yielded. This is a generator function, yielding all the
    :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>`.
    No :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
        for sub_element in element.value:
            yield from walk_submodel_element(sub_element)
            yield sub_element
    elif isinstance(element, model.Operation):
        for var_list in (element.input_variable, element.output_variable, element.in_output_variable):
            for sub_element in var_list:
                yield from walk_submodel_element(sub_element)
                yield sub_element
    elif isinstance(element, model.Entity):
        for sub_element in element.statement:
            yield from walk_submodel_element(sub_element)
            yield sub_element


def walk_submodel(submodel: model.Submodel) -> Iterator[model.SubmodelElement]:
    """
    Traverse the :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` in a
    :class:`~basyx.aas.model.submodel.Submodel` recursively.

    This is a generator function, yielding all the :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>`.
    No :class:`SubmodelElements <basyx.aas.model.submodel.SubmodelElement>` should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    for element in submodel.submodel_element:
        yield from walk_submodel_element(element)
        yield element


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
