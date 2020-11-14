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
from ..json import StrippedAASToJsonEncoder
from ..xml import xml_serialization

from typing import Dict, Iterable, Optional, Tuple, Type, Union


@enum.unique
class ErrorType(enum.Enum):
    UNSPECIFIED = enum.auto()
    DEBUG = enum.auto()
    INFORMATION = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    FATAL = enum.auto()
    EXCEPTION = enum.auto()

    def __str__(self):
        return self.name.capitalize()


class Error:
    def __init__(self, code: str, text: str, type_: ErrorType = ErrorType.UNSPECIFIED):
        self.type = type_
        self.code = code
        self.text = text


ResultData = Union[object, Tuple[object]]


class Result:
    def __init__(self, data: Optional[Union[ResultData, Error]] = None):
        self.success: bool = not isinstance(data, Error)
        self.data: Optional[ResultData] = None
        self.error: Optional[Error] = None
        if isinstance(data, Error):
            self.error = data
        else:
            self.data = data


class APIResponse(abc.ABC, Response):
    @abc.abstractmethod
    def __init__(self, result: Result, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = self.serialize(result)

    @abc.abstractmethod
    def serialize(self, result: Result) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, result: Result) -> str:
        return json.dumps(result, cls=ResultToJsonEncoder)


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, result: Result) -> str:
        result_elem = result_to_xml(result, nsmap=xml_serialization.NS_MAP)
        etree.cleanup_namespaces(result_elem)
        return etree.tostring(result_elem, xml_declaration=True, encoding="utf-8")


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


class ResultToJsonEncoder(StrippedAASToJsonEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, Result):
            return result_to_json(obj)
        if isinstance(obj, Error):
            return error_to_json(obj)
        if isinstance(obj, ErrorType):
            return str(obj)
        return super().default(obj)


def result_to_json(result: Result) -> Dict[str, object]:
    return {
        "success": result.success,
        "error": result.error,
        "data": result.data
    }


def error_to_json(error: Error) -> Dict[str, object]:
    return {
        "type": error.type,
        "code": error.code,
        "text": error.text
    }


def result_to_xml(result: Result, **kwargs) -> etree.Element:
    result_elem = etree.Element("result", **kwargs)
    success_elem = etree.Element("success")
    success_elem.text = xml_serialization.boolean_to_xml(result.success)
    error_elem = etree.Element("error")
    if result.error is not None:
        append_error_elements(error_elem, result.error)
    data_elem = etree.Element("data")
    if result.data is not None:
        for element in result_data_to_xml(result.data):
            data_elem.append(element)
    result_elem.append(success_elem)
    result_elem.append(error_elem)
    result_elem.append(data_elem)
    return result_elem


def append_error_elements(element: etree.Element, error: Error) -> None:
    type_elem = etree.Element("type")
    type_elem.text = str(error.type)
    code_elem = etree.Element("code")
    code_elem.text = error.code
    text_elem = etree.Element("text")
    text_elem.text = error.text
    element.append(type_elem)
    element.append(code_elem)
    element.append(text_elem)


def result_data_to_xml(data: ResultData) -> Iterable[etree.Element]:
    if not isinstance(data, tuple):
        data = (data,)
    for obj in data:
        yield aas_object_to_xml(obj)


def aas_object_to_xml(obj: object) -> etree.Element:
    if isinstance(obj, model.AssetAdministrationShell):
        return xml_serialization.asset_administration_shell_to_xml(obj)
    if isinstance(obj, model.Reference):
        return xml_serialization.reference_to_xml(obj)
    if isinstance(obj, model.View):
        return xml_serialization.view_to_xml(obj)
    if isinstance(obj, model.Submodel):
        return xml_serialization.submodel_to_xml(obj)
    # TODO: xml serialization needs a constraint_to_xml() function
    if isinstance(obj, model.Qualifier):
        return xml_serialization.qualifier_to_xml(obj)
    if isinstance(obj, model.Formula):
        return xml_serialization.formula_to_xml(obj)
    if isinstance(obj, model.SubmodelElement):
        return xml_serialization.submodel_element_to_xml(obj)
    raise TypeError(f"Serializing {type(obj).__name__} to XML is not supported!")


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
    headers = exception.get_headers()
    location = exception.get_response().location
    if location is not None:
        headers.append(("Location", location))
    result = Result()
    if exception.code and exception.code >= 400:
        error = Error(type(exception).__name__, exception.description if exception.description is not None else "",
                      ErrorType.ERROR)
        result = Result(error)
    return response_type(result, status=exception.code, headers=headers)
