import abc
import datetime
import enum
import json
from typing import Union, List, Optional, Type, Dict

import werkzeug.exceptions
from lxml import etree
from werkzeug import Response, Request

from basyx.aas.adapter._generic import XML_NS_MAP
from basyx.aas.adapter.xml import xml_serialization
from server.app.adapter.jsonization import ServerAASToJsonEncoder


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


class ResultToJsonEncoder(ServerAASToJsonEncoder):
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


def http_exception_to_response(exception: werkzeug.exceptions.HTTPException, response_type: Type[APIResponse]) \
        -> APIResponse:
    headers = exception.get_headers()
    location = exception.get_response().location
    if location is not None:
        headers.append(("Location", location))
    if exception.code and exception.code >= 400:
        message = Message(type(exception).__name__, exception.description if exception.description is not None else "",
                          MessageType.ERROR)
        result = Result(False, [message])
    else:
        result = Result(False)
    return response_type(result, status=exception.code, headers=headers)


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
