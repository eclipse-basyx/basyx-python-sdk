# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import abc
import datetime
import enum
import io
import itertools
import json
from typing import Iterable, Type, Iterator, Tuple, Optional, List, Union, Dict, Callable, TypeVar, Any

import werkzeug.exceptions
import werkzeug.routing
import werkzeug.utils
from lxml import etree
from werkzeug import Response, Request
from werkzeug.exceptions import NotFound, BadRequest
from werkzeug.routing import MapAdapter

from basyx.aas import model
from basyx.aas.adapter._generic import XML_NS_MAP
from basyx.aas.adapter.json import StrictStrippedAASFromJsonDecoder, StrictAASFromJsonDecoder, AASToJsonEncoder
from basyx.aas.adapter.xml import xml_serialization, XMLConstructables, read_aas_xml_element
from basyx.aas.model import AbstractObjectStore
from util.converters import base64url_decode


T = TypeVar("T")


@enum.unique
class MessageType(enum.Enum):
    UNDEFINED = enum.auto()
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    EXCEPTION = enum.auto()

    def __str__(self):
        return self.name.capitalize()


class Message:
    def __init__(self, code: str, text: str, message_type: MessageType = MessageType.UNDEFINED,
                 timestamp: Optional[datetime.datetime] = None):
        self.code: str = code
        self.text: str = text
        self.message_type: MessageType = message_type
        self.timestamp: datetime.datetime = timestamp if timestamp is not None \
            else datetime.datetime.now(datetime.timezone.utc)


class Result:
    def __init__(self, success: bool, messages: Optional[List[Message]] = None):
        if messages is None:
            messages = []
        self.success: bool = success
        self.messages: List[Message] = messages


ResponseData = Union[Result, object, List[object]]


class APIResponse(abc.ABC, Response):
    @abc.abstractmethod
    def __init__(self, obj: Optional[ResponseData] = None, cursor: Optional[int] = None,
                 stripped: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if obj is None:
            self.status_code = 204
        else:
            self.data = self.serialize(obj, cursor, stripped)

    @abc.abstractmethod
    def serialize(self, obj: ResponseData, cursor: Optional[int], stripped: bool) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, obj: ResponseData, cursor: Optional[int], stripped: bool) -> str:
        if cursor is None:
            data = obj
        else:
            data = {
                "paging_metadata": {"cursor": str(cursor)},
                "result": obj
            }
        return json.dumps(
            data,
            cls=StrippedResultToJsonEncoder if stripped else ResultToJsonEncoder,
            separators=(",", ":")
        )


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, obj: ResponseData, cursor: Optional[int], stripped: bool) -> str:
        root_elem = etree.Element("response", nsmap=XML_NS_MAP)
        if cursor is not None:
            root_elem.set("cursor", str(cursor))
        if isinstance(obj, Result):
            result_elem = self.result_to_xml(obj, **XML_NS_MAP)
            for child in result_elem:
                root_elem.append(child)
        elif isinstance(obj, list):
            for item in obj:
                item_elem = xml_serialization.object_to_xml_element(item)
                root_elem.append(item_elem)
        else:
            obj_elem = xml_serialization.object_to_xml_element(obj)
            for child in obj_elem:
                root_elem.append(child)
        etree.cleanup_namespaces(root_elem)
        xml_str = etree.tostring(root_elem, xml_declaration=True, encoding="utf-8")
        return xml_str  # type: ignore[return-value]

    @classmethod
    def result_to_xml(cls, result: Result, **kwargs) -> etree._Element:
        result_elem = etree.Element("result", **kwargs)
        success_elem = etree.Element("success")
        success_elem.text = xml_serialization.boolean_to_xml(result.success)
        messages_elem = etree.Element("messages")
        for message in result.messages:
            messages_elem.append(cls.message_to_xml(message))

        result_elem.append(success_elem)
        result_elem.append(messages_elem)
        return result_elem

    @classmethod
    def message_to_xml(cls, message: Message) -> etree._Element:
        message_elem = etree.Element("message")
        message_type_elem = etree.Element("messageType")
        message_type_elem.text = str(message.message_type)
        text_elem = etree.Element("text")
        text_elem.text = message.text
        code_elem = etree.Element("code")
        code_elem.text = message.code
        timestamp_elem = etree.Element("timestamp")
        timestamp_elem.text = message.timestamp.isoformat()

        message_elem.append(message_type_elem)
        message_elem.append(text_elem)
        message_elem.append(code_elem)
        message_elem.append(timestamp_elem)
        return message_elem


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


class ResultToJsonEncoder(AASToJsonEncoder):
    @classmethod
    def _result_to_json(cls, result: Result) -> Dict[str, object]:
        return {
            "success": result.success,
            "messages": result.messages
        }

    @classmethod
    def _message_to_json(cls, message: Message) -> Dict[str, object]:
        return {
            "messageType": message.message_type,
            "text": message.text,
            "code": message.code,
            "timestamp": message.timestamp.isoformat()
        }

    def default(self, obj: object) -> object:
        if isinstance(obj, Result):
            return self._result_to_json(obj)
        if isinstance(obj, Message):
            return self._message_to_json(obj)
        if isinstance(obj, MessageType):
            return str(obj)
        return super().default(obj)


class StrippedResultToJsonEncoder(ResultToJsonEncoder):
    stripped = True


