# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
from typing import Optional, Tuple

from basyx.aas import model

from . import _generic


def reference_sort_key(obj: Optional[model.Reference]) -> Tuple:
    """
    Sort key of a Reference, consisting of its type, its keys and its referredSemanticId

    :param obj: object of class Reference or ``None``
    :return: tuple which totally orders References, ``()`` for ``None``
    """
    if obj is None:
        return ()
    return (
        _generic.REFERENCE_TYPES[obj.__class__],
        tuple((_generic.KEY_TYPES[key.type], key.value) for key in obj.key),
        reference_sort_key(obj.referred_semantic_id),
    )


def specific_asset_id_sort_key(obj: model.SpecificAssetId) -> Tuple:
    """
    Sort key of a SpecificAssetId, consisting of all its attributes, since its name is not unique

    :param obj: object of class SpecificAssetId
    :return: tuple which totally orders SpecificAssetIds
    """
    return (
        obj.name,
        obj.value,
        reference_sort_key(obj.external_subject_id),
        reference_sort_key(obj.semantic_id),
        tuple(sorted(reference_sort_key(ref) for ref in obj.supplemental_semantic_id)),
    )


def embedded_data_specification_sort_key(obj: model.EmbeddedDataSpecification) -> Tuple:
    """
    Sort key of an EmbeddedDataSpecification, consisting of its dataSpecification

    :param obj: object of class EmbeddedDataSpecification
    :return: tuple which totally orders EmbeddedDataSpecifications
    """
    return reference_sort_key(obj.data_specification)


def value_reference_pair_sort_key(obj: model.ValueReferencePair) -> Tuple:
    """
    Sort key of a ValueReferencePair, consisting of its value and its valueId, since its value is not unique

    :param obj: object of class ValueReferencePair
    :return: tuple which totally orders ValueReferencePairs
    """
    return model.datatypes.xsd_repr(obj.value), reference_sort_key(obj.value_id)


def extension_sort_key(obj: model.Extension) -> str:
    """
    Sort key of an Extension, its name, which is unique (Constraint AASd-077)

    :param obj: object of class Extension
    :return: name of the Extension
    """
    return obj.name


def qualifier_sort_key(obj: model.Qualifier) -> str:
    """
    Sort key of a Qualifier, its type, which is unique (Constraint AASd-021)

    :param obj: object of class Qualifier
    :return: type of the Qualifier
    """
    return obj.type


def referable_sort_key(obj: model.Referable) -> str:
    """
    Sort key of a Referable within its namespace, its idShort, which is unique (Constraint AASd-022)

    :param obj: object of class Referable
    :return: idShort of the Referable, ``""`` if it has none
    """
    return obj.id_short or ""


def identifiable_sort_key(obj: model.Identifiable) -> str:
    """
    Sort key of an Identifiable, its globally unique id

    :param obj: object of class Identifiable
    :return: id of the Identifiable
    """
    return obj.id
