# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Central parsing and validation of serialization modifiers
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from werkzeug import Request
from werkzeug.exceptions import BadRequest

__all__ = ["Content", "Modifiers", "parse_modifiers"]


class Content(str, Enum):
    NORMAL = "normal"
    METADATA = "metadata"
    VALUE = "value"
    REFERENCE = "reference"
    PATH = "path"


@dataclass(frozen=True)
class Modifiers:
    content: Content
    deep: bool
    with_blob: bool


def parse_modifiers(request: Request, content: Optional[Content] = None) -> Modifiers:
    # content is None when URL carried no $... suffix. Default: normal
    resolved = content if content is not None else Content.NORMAL
    deep = _parse_level(request, resolved)
    with_blob = _parse_extent(request, resolved)
    return Modifiers(content=resolved, deep=deep, with_blob=with_blob)


def _parse_level(request: Request, content: Content) -> bool:
    raw = request.args.get("level")
    if raw is None:
        # Spec default is deep
        return True
    if content is Content.METADATA:
        raise BadRequest("Parameter 'level' is not allowed with /$metadata.")
    if content is Content.REFERENCE and raw == "deep":
        raise BadRequest("Parameter 'level=deep' is not allowed with /$reference.")
    if raw not in {"deep", "core"}:
        raise BadRequest(f"Invalid value for 'level': {raw!r}. Expected 'deep' or 'core'.")
    return raw == "deep"


def _parse_extent(request: Request, content: Content) -> bool:
    raw = request.args.get("extent")
    if raw is None:
        return False
    norm = raw.lower()
    if norm not in {"withblobvalue", "withoutblobvalue"}:
        raise BadRequest(
            f"Invalid value for 'extent': {raw!r}. Expected 'WithBLOBValue' or 'WithoutBLOBValue'."
        )
    want_blob = norm == "withblobvalue"
    if want_blob and content in {Content.METADATA, Content.REFERENCE, Content.PATH}:
        raise BadRequest(f"Parameter 'extent=WithBLOBValue' is not allowed with /${content.value}.")
    return want_blob