class BaseWSGIApp:
    url_map: werkzeug.routing.Map

    # TODO: the parameters can be typed via builtin wsgiref with Python 3.11+
    def __call__(self, environ, start_response) -> Iterable[bytes]:
        response: Response = self.handle_request(Request(environ))
        return response(environ, start_response)

    @classmethod
    def _get_slice(cls, request: Request, iterator: Iterable[T]) -> Tuple[Iterator[T], int]:
        limit_str = request.args.get('limit', default="10")
        cursor_str = request.args.get('cursor', default="1")
        try:
            limit, cursor = int(limit_str), int(cursor_str) - 1  # cursor is 1-indexed
            if limit < 0 or cursor < 0:
                raise ValueError
        except ValueError:
            raise BadRequest("Limit can not be negative, cursor must be positive!")
        start_index = cursor
        end_index = cursor + limit
        paginated_slice = itertools.islice(iterator, start_index, end_index)
        return paginated_slice, end_index

    def handle_request(self, request: Request):
        map_adapter: MapAdapter = self.url_map.bind_to_environ(request.environ)
        try:
            response_t = self.get_response_type(request)
        except werkzeug.exceptions.NotAcceptable as e:
            return e

        try:
            endpoint, values = map_adapter.match()
            return endpoint(request, values, response_t=response_t, map_adapter=map_adapter)

        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.HTTPException as e:
            return self.http_exception_to_response(e, response_t)

    @staticmethod
    def get_response_type(request: Request) -> Type[APIResponse]:
        response_types: Dict[str, Type[APIResponse]] = {
            "application/json": JsonResponse,
            "application/xml": XmlResponse,
            "text/xml": XmlResponseAlt
        }
        if len(request.accept_mimetypes) == 0 or request.accept_mimetypes.best in (None, "*/*"):
            return JsonResponse
        mime_type = request.accept_mimetypes.best_match(response_types)
        if mime_type is None:
            raise werkzeug.exceptions.NotAcceptable("This server supports the following content types: "
                                                    + ", ".join(response_types.keys()))
        return response_types[mime_type]

    @staticmethod
    def http_exception_to_response(exception: werkzeug.exceptions.HTTPException, response_type: Type[APIResponse]) \
            -> APIResponse:
        headers = exception.get_headers()
        location = exception.get_response().location
        if location is not None:
            headers.append(("Location", location))
        if exception.code and exception.code >= 400:
            message = Message(type(exception).__name__,
                              exception.description if exception.description is not None else "",
                              MessageType.ERROR)
            result = Result(False, [message])
        else:
            result = Result(False)
        return response_type(result, status=exception.code, headers=headers)


class ObjectStoreWSGIApp(BaseWSGIApp):
    object_store: AbstractObjectStore

    def _get_all_obj_of_type(self, type_: Type[model.provider._IT]) -> Iterator[model.provider._IT]:
        for obj in self.object_store:
            if isinstance(obj, type_):
                yield obj

    def _get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(f"No {type_.__name__} with {identifier} found!")
        return identifiable


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
        if type_ not in cls.type_constructables_map:
            raise TypeError(f"Parsing {type_} is not supported!")

    @classmethod
    def assert_type(cls, obj: object, type_: Type[T]) -> T:
        if not isinstance(obj, type_):
            raise BadRequest(f"Object {obj!r} is not of type {type_.__name__}!")
        return obj

    @classmethod
    def json_list(cls, data: Union[str, bytes], expect_type: Type[T], stripped: bool, expect_single: bool) -> List[T]:
        cls.check_type_support(expect_type)
        decoder: Type[StrictAASFromJsonDecoder] = StrictStrippedAASFromJsonDecoder if stripped \
            else StrictAASFromJsonDecoder
        try:
            parsed = json.loads(data, cls=decoder)
            if isinstance(parsed, list) and expect_single:
                raise BadRequest(f"Expected a single object of type {expect_type.__name__}, got {parsed!r}!")
            if not isinstance(parsed, list) and not expect_single:
                raise BadRequest(f"Expected List[{expect_type.__name__}], got {parsed!r}!")
            parsed = [parsed] if not isinstance(parsed, list) else parsed

            # TODO: the following is ugly, but necessary because references aren't self-identified objects
            #  in the json schema
            # TODO: json deserialization will always create an ModelReference[Submodel], xml deserialization determines
            #  that automatically
            mapping = {
                model.ModelReference: decoder._construct_model_reference,
                model.AssetInformation: decoder._construct_asset_information,
                model.SpecificAssetId: decoder._construct_specific_asset_id,
                model.Reference: decoder._construct_reference,
                model.Qualifier: decoder._construct_qualifier,
            }

            constructor: Optional[Callable[..., T]] = mapping.get(expect_type)  # type: ignore[assignment]
            args = []
            if expect_type is model.ModelReference:
                args.append(model.Submodel)

            if constructor is not None:
                # construct elements that aren't self-identified
                return [constructor(obj, *args) for obj in parsed]

        except (KeyError, ValueError, TypeError, json.JSONDecodeError, model.AASConstraintViolation) as e:
            raise BadRequest(str(e)) from e

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
            raise BadRequest(str(f)) from e
        except (etree.XMLSyntaxError, model.AASConstraintViolation) as e:
            raise BadRequest(str(e)) from e
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
                return [cls._convert_single_json_item(parsed, expect_type, stripped)]
        else:
            return [cls.xml(request.get_data(), expect_type, stripped)]

    @classmethod
    def _convert_single_json_item(cls, data: Any, expect_type: Type[T], stripped: bool) -> T:
        """
        Converts a single JSON-Object (as a Python-Dict) to an object of type expect_type.
        Here the dictionary is first serialized back to a JSON-string and returned as bytes.
        """
        json_bytes = json.dumps(data).encode("utf-8")
        return cls.json(json_bytes, expect_type, stripped)


def is_stripped_request(request: Request) -> bool:
    level = request.args.get("level")
    if level not in {"deep", "core", None}:
        raise BadRequest(f"Level {level} is not a valid level!")
    extent = request.args.get("extent")
    if extent is not None:
        raise werkzeug.exceptions.NotImplemented(f"The parameter extent is not yet implemented for this server!")
    return level == "core"
