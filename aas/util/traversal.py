# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
A module with helper functions for traversing AAS object strcutures.
"""

from typing import Union, Iterator

from .. import model


def walk_submodel(collection: Union[model.Submodel, model.SubmodelElementCollection]) \
        -> Iterator[model.SubmodelElement]:
    """
    Traverse the SubmodelElements in a Submodel or a SubmodelElementCollection recursively in post-order tree-traversal.

    This is a generator function, yielding all the SubmodelElements. No SubmodelElements should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    elements = collection.submodel_element if isinstance(collection, model.Submodel) else collection.value
    for element in elements:
        if isinstance(element, model.SubmodelElementCollection):
            yield from walk_submodel(element)
        yield element
