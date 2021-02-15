# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
A module with helper functions for traversing AAS object structures.
"""

from typing import Union, Iterator

from .. import model


def walk_submodel(collection: Union[model.Submodel, model.SubmodelElementCollection]) \
        -> Iterator[model.SubmodelElement]:
    """
    Traverse the :class:`SubmodelElements <aas.model.submodel.SubmodelElement>` in a
    :class:`~aas.model.submodel.Submodel` or a :class:`~aas.model.submodel.SubmodelElementCollection` recursively in
    post-order tree-traversal.

    This is a generator function, yielding all the :class:`SubmodelElements <aas.model.submodel.SubmodelElement>`.
    No :class:`SubmodelElements <aas.model.submodel.SubmodelElement>` should be added, removed or
    moved while iterating, as this could result in undefined behaviour.
    """
    elements = collection.submodel_element if isinstance(collection, model.Submodel) else collection.value
    for element in elements:
        if isinstance(element, model.SubmodelElementCollection):
            yield from walk_submodel(element)
        yield element


def walk_semantic_ids_recursive(root: model.Referable) -> Iterator[model.Reference]:
    """
    Traverse an AAS object hierarchy (e.g. an AAS with its :class:`Views <aas.model.aas.View>` or a
    :class:`~aas.model.submodel.Submodel` with all recursively contained
    :class:`SubmodelElements <aas.model.submodel.SubmodelElements>`) recursively and return all non-empty (!= None)
    semanticIds.

    This is a generator function, yielding all the semanticIds. No :class:`~aas.model.base.Referable` objects should be
    added, removed or moved to/from/in the AAS object hierarchy while iterating, as this could result in undefined
    behaviour.
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
