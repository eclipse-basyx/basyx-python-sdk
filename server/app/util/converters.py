# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
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


class Base64URLConverter(werkzeug.routing.UnicodeConverter):
    def to_url(self, value: model.Identifier) -> str:
        return super().to_url(base64url_encode(value))

    def to_python(self, value: str) -> model.Identifier:
        value = super().to_python(value)
        decoded = base64url_decode(super().to_python(value))
        return decoded


class IdShortPathConverter(werkzeug.routing.UnicodeConverter):
    id_short_sep = "."

    def to_url(self, value: List[str]) -> str:
        return super().to_url(self.id_short_sep.join(value))

    def to_python(self, value: str) -> List[str]:
        id_shorts = super().to_python(value).split(self.id_short_sep)
        for id_short in id_shorts:
            try:
                model.Referable.validate_id_short(id_short)
            except (ValueError, model.AASConstraintViolation):
                raise BadRequest(f"{id_short} is not a valid id_short!")
        return id_shorts
