# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
from typing import Callable, Dict, Type

from basyx.aas import model

from ..json_serialization import AASToJsonEncoder


class ReferenceJsonEncoder(AASToJsonEncoder):
    """
    Custom JSONEncoder that serializes :class:`~basyx.aas.model.base.Referable` objects, which are contained
    in an :class:`~basyx.aas.model.base.Identifiable`, as their :class:`~basyx.aas.model.base.ModelReference`.
    """

    @classmethod
    def _get_aas_class_serializers(cls) -> Dict[Type, Callable]:
        normal_serializers = super()._get_aas_class_serializers()
        serializers: Dict[Type, Callable] = {}
        for typ in normal_serializers:
            if not issubclass(typ, model.Referable):
                serializers[typ] = cls._no_referable

        serializers.update({
            model.Reference: normal_serializers[model.Reference],
            model.Key: normal_serializers[model.Key],
            model.Referable: cls._referable_to_reference,
        })

        return serializers

    @classmethod
    def _referable_to_reference(cls, obj: model.Referable) -> model.Reference:
        return model.ModelReference.from_referable(obj)

    @classmethod
    def _no_referable(cls, obj: object):
        raise TypeError(f"Object of type {obj.__class__.__name__} has no Reference serialization")
