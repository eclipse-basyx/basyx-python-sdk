# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
A module with helper functions for traversing AAS object strcutures.
"""

from typing import Union, Iterator

from .. import model


def walk_submodel(collection: Union[model.Submodel, model.SubmodelElementCollection]) \
        -> Iterator[model.SubmodelElement]:
    """
    Traverse the :class:`SubmodelElements <aas.model.submodel.SubmodelElement>` in a
    :class:`~aas.model.submodel.Submodel` or a :class:`~aas.model.submodel.SubmodelElementCollection` recursively in
    post-order tree-traversal.

    This is a generator function, yielding all the :class:`SubmodelElements <aas.model.submodel.SubmodelElement>`. No
    :class:`SubmodelElements <aas.model.submodel.SubmodelElement>` should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    elements = collection.submodel_element if isinstance(collection, model.Submodel) else collection.value
    for element in elements:
        if isinstance(element, model.SubmodelElementCollection):
            yield from walk_submodel(element)
        yield element
