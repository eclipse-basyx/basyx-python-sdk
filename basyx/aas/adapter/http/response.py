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
from werkzeug.wrappers import Request, Response

from aas import model
from aas.adapter.json import json_serialization
from aas.adapter.xml import xml_serialization

from typing import Dict, List, Sequence, Type, Union


@enum.unique
class MessageType(enum.Enum):
    UNSPECIFIED = enum.auto()
    DEBUG = enum.auto()
    INFORMATION = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    FATAL = enum.auto()
    EXCEPTION = enum.auto()

    def __str__(self):
        return self.name.capitalize()


class Message:
    def __init__(self, code: str, text: str, message_type: MessageType = MessageType.UNSPECIFIED):
        self.message_type = message_type
        self.code = code
        self.text = text


class Result:
    def __init__(self, success: bool, is_exception: bool, messages: List[Message]):
        self.success = success
        self.is_exception = is_exception
        self.messages = messages


# not all sequence types are json serializable, but Sequence is covariant,
# which is necessary for List[Submodel] or List[AssetAdministrationShell] to be valid for List[Referable]
ResponseData = Union[Result, model.Referable, Sequence[model.Referable]]

ResponseDataInternal = Union[Result, model.Referable, List[model.Referable]]


class APIResponse(abc.ABC, Response):
    def __init__(self, data: ResponseData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # convert possible sequence types to List (see line 54-55)
        if isinstance(data, Sequence):
            data = list(data)
        self.data = self.serialize(data)

    @abc.abstractmethod
    def serialize(self, data: ResponseDataInternal) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, data: ResponseDataInternal) -> str:
        return json.dumps(data, cls=ResultToJsonEncoder if isinstance(data, Result)
                          else json_serialization.AASToJsonEncoder)


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, data: ResponseDataInternal) -> str:
        return xml_element_to_str(response_data_to_xml(data))


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


def xml_element_to_str(element: etree.Element) -> str:
    # namespaces will just get assigned a prefix like nsX, where X is a positive integer
    # "aas" would be a better prefix for the AAS namespace
    # TODO: find a way to specify a namespace map when serializing
    return etree.tostring(element, xml_declaration=True, encoding="utf-8")


class ResultToJsonEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, Result):
            return result_to_json(obj)
        if isinstance(obj, Message):
            return message_to_json(obj)
        if isinstance(obj, MessageType):
            return str(obj)
        return super().default(obj)


def result_to_json(result: Result) -> Dict[str, object]:
    return {
        "success": result.success,
        "isException": result.is_exception,
        "messages": result.messages
    }


def message_to_json(message: Message) -> Dict[str, object]:
    return {
        "messageType": message.message_type,
        "code": message.code,
        "text": message.text
    }


def response_data_to_xml(data: ResponseDataInternal) -> etree.Element:
    if isinstance(data, Result):
        return result_to_xml(data)
    if isinstance(data, model.Referable):
        return referable_to_xml(data)
    if isinstance(data, List):
        elements: List[etree.Element] = [referable_to_xml(obj) for obj in data]
        wrapper = etree.Element("list")
        for elem in elements:
            wrapper.append(elem)
        return wrapper


def referable_to_xml(data: model.Referable) -> etree.Element:
    # TODO: maybe support more referables
    if isinstance(data, model.AssetAdministrationShell):
        return xml_serialization.asset_administration_shell_to_xml(data)
    if isinstance(data, model.Submodel):
        return xml_serialization.submodel_to_xml(data)
    if isinstance(data, model.SubmodelElement):
        return xml_serialization.submodel_element_to_xml(data)
    if isinstance(data, model.ConceptDictionary):
        return xml_serialization.concept_dictionary_to_xml(data)
    if isinstance(data, model.ConceptDescription):
        return xml_serialization.concept_description_to_xml(data)
    if isinstance(data, model.View):
        return xml_serialization.view_to_xml(data)
    if isinstance(data, model.Asset):
        return xml_serialization.asset_to_xml(data)
    raise TypeError(f"Referable {data} couldn't be serialized to xml (unsupported type)!")


def result_to_xml(result: Result) -> etree.Element:
    result_elem = etree.Element("result")
    success_elem = etree.Element("success")
    success_elem.text = xml_serialization.boolean_to_xml(result.success)
    is_exception_elem = etree.Element("isException")
    is_exception_elem.text = xml_serialization.boolean_to_xml(result.is_exception)
    messages_elem = etree.Element("messages")
    for message in result.messages:
        messages_elem.append(message_to_xml(message))
    result_elem.append(success_elem)
    result_elem.append(is_exception_elem)
    result_elem.append(messages_elem)
    return result_elem


def message_to_xml(message: Message) -> etree.Element:
    message_elem = etree.Element("message")
    message_type_elem = etree.Element("messageType")
    message_type_elem.text = str(message.message_type)
    code_elem = etree.Element("code")
    code_elem.text = message.code
    text_elem = etree.Element("text")
    text_elem.text = message.text
    message_elem.append(message_type_elem)
    message_elem.append(code_elem)
    message_elem.append(text_elem)
    return message_elem


def get_response_type(request: Request) -> Type[APIResponse]:
    response_types: Dict[str, Type[APIResponse]] = {
        "application/json": JsonResponse,
        "application/xml": XmlResponse,
        "text/xml": XmlResponseAlt
    }
    mime_type = request.accept_mimetypes.best_match(response_types)
    if mime_type is None:
        raise werkzeug.exceptions.NotAcceptable(f"This server supports the following content types: "
                                                + ", ".join(response_types.keys()))
    return response_types[mime_type]


def http_exception_to_response(exception: werkzeug.exceptions.HTTPException, response_type: Type[APIResponse]) \
        -> APIResponse:
    success: bool = exception.code < 400 if exception.code is not None else False
    message_type = MessageType.INFORMATION if success else MessageType.ERROR
    message = Message(type(exception).__name__, exception.description if exception.description is not None else "",
                      message_type)
    return response_type(Result(success, not success, [message]), status=exception.code,
                         headers=exception.get_headers())
