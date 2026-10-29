# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
ValueOnly serialization of Submodels and SubmodelElements, as defined in "Specification of the Asset Administration
Shell Part 1", section "Value-Only Serialization in JSON".

The ValueOnly serialization cannot be derived from the JSON schema of the metamodel, since it defines individual rules
per class. Therefore, it is implemented by hand here, on top of the object model of the ``basyx-python-sdk``.

The returned structures are JSON-serializable with :class:`~basyx.aas.adapter.json.AASToJsonEncoder` (or any subclass,
e.g. the ``ResultToJsonEncoder`` of this server): :class:`~basyx.aas.model.base.Reference` and
:class:`~basyx.aas.model.base.SpecificAssetId` objects are passed through as-is instead of being converted here, to
avoid duplicating the serialization rules of the SDK.
"""

import base64
import decimal
import math
from typing import Any, Dict, Iterable, List, Optional

from basyx.aas import model
from basyx.aas.adapter._generic import ENTITY_TYPES

__all__ = [
    "has_value_only_representation",
    "submodel_element_to_named_value_only",
    "submodel_element_to_value_only",
    "submodel_to_value_only",
]

# SubmodelElement types that don't have a ValueOnly representation. Operations only have one in the context of their
# invocation, which is not supported by this server.
_TYPES_WITHOUT_VALUE_ONLY = (model.Operation, model.Capability)


def has_value_only_representation(element: model.SubmodelElement) -> bool:
    """
    Whether a SubmodelElement has a ValueOnly representation at all.

    :param element: The SubmodelElement to check
    :return: ``False`` for Operations and Capabilities, ``True`` otherwise
    """
    return not isinstance(element, _TYPES_WITHOUT_VALUE_ONLY)


def submodel_to_value_only(submodel: model.Submodel, deep: bool = True) -> Dict[str, Any]:
    """
    Serialize a Submodel in its ValueOnly representation.

    :param submodel: The Submodel to serialize
    :param deep: If ``False`` (i.e. ``level=core``), only the first level of SubmodelElements is serialized and nested
                 containers are returned empty
    :return: A dictionary, mapping the idShort of each SubmodelElement to its value
    """
    return _namespace_to_value_only(submodel.submodel_element, _initial_depth(deep))


def submodel_element_to_value_only(element: model.SubmodelElement, deep: bool = True) -> Any:
    """
    Serialize a SubmodelElement in its ValueOnly representation.

    :param element: The SubmodelElement to serialize
    :param deep: If ``False`` (i.e. ``level=core``), only the first level of child elements is serialized and nested
                 containers are returned empty
    :raises TypeError: If the given element doesn't have a ValueOnly representation, see
                       :func:`has_value_only_representation`
    :return: The value of the element, ``None`` if it doesn't have one
    """
    return _element_to_value_only(element, _initial_depth(deep))


def _initial_depth(deep: bool) -> float:
    # The number of container levels that are serialized below the requested resource. level=core includes the direct
    # children of the requested resource, but returns their children as empty containers.
    return math.inf if deep else 1


def _namespace_to_value_only(elements: Iterable[model.SubmodelElement], depth: float) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if depth <= 0:
        return data
    for element in elements:
        if not has_value_only_representation(element):
            continue
        value = _element_to_value_only(element, depth - 1)
        # Elements without a value are omitted
        if value is None:
            continue
        # The idShort is always set for elements that aren't contained in a SubmodelElementList
        assert element.id_short is not None
        data[element.id_short] = value
    return data


def _element_to_value_only(element: model.SubmodelElement, depth: float) -> Any:
    if isinstance(element, model.Property):
        return _typed_value_to_value_only(element.value, element.value_type)
    if isinstance(element, model.MultiLanguageProperty):
        return _lang_string_set_to_value_only(element.value)
    if isinstance(element, model.Range):
        return _range_to_value_only(element)
    if isinstance(element, model.Blob):
        return {
            "contentType": element.content_type,
            "value": None if element.value is None else base64.b64encode(element.value).decode(),
        }
    if isinstance(element, model.File):
        return {"contentType": element.content_type, "value": element.value}
    if isinstance(element, model.ReferenceElement):
        return element.value
    # AnnotatedRelationshipElement is a subclass of RelationshipElement and must therefore be checked first
    if isinstance(element, model.AnnotatedRelationshipElement):
        return {
            "first": element.first,
            "second": element.second,
            "annotations": _annotations_to_value_only(element.annotation, depth),
        }
    if isinstance(element, model.RelationshipElement):
        return {"first": element.first, "second": element.second}
    if isinstance(element, model.Entity):
        return _entity_to_value_only(element, depth)
    if isinstance(element, model.BasicEventElement):
        return {"observed": element.observed}
    if isinstance(element, model.SubmodelElementList):
        return _submodel_element_list_to_value_only(element, depth)
    if isinstance(element, model.SubmodelElementCollection):
        return _namespace_to_value_only(element.value, depth)
    raise TypeError(f"{element!r} doesn't have a ValueOnly representation!")


def _typed_value_to_value_only(value: Optional[model.ValueDataType], value_type: model.DataTypeDefXsd) -> Any:
    """
    Map a typed value to its JSON representation: booleans become JSON booleans, numeric types become JSON numbers and
    everything else becomes a JSON string containing the XSD representation of the value.
    """
    if value is None:
        return None
    if value_type is model.datatypes.Boolean or isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        # int subclasses are serialized as JSON numbers as-is. xs:integer is unbounded, so no conversion to float may
        # happen here, as that would raise an OverflowError for large values.
        return value
    if isinstance(value, (float, decimal.Decimal)):
        # JSON doesn't support NaN, INF and -INF. The specification acknowledges this gap without resolving it, so the
        # XSD representation is returned as a string instead of emitting invalid JSON. This also catches values of
        # decimal.Decimal that are finite, but too large to be represented as a float.
        if not math.isfinite(float(value)):
            return model.datatypes.xsd_repr(value)
        # decimal.Decimal cannot be serialized as JSON and may lose precision here
        return float(value) if isinstance(value, decimal.Decimal) else value
    return model.datatypes.xsd_repr(value)


def _lang_string_set_to_value_only(value: Optional[model.MultiLanguageTextType]) -> List[Dict[str, str]]:
    if value is None:
        return []
    # Sorted by language, to keep the order of the languages deterministic across requests
    return [{language: text} for language, text in sorted(value.items())]


def _range_to_value_only(element: model.Range) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if element.min is not None:
        data["min"] = _typed_value_to_value_only(element.min, element.value_type)
    if element.max is not None:
        data["max"] = _typed_value_to_value_only(element.max, element.value_type)
    return data


def _annotations_to_value_only(annotations: Iterable[model.DataElement], depth: float) -> List[Dict[str, Any]]:
    if depth <= 0:
        return []
    return [
        {annotation.id_short: _element_to_value_only(annotation, depth - 1)}
        for annotation in annotations
        if annotation.id_short is not None
    ]


def _entity_to_value_only(element: model.Entity, depth: float) -> Dict[str, Any]:
    data: Dict[str, Any] = {"statements": _namespace_to_value_only(element.statement, depth)}
    # entityType is mandatory in the specification, but optional in the object model of the SDK
    if element.entity_type is not None:
        data["entityType"] = ENTITY_TYPES[element.entity_type]
    if element.global_asset_id is not None:
        data["globalAssetId"] = element.global_asset_id
    if len(element.specific_asset_id) > 0:
        data["specificAssetIds"] = list(element.specific_asset_id)
    return data


def _submodel_element_list_to_value_only(element: model.SubmodelElementList, depth: float) -> List[Any]:
    if depth <= 0:
        return []
    # In contrast to the other containers, elements without a value are not omitted here, to keep the indices of the
    # remaining elements intact
    return [
        _element_to_value_only(child, depth - 1) if has_value_only_representation(child) else None
        for child in element.value
    ]


def submodel_element_to_named_value_only(element: model.SubmodelElement, deep: bool = True) -> Dict[str, Any]:
    """
    Serialize a SubmodelElement as a single-entry dictionary, mapping its idShort to its ValueOnly representation.

    This is the representation used for the entries of ``GET /submodels/{submodelIdentifier}/submodel-elements/$value``.
    The specification leaves the shape of these entries open: a bare ``SubmodelElementValue`` would lose the
    association between a value and the element it belongs to, hence the elements are named here, just like they are
    within the ValueOnly representation of their parent.

    :param element: The SubmodelElement to serialize
    :param deep: If ``False`` (i.e. ``level=core``), only the first level of child elements is serialized
    :return: A dictionary with a single entry, mapping the idShort of the given element to its value
    """
    # The idShort is always set for elements that aren't contained in a SubmodelElementList
    assert element.id_short is not None
    return {element.id_short: submodel_element_to_value_only(element, deep)}
