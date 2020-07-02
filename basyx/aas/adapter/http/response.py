# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import abc
import enum
import json
from lxml import etree  # type: ignore
import werkzeug.exceptions
from werkzeug.wrappers import Response

from aas import model
from aas.adapter.json import json_serialization
from aas.adapter.xml import xml_serialization

from typing import Dict, List, Optional, Type, Union


@enum.unique
class MessageType(enum.Enum):
    UNSPECIFIED = enum.auto()
    DEBUG = enum.auto()
    INFORMATION = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    FATAL = enum.auto()
    EXCEPTION = enum.auto()


class Message:
    def __init__(self, code: str, text: str, message_type: MessageType = MessageType.UNSPECIFIED):
        self.code = code
        self.text = text
        self.message_type = message_type


class Result:
    def __init__(self, success: bool, is_exception: bool, messages: List[Message]):
        self.success = success
        self.is_exception = is_exception
        self.messages = messages


ResponseDataType = Union[Result, model.Referable, List[model.Referable]]


class ResponseData(BaseException):
    def __init__(self, data: ResponseDataType, http_status_code: int = 200):
        self.data = data
        self.http_status_code = 200


class APIResponse(abc.ABC, Response):
    def __init__(self, data: ResponseData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = data.http_status_code
        self.data = self.serialize(data.data)

    @abc.abstractmethod
    def serialize(self, data: ResponseDataType) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, data: ResponseDataType) -> str:
        return json.dumps(data, cls=json_serialization.AASToJsonEncoder)


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, data: ResponseDataType) -> str:
        return ""


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


"""
A mapping of supported content types to their respective ResponseType.
The first content type in this dict will be preferred if the requester
doesn't specify preferred content types using the HTTP Accept header.
"""
RESPONSE_TYPES: Dict[str, Type[APIResponse]] = {
    "application/json": JsonResponse,
    "application/xml": XmlResponse,
    "text/xml": XmlResponseAlt
}


def create_result_response(code: str, text: str, message_type: MessageType, http_status_code: int = 200,
                           success: bool = False, is_exception: bool = False) -> ResponseData:
    message = Message(code, text, message_type)
    result = Result(success, is_exception, [message])
    return ResponseData(result, http_status_code)


def xml_element_to_str(element: etree.Element) -> str:
    # namespaces will just get assigned a prefix like nsX, where X is a positive integer
    # "aas" would be a better prefix for the AAS namespace
    # TODO: find a way to specify a namespace map when serializing
    return etree.tostring(element, xml_declaration=True, encoding="utf-8")
