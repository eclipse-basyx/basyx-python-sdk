# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements constraint functions for the listed constrained string types.
All types are constrained in length (min and max).

.. warning::
    This module is intended for internal use only.

The following types aliased in the :mod:`~server.app.interfaces.base` module are constrained:

- :class:`~server.app.interfaces.base.CodeType`
- :class:`~server.app.interfaces.base.ShortIdType`
- :class:`~server.app.interfaces.base.LocatorType`
- :class:`~server.app.interfaces.base.TextType`
- :class:`~server.app.interfaces.base.SchemeType`
"""

from typing import Callable, Optional, Type

from basyx.aas.model._string_constraints import _T, check, constrain_attr


def check_code_type(
    value: str, type_name: str = "CodeType", attribute: Optional[str] = None
) -> None:
    return check(value, type_name, 1, 32, attribute=attribute)


def check_short_id_type(
    value: str, type_name: str = "ShortIdType", attribute: Optional[str] = None
) -> None:
    return check(value, type_name, 1, 128, attribute=attribute)


def check_locator_type(
    value: str, type_name: str = "LocatorType", attribute: Optional[str] = None
) -> None:
    return check(value, type_name, 1, 2048, attribute=attribute)


def check_text_type(
    value: str, type_name: str = "TextType", attribute: Optional[str] = None
) -> None:
    return check(value, type_name, 1, 2048, attribute=attribute)


def check_scheme_type(
    value: str, type_name: str = "SchemeType", attribute: Optional[str] = None
) -> None:
    return check(value, type_name, 1, 128, attribute=attribute)


def constrain_code_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_code_type)


def constrain_short_id_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_short_id_type)


def constrain_locator_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_locator_type)


def constrain_text_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_text_type)


def constrain_scheme_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_scheme_type)
