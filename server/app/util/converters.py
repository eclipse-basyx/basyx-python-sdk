# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module contains helper classes for converting various types between our Python SDK types
and the HTTP-API formats, such as:
- Base64URLConverter
- IdShortPathConverter
"""

import base64
import binascii

import werkzeug.routing
import werkzeug.utils
from werkzeug.exceptions import BadRequest

from basyx.aas import model

from typing import List

BASE64URL_ENCODING = "utf-8"


def base64url_decode(data: str) -> str:
    try:
        # If the requester omits the base64 padding, an exception will be raised.
        # However, Python doesn't complain about too much padding,
        # thus we simply always append two padding characters (==).
        # See also: https://stackoverflow.com/a/49459036/4780052
        decoded = base64.urlsafe_b64decode(data + "==").decode(BASE64URL_ENCODING)
    except binascii.Error:
        raise BadRequest(f"Encoded data {data} is invalid base64url!")
    except UnicodeDecodeError:
        raise BadRequest(f"Encoded base64url value is not a valid {BASE64URL_ENCODING} string!")
    return decoded


def base64url_encode(data: str) -> str:
    encoded = base64.urlsafe_b64encode(data.encode(BASE64URL_ENCODING)).decode("ascii")
    return encoded


class IdentifierToBase64URLConverter(werkzeug.routing.UnicodeConverter):
    """
       A custom URL converter for Werkzeug routing that encodes and decodes
       Identifiers using Base64 URL-safe encoding.
    """
    def to_url(self, value: model.Identifier) -> str:
        return super().to_url(base64url_encode(value))

    def to_python(self, value: str) -> model.Identifier:
        value = super().to_python(value)
        decoded = base64url_decode(value)
        return decoded


class IdShortPathConverter(werkzeug.routing.UnicodeConverter):
    """
        A custom Werkzeug URL converter for handling dot-separated idShort paths and indexes.

        This converter joins a list of idShort strings into an id_short_sep-separated path for URLs
        (e.g., ["submodel", "element", "1"] -> "submodel.element[1]") and parses incoming URL paths
        back into a list, validating each idShort.
        """

    def to_url(self, value: List[str]) -> str:
        id_short_path = model.Referable.build_id_short_path(value)
        return super().to_url(id_short_path)

    def to_python(self, value: str) -> List[str]:
        try:
            parsed_id_short_path = model.Referable.parse_id_short_path(value)
        except (ValueError, model.AASConstraintViolation) as e:
            raise BadRequest(f"{value} is not a valid id_short!") from e
        return parsed_id_short_path
