# Copyright (c) 2024 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import base64
import binascii
import io
import json

from lxml import etree
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest, UnprocessableEntity
from werkzeug.wrappers import Request

from basyx.aas import model

from basyx.aas.adapter.xml import XMLConstructables, read_aas_xml_element

from server.app import server_model
from server.app.adapter.jsonization import ServerStrictAASFromJsonDecoder, ServerStrictStrippedAASFromJsonDecoder

from typing import Callable, List, Optional, Type, TypeVar, Union


def is_stripped_request(request: Request) -> bool:
    return request.args.get("level") == "core"


T = TypeVar("T")

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


class HTTPApiDecoder:
    # these are the types we can construct (well, only the ones we need)
    type_constructables_map = {
        model.AssetAdministrationShell: XMLConstructables.ASSET_ADMINISTRATION_SHELL,
        model.AssetInformation: XMLConstructables.ASSET_INFORMATION,
        model.ModelReference: XMLConstructables.MODEL_REFERENCE,
        model.SpecificAssetId: XMLConstructables.SPECIFIC_ASSET_ID,
        model.Qualifier: XMLConstructables.QUALIFIER,
        model.Submodel: XMLConstructables.SUBMODEL,
        model.SubmodelElement: XMLConstructables.SUBMODEL_ELEMENT,
        model.Reference: XMLConstructables.REFERENCE,
    }

    @classmethod
    def check_type_support(cls, type_: type):
        tolerated_types = (
            server_model.AssetAdministrationShellDescriptor,
            server_model.SubmodelDescriptor,
            server_model.AssetLink,
        )
        if type_ not in cls.type_constructables_map and type_ not in tolerated_types:
            raise TypeError(f"Parsing {type_} is not supported!")

    @classmethod
    def assert_type(cls, obj: object, type_: Type[T]) -> T:
        if not isinstance(obj, type_):
            raise UnprocessableEntity(f"Object {obj!r} is not of type {type_.__name__}!")
        return obj

    @classmethod
    def json_list(cls, data: Union[str, bytes], expect_type: Type[T], stripped: bool, expect_single: bool) -> List[T]:
        cls.check_type_support(expect_type)
        decoder: Type[ServerStrictAASFromJsonDecoder] = ServerStrictStrippedAASFromJsonDecoder if stripped \
            else ServerStrictAASFromJsonDecoder
        try:
            parsed = json.loads(data, cls=decoder)
            if isinstance(parsed, list) and expect_single:
                raise UnprocessableEntity(f"Expected a single object of type {expect_type.__name__}, got {parsed!r}!")
            if not isinstance(parsed, list) and not expect_single:
                raise UnprocessableEntity(f"Expected List[{expect_type.__name__}], got {parsed!r}!")
            parsed = [parsed] if not isinstance(parsed, list) else parsed

            # TODO: the following is ugly, but necessary because references aren't self-identified objects
            #  in the json schema
            # TODO: json deserialization will always create an ModelReference[Submodel], xml deserialization determines
            #  that automatically
            mapping = {
                model.ModelReference: decoder._construct_model_reference,  # type: ignore[assignment]
                model.AssetInformation: decoder._construct_asset_information,  # type: ignore[assignment]
                model.SpecificAssetId: decoder._construct_specific_asset_id,  # type: ignore[assignment]
                model.Reference: decoder._construct_reference,  # type: ignore[assignment]
                model.Qualifier: decoder._construct_qualifier,  # type: ignore[assignment]
                server_model.AssetAdministrationShellDescriptor:
                    decoder._construct_asset_administration_shell_descriptor,  # type: ignore[assignment]
                server_model.SubmodelDescriptor: decoder._construct_submodel_descriptor,  # type: ignore[assignment]
                server_model.AssetLink: decoder._construct_asset_link,  # type: ignore[assignment]
            }

            constructor: Optional[Callable[..., T]] = mapping.get(expect_type)
            args = []
            if expect_type is model.ModelReference:
                args.append(model.Submodel)

            if constructor is not None:
                # construct elements that aren't self-identified
                return [constructor(obj, *args) for obj in parsed]

        except (KeyError, ValueError, TypeError, json.JSONDecodeError, model.AASConstraintViolation) as e:
            raise UnprocessableEntity(str(e)) from e

        return [cls.assert_type(obj, expect_type) for obj in parsed]

    @classmethod
    def base64url_json_list(cls, data: str, expect_type: Type[T], stripped: bool, expect_single: bool) -> List[T]:
        data = base64url_decode(data)
        return cls.json_list(data, expect_type, stripped, expect_single)

    @classmethod
    def json(cls, data: Union[str, bytes], expect_type: Type[T], stripped: bool) -> T:
        return cls.json_list(data, expect_type, stripped, True)[0]

    @classmethod
    def base64url_json(cls, data: str, expect_type: Type[T], stripped: bool) -> T:
        data = base64url_decode(data)
        return cls.json_list(data, expect_type, stripped, True)[0]

    @classmethod
    def xml(cls, data: bytes, expect_type: Type[T], stripped: bool) -> T:
        cls.check_type_support(expect_type)
        try:
            xml_data = io.BytesIO(data)
            rv = read_aas_xml_element(xml_data, cls.type_constructables_map[expect_type],
                                             stripped=stripped, failsafe=False)
        except (KeyError, ValueError) as e:
            # xml deserialization creates an error chain. since we only return one error, return the root cause
            f: BaseException = e
            while f.__cause__ is not None:
                f = f.__cause__
            raise UnprocessableEntity(str(f)) from e
        except (etree.XMLSyntaxError, model.AASConstraintViolation) as e:
            raise UnprocessableEntity(str(e)) from e
        return cls.assert_type(rv, expect_type)

    @classmethod
    def request_body(cls, request: Request, expect_type: Type[T], stripped: bool) -> T:
        """
        TODO: werkzeug documentation recommends checking the content length before retrieving the body to prevent
              running out of memory. but it doesn't state how to check the content length
              also: what would be a reasonable maximum content length? the request body isn't limited by the xml/json
              schema
            In the meeting (25.11.2020) we discussed, this may refer to a reverse proxy in front of this WSGI app,
            which should limit the maximum content length.
        """
        valid_content_types = ("application/json", "application/xml", "text/xml")

        if request.mimetype not in valid_content_types:
            raise werkzeug.exceptions.UnsupportedMediaType(
                f"Invalid content-type: {request.mimetype}! Supported types: "
                + ", ".join(valid_content_types))

        if request.mimetype == "application/json":
            return cls.json(request.get_data(), expect_type, stripped)
        return cls.xml(request.get_data(), expect_type, stripped)

    @classmethod
    def request_body_list(cls, request: Request, expect_type: Type[T], stripped: bool) -> List[T]:
        """
        Deserializes the request body to an instance (or list of instances)
        of the expected type.
        """
        # TODO: Refactor this method and request_body to avoid code duplication
        valid_content_types = ("application/json", "application/xml", "text/xml")

        if request.mimetype not in valid_content_types:
            raise werkzeug.exceptions.UnsupportedMediaType(
                f"Invalid content-type: {request.mimetype}! Supported types: " + ", ".join(valid_content_types)
            )

        if request.mimetype == "application/json":
            raw_data = request.get_data()
            try:
                parsed = json.loads(raw_data)
            except Exception as e:
                raise werkzeug.exceptions.BadRequest(f"Invalid JSON: {e}")
            # Prüfe, ob parsed ein Array ist:
            if isinstance(parsed, list):
                # Für jedes Element wird die Konvertierung angewandt.
                return [cls._convert_single_json_item(item, expect_type, stripped) for item in parsed]  # type: ignore
            else:
                return cls._convert_single_json_item(parsed, expect_type, stripped)
        else:
            return cls.xml(request.get_data(), expect_type, stripped)

    @classmethod
    def _convert_single_json_item(cls, data: any, expect_type: Type[T], stripped: bool) -> T:
        """
        Konvertiert ein einzelnes JSON-Objekt (als Python-Dict) in ein Objekt vom Typ expect_type.
        Hierbei wird das Dictionary zuerst wieder in einen JSON-String serialisiert und als Bytes übergeben.
        """
        json_bytes = json.dumps(data).encode("utf-8")
        return cls.json(json_bytes, expect_type, stripped)


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
