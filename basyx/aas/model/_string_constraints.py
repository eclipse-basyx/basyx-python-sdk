# Copyright (c) 2023 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements constraint functions for the listed constrained string types and is meant for internal use only.
All types are constrained in length (min and max), RevisionType and VersionType are additionally constrained
by a regular expression. The following types aliased in the base module are constrained:
- ContentType
- Identifier
- LabelType
- MessageTopicType
- NameType
- PathType
- RevisionType
- ShortNameType
- QualifierType
- VersionType
"""

import re

from typing import Callable, Optional, Type, TypeVar


_T = TypeVar("_T")


# Functions to verify the constraints for a given value.
def check(value: str, type_name: str, min_length: int = 0, max_length: Optional[int] = None,
          pattern: Optional[re.Pattern] = None) -> None:
    if len(value) < min_length:
        raise ValueError(f"{type_name} has a minimum length of {min_length}! (length: {len(value)})")
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{type_name} has a maximum length of {max_length}! (length: {len(value)})")
    if pattern is not None and not pattern.fullmatch(value):
        raise ValueError(f"{type_name} must match the pattern '{pattern.pattern}'! (value: '{value}')")


def check_content_type(value: str, type_name: str = "ContentType") -> None:
    return check(value, type_name, 1, 100)


def check_identifier(value: str, type_name: str = "Identifier") -> None:
    return check(value, type_name, 1, 2000)


def check_label_type(value: str, type_name: str = "LabelType") -> None:
    return check(value, type_name, 1, 64)


def check_message_topic_type(value: str, type_name: str = "MessageTopicType") -> None:
    return check(value, type_name, 1, 255)


def check_name_type(value: str, type_name: str = "NameType") -> None:
    return check(value, type_name, 1, 128)


def check_path_type(value: str, type_name: str = "PathType") -> None:
    return check_identifier(value, type_name)


def check_qualifier_type(value: str, type_name: str = "QualifierType") -> None:
    return check_name_type(value, type_name)


def check_revision_type(value: str, type_name: str = "RevisionType") -> None:
    return check(value, type_name, 1, 4, re.compile(r"([0-9]|[1-9][0-9]*)"))


def check_short_name_type(value: str, type_name: str = "ShortNameType") -> None:
    return check(value, type_name, 1, 64)


def check_version_type(value: str, type_name: str = "VersionType") -> None:
    return check(value, type_name, 1, 4, re.compile(r"([0-9]|[1-9][0-9]*)"))


# Decorator functions to add getter/setter to classes for verification, whenever a value is updated.
def constrain_attr(pub_attr_name: str, constraint_check_fn: Callable[[str], None]) \
        -> Callable[[Type[_T]], Type[_T]]:
    def decorator_fn(decorated_class: Type[_T]) -> Type[_T]:
        def _getter(self) -> Optional[str]:
            return getattr(self, "_" + pub_attr_name)

        def _setter(self, value: Optional[str]) -> None:
            # if value is None, skip checks. incorrect 'None' assignments are caught by the type checker anyway
            if value is not None:
                constraint_check_fn(value)
            setattr(self, "_" + pub_attr_name, value)

        setattr(decorated_class, pub_attr_name, property(_getter, _setter))
        return decorated_class

    return decorator_fn


def constrain_content_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_content_type)


def constrain_identifier(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_identifier)


def constrain_label_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_label_type)


def constrain_message_topic_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_message_topic_type)


def constrain_name_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_name_type)


def constrain_path_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_path_type)


def constrain_qualifier_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_qualifier_type)


def constrain_revision_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_revision_type)


def constrain_short_name_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_short_name_type)


def constrain_version_type(pub_attr_name: str) -> Callable[[Type[_T]], Type[_T]]:
    return constrain_attr(pub_attr_name, check_version_type)
