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
import base64
import binascii
import datetime
import enum
import io
import json
from lxml import etree  # type: ignore
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnprocessableEntity
from werkzeug.routing import MapAdapter, Rule, Submount
from werkzeug.wrappers import Request, Response

from aas import model
from .xml import XMLConstructables, read_aas_xml_element, xml_serialization
from .json import AASToJsonEncoder, StrictAASFromJsonDecoder, StrictStrippedAASFromJsonDecoder
from ._generic import IDENTIFIER_TYPES, IDENTIFIER_TYPES_INVERSE

from typing import Callable, Dict, List, Optional, Type, TypeVar, Union


# TODO: support the path/reference/etc. parameter


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
    def __init__(self, code: str, text: str, type_: MessageType = MessageType.UNDEFINED,
                 timestamp: Optional[datetime.datetime] = None):
        self.code = code
        self.text = text
        self.messageType = type_
        self.timestamp = timestamp if timestamp is not None else datetime.datetime.utcnow()


class Result:
    def __init__(self, success: bool, messages: Optional[List[Message]] = None):
        if messages is None:
            messages = []
        self.success: bool = success
        self.messages: List[Message] = messages


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
            "messageType": message.messageType,
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


ResponseData = Union[Result, object, List[object]]


class APIResponse(abc.ABC, Response):
    @abc.abstractmethod
    def __init__(self, obj: Optional[ResponseData] = None, stripped: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if obj is None:
            self.status_code = 204
        else:
            self.data = self.serialize(obj, stripped)

    @abc.abstractmethod
    def serialize(self, obj: ResponseData, stripped: bool) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, obj: ResponseData, stripped: bool) -> str:
        return json.dumps(obj, cls=StrippedResultToJsonEncoder if stripped else ResultToJsonEncoder,
                          separators=(",", ":"))


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize(self, obj: ResponseData, stripped: bool) -> str:
        # TODO: xml serialization doesn't support stripped objects
        if isinstance(obj, Result):
            response_elem = result_to_xml(obj, nsmap=xml_serialization.NS_MAP)
            etree.cleanup_namespaces(response_elem)
        else:
            if isinstance(obj, list):
                response_elem = etree.Element("list", nsmap=xml_serialization.NS_MAP)
                for obj in obj:
                    response_elem.append(aas_object_to_xml(obj))
                etree.cleanup_namespaces(response_elem)
            else:
                # dirty hack to be able to use the namespace prefixes defined in xml_serialization.NS_MAP
                parent = etree.Element("parent", nsmap=xml_serialization.NS_MAP)
                response_elem = aas_object_to_xml(obj)
                parent.append(response_elem)
                etree.cleanup_namespaces(parent)
        return etree.tostring(response_elem, xml_declaration=True, encoding="utf-8")


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


def result_to_xml(result: Result, **kwargs) -> etree.Element:
    result_elem = etree.Element("result", **kwargs)
    success_elem = etree.Element("success")
    success_elem.text = xml_serialization.boolean_to_xml(result.success)
    messages_elem = etree.Element("messages")
    for message in result.messages:
        messages_elem.append(message_to_xml(message))

    result_elem.append(success_elem)
    result_elem.append(messages_elem)
    return result_elem


def message_to_xml(message: Message) -> etree.Element:
    message_elem = etree.Element("message")
    message_type_elem = etree.Element("messageType")
    message_type_elem.text = str(message.messageType)
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


def aas_object_to_xml(obj: object) -> etree.Element:
    # TODO: a similar function should be implemented in the xml serialization
    if isinstance(obj, model.AssetAdministrationShell):
        return xml_serialization.asset_administration_shell_to_xml(obj)
    if isinstance(obj, model.AssetInformation):
        return xml_serialization.asset_information_to_xml(obj)
    if isinstance(obj, model.Reference):
        return xml_serialization.reference_to_xml(obj)
    if isinstance(obj, model.Submodel):
        return xml_serialization.submodel_to_xml(obj)
    # TODO: xml serialization needs a constraint_to_xml() function
    if isinstance(obj, model.Qualifier):
        return xml_serialization.qualifier_to_xml(obj)
    if isinstance(obj, model.SubmodelElement):
        return xml_serialization.submodel_element_to_xml(obj)
    raise TypeError(f"Serializing {type(obj).__name__} to XML is not supported!")


def get_response_type(request: Request) -> Type[APIResponse]:
    response_types: Dict[str, Type[APIResponse]] = {
        "application/json": JsonResponse,
        "application/xml": XmlResponse,
        "text/xml": XmlResponseAlt
    }
    if len(request.accept_mimetypes) == 0:
        return JsonResponse
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
    if exception.code and exception.code >= 400:
        message = Message(type(exception).__name__, exception.description if exception.description is not None else "",
                          MessageType.ERROR)
        result = Result(False, [message])
    else:
        result = Result(False)
    return response_type(result, status=exception.code, headers=headers)


def is_stripped_request(request: Request) -> bool:
    return request.args.get("level") == "core"


T = TypeVar("T")


def parse_request_body(request: Request, expect_type: Type[T]) -> T:
    """
    TODO: werkzeug documentation recommends checking the content length before retrieving the body to prevent
          running out of memory. but it doesn't state how to check the content length
          also: what would be a reasonable maximum content length? the request body isn't limited by the xml/json schema
        In the meeting (25.11.2020) we discussed, this may refer to a reverse proxy in front of this WSGI app,
        which should limit the maximum content length.
    """
    type_constructables_map = {
        model.AssetAdministrationShell: XMLConstructables.ASSET_ADMINISTRATION_SHELL,
        model.AssetInformation: XMLConstructables.ASSET_INFORMATION,
        model.AASReference: XMLConstructables.AAS_REFERENCE,
        model.View: XMLConstructables.VIEW,
        model.Qualifier: XMLConstructables.QUALIFIER,
        model.SubmodelElement: XMLConstructables.SUBMODEL_ELEMENT
    }

    if expect_type not in type_constructables_map:
        raise TypeError(f"Parsing {expect_type} is not supported!")

    valid_content_types = ("application/json", "application/xml", "text/xml")

    if request.mimetype not in valid_content_types:
        raise werkzeug.exceptions.UnsupportedMediaType(f"Invalid content-type: {request.mimetype}! Supported types: "
                                                       + ", ".join(valid_content_types))

    try:
        if request.mimetype == "application/json":
            decoder: Type[StrictAASFromJsonDecoder] = StrictStrippedAASFromJsonDecoder if is_stripped_request(request) \
                                                      else StrictAASFromJsonDecoder
            rv = json.loads(request.get_data(), cls=decoder)
            # TODO: the following is ugly, but necessary because references aren't self-identified objects
            #  in the json schema
            # TODO: json deserialization will always create an AASReference[Submodel], xml deserialization determines
            #  that automatically
            if expect_type is model.AASReference:
                rv = decoder._construct_aas_reference(rv, model.Submodel)
            elif expect_type is model.AssetInformation:
                rv = decoder._construct_asset_information(rv, model.AssetInformation)
        else:
            try:
                xml_data = io.BytesIO(request.get_data())
                rv = read_aas_xml_element(xml_data, type_constructables_map[expect_type],
                                          stripped=is_stripped_request(request), failsafe=False)
            except (KeyError, ValueError) as e:
                # xml deserialization creates an error chain. since we only return one error, return the root cause
                f: BaseException = e
                while f.__cause__ is not None:
                    f = f.__cause__
                raise f from e
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, etree.XMLSyntaxError, model.AASConstraintViolation) \
            as e:
        raise UnprocessableEntity(str(e)) from e

    if not isinstance(rv, expect_type):
        raise UnprocessableEntity(f"Object {rv!r} is not of type {expect_type.__name__}!")
    return rv


class IdentifierConverter(werkzeug.routing.UnicodeConverter):
    encoding = "utf-8"

    def to_url(self, value: model.Identifier) -> str:
        return super().to_url(base64.urlsafe_b64encode((IDENTIFIER_TYPES[value.id_type] + ":" + value.id)
                                                       .encode(self.encoding)))

    def to_python(self, value: str) -> model.Identifier:
        value = super().to_python(value)
        try:
            decoded = base64.urlsafe_b64decode(super().to_python(value)).decode(self.encoding)
        except binascii.Error:
            raise BadRequest(f"Encoded identifier {value} is invalid base64url!")
        except UnicodeDecodeError:
            raise BadRequest(f"Encoded base64url value is not a valid utf-8 string!")
        id_type_str, id_ = decoded.split(":", 1)
        try:
            return model.Identifier(id_, IDENTIFIER_TYPES_INVERSE[id_type_str])
        except KeyError:
            raise BadRequest(f"{id_type_str} is not a valid identifier type!")


class IdShortPathConverter(werkzeug.routing.UnicodeConverter):
    id_short_sep = "."

    @classmethod
    def validate_id_short(cls, id_short: str) -> bool:
        try:
            model.MultiLanguageProperty(id_short)
        except model.AASConstraintViolation:
            return False
        return True

    def to_url(self, value: List[str]) -> str:
        for id_short in value:
            if not self.validate_id_short(id_short):
                raise ValueError(f"{id_short} is not a valid id_short!")
        return super().to_url(".".join(id_short for id_short in value))

    def to_python(self, value: str) -> List[str]:
        id_shorts = super().to_python(value).split(self.id_short_sep)
        for id_short in id_shorts:
            if not self.validate_id_short(id_short):
                raise BadRequest(f"{id_short} is not a valid id_short!")
        return id_shorts


class WSGIApp:
    def __init__(self, object_store: model.AbstractObjectStore):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map = werkzeug.routing.Map([
            Submount("/api/v1", [
                Submount("/aas/<identifier:aas_id>/aas", [
                    Rule("/", methods=["GET"], endpoint=self.get_aas),
                    Rule("/", methods=["PUT"], endpoint=self.put_aas),
                    Rule("/assetInformation", methods=["GET"], endpoint=self.get_aas_asset_information),
                    Rule("/assetInformation", methods=["PUT"], endpoint=self.put_aas_asset_information),
                    Submount("/submodels", [
                        Rule("/", methods=["GET"], endpoint=self.get_aas_submodel_refs),
                        Rule("/<identifier:sm_id>/", methods=["PUT"],
                             endpoint=self.put_aas_submodel_refs),
                        Rule("/<identifier:sm_id>/", methods=["DELETE"],
                             endpoint=self.delete_aas_submodel_refs_specific)
                    ])
                ]),
                Submount("/submodels/<identifier:submodel_id>", [
                    Rule("/", methods=["GET"], endpoint=self.get_submodel),
                    Rule("/submodelElements/", methods=["GET"], endpoint=self.get_submodel_submodel_elements),
                    Rule("/submodelElements/", methods=["POST"], endpoint=self.post_submodel_submodel_elements),
                    Submount("/<id_short_path:id_shorts>", [
                        Rule("/", methods=["GET"],
                             endpoint=self.get_submodel_submodel_elements_specific_nested),
                        Rule("/", methods=["PUT"],
                             endpoint=self.put_submodel_submodel_elements_specific_nested),
                        Rule("/", methods=["DELETE"],
                             endpoint=self.delete_submodel_submodel_elements_specific_nested),
                        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
                        # see https://github.com/python/mypy/issues/5374
                        Rule("/values/", methods=["GET"],
                             endpoint=self.factory_get_submodel_submodel_elements_nested_attr(
                                 model.SubmodelElementCollection, "value")),  # type: ignore
                        Rule("/values/", methods=["POST"],
                             endpoint=self.factory_post_submodel_submodel_elements_nested_attr(
                                 model.SubmodelElementCollection, "value")),  # type: ignore
                        Rule("/annotations/", methods=["GET"],
                             endpoint=self.factory_get_submodel_submodel_elements_nested_attr(
                                 model.AnnotatedRelationshipElement, "annotation")),
                        Rule("/annotations/", methods=["POST"],
                             endpoint=self.factory_post_submodel_submodel_elements_nested_attr(
                                 model.AnnotatedRelationshipElement, "annotation",
                                 request_body_type=model.DataElement)),  # type: ignore
                        Rule("/statements/", methods=["GET"],
                             endpoint=self.factory_get_submodel_submodel_elements_nested_attr(model.Entity,
                                                                                              "statement")),
                        Rule("/statements/", methods=["POST"],
                             endpoint=self.factory_post_submodel_submodel_elements_nested_attr(model.Entity,
                                                                                               "statement")),
                        Submount("/constraints", [
                            Rule("/", methods=["GET"], endpoint=self.get_submodel_submodel_element_constraints),
                            Rule("/", methods=["POST"], endpoint=self.post_submodel_submodel_element_constraints),
                            Rule("/<path:qualifier_type>/", methods=["GET"],
                                 endpoint=self.get_submodel_submodel_element_constraints),
                            Rule("/<path:qualifier_type>/", methods=["PUT"],
                                 endpoint=self.put_submodel_submodel_element_constraints),
                            Rule("/<path:qualifier_type>/", methods=["DELETE"],
                                 endpoint=self.delete_submodel_submodel_element_constraints),
                        ])
                    ]),
                    Submount("/constraints", [
                        Rule("/", methods=["GET"], endpoint=self.get_submodel_submodel_element_constraints),
                        Rule("/", methods=["POST"], endpoint=self.post_submodel_submodel_element_constraints),
                        Rule("/<path:qualifier_type>/", methods=["GET"],
                             endpoint=self.get_submodel_submodel_element_constraints),
                        Rule("/<path:qualifier_type>/", methods=["PUT"],
                             endpoint=self.put_submodel_submodel_element_constraints),
                        Rule("/<path:qualifier_type>/", methods=["DELETE"],
                             endpoint=self.delete_submodel_submodel_element_constraints),
                    ])
                ])
            ])
        ], converters={
            "identifier": IdentifierConverter,
            "id_short_path": IdShortPathConverter
        })

    def __call__(self, environ, start_response):
        response = self.handle_request(Request(environ))
        return response(environ, start_response)

    def _get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(f"No {type_.__name__} with {identifier} found!")
        return identifiable

    def _resolve_reference(self, reference: model.AASReference[model.base._RT]) -> model.base._RT:
        try:
            return reference.resolve(self.object_store)
        except (KeyError, TypeError, model.UnexpectedTypeError) as e:
            raise werkzeug.exceptions.InternalServerError(str(e)) from e

    @classmethod
    def _get_aas_submodel_reference_by_submodel_identifier(cls, aas: model.AssetAdministrationShell,
                                                           sm_identifier: model.Identifier) \
            -> model.AASReference[model.Submodel]:
        for sm_ref in aas.submodel:
            if sm_ref.get_identifier() == sm_identifier:
                return sm_ref
        raise NotFound(f"No reference to submodel with {sm_identifier} found!")

    @classmethod
    def _get_nested_submodel_element(cls, namespace: model.UniqueIdShortNamespace, id_shorts: List[str]) \
            -> model.SubmodelElement:
        current_namespace: Union[model.UniqueIdShortNamespace, model.SubmodelElement] = namespace
        for id_short in id_shorts:
            current_namespace = cls._expect_namespace(current_namespace, id_short)
            next_obj = cls._namespace_submodel_element_op(current_namespace, current_namespace.get_referable, id_short)
            if not isinstance(next_obj, model.SubmodelElement):
                raise werkzeug.exceptions.InternalServerError(f"{next_obj}, child of {current_namespace!r}, "
                                                              f"is not a submodel element!")
            current_namespace = next_obj
        if not isinstance(current_namespace, model.SubmodelElement):
            raise ValueError("No id_shorts specified!")
        return current_namespace

    @classmethod
    def _get_submodel_or_nested_submodel_element(cls, submodel: model.Submodel, id_shorts: List[str]) \
            -> Union[model.Submodel, model.SubmodelElement]:
        try:
            return cls._get_nested_submodel_element(submodel, id_shorts)
        except ValueError:
            return submodel

    @classmethod
    def _expect_namespace(cls, obj: object, needle: str) -> model.UniqueIdShortNamespace:
        if not isinstance(obj, model.UniqueIdShortNamespace):
            raise BadRequest(f"{obj!r} is not a namespace, can't locate {needle}!")
        return obj

    @classmethod
    def _namespace_submodel_element_op(cls, namespace: model.UniqueIdShortNamespace, op: Callable[[str], T], arg: str) \
            -> T:
        try:
            return op(arg)
        except KeyError as e:
            raise NotFound(f"Submodel element with id_short {arg} not found in {namespace!r}") from e

    def handle_request(self, request: Request):
        map_adapter: MapAdapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = map_adapter.match()
            if endpoint is None:
                raise werkzeug.exceptions.NotImplemented("This route is not yet implemented.")
            return endpoint(request, values, map_adapter=map_adapter)
        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.NotAcceptable as e:
            return e
        except werkzeug.exceptions.HTTPException as e:
            try:
                # get_response_type() may raise a NotAcceptable error, so we have to handle that
                return http_exception_to_response(e, get_response_type(request))
            except werkzeug.exceptions.NotAcceptable as e:
                return e

    # --------- AAS ROUTES ---------
    def get_aas(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        return response_t(aas, stripped=is_stripped_request(request))

    def put_aas(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        aas_new = parse_request_body(request, model.AssetAdministrationShell)
        aas.update_from(aas_new)
        aas.commit()
        return response_t()

    def get_aas_asset_information(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        return response_t(aas.asset_information)

    def put_aas_asset_information(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        aas.asset_information = parse_request_body(request, model.AssetInformation)
        aas.commit()
        return response_t()

    def get_aas_submodel_refs(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        return response_t(list(aas.submodel))

    def put_aas_submodel_refs(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas_identifier = url_args["aas_id"]
        aas = self._get_obj_ts(aas_identifier, model.AssetAdministrationShell)
        aas.update()
        sm_ref = parse_request_body(request, model.AASReference)
        if sm_ref in aas.submodel:
            raise Conflict(f"{sm_ref!r} already exists!")
        aas.submodel.add(sm_ref)
        aas.commit()
        return response_t(sm_ref, status=201)

    def delete_aas_submodel_refs_specific(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        sm_ref = self._get_aas_submodel_reference_by_submodel_identifier(aas, url_args["sm_id"])
        # use remove(sm_ref) because it raises a KeyError if sm_ref is not present
        # sm_ref must be present because _get_aas_submodel_reference_by_submodel_identifier() found it there
        # so if sm_ref is not in aas.submodel, this implementation is bugged and the raised KeyError will result
        # in an InternalServerError
        aas.submodel.remove(sm_ref)
        aas.commit()
        return response_t()

    # --------- SUBMODEL ROUTES ---------
    def get_submodel(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        return response_t(Result(submodel))

    def get_submodel_submodel_elements(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        return response_t(Result(tuple(submodel.submodel_element)))

    def post_submodel_submodel_elements(self, request: Request, url_args: Dict, map_adapter: MapAdapter) -> Response:
        response_t = get_response_type(request)
        submodel_identifier = url_args["submodel_id"]
        submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
        submodel.update()
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        submodel_element = parse_request_body(request, model.SubmodelElement)  # type: ignore
        if submodel.submodel_element.contains_id("id_short", submodel_element.id_short):
            raise Conflict(f"Submodel element with id_short {submodel_element.id_short} already exists!")
        submodel.submodel_element.add(submodel_element)
        submodel.commit()
        created_resource_url = map_adapter.build(self.get_submodel_submodel_elements_specific_nested, {
            "submodel_id": submodel_identifier,
            "id_shorts": [submodel_element.id_short]
        }, force_external=True)
        return response_t(Result(submodel_element), status=201, headers={"Location": created_resource_url})

    def get_submodel_submodel_elements_specific_nested(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        submodel_element = self._get_nested_submodel_element(submodel, url_args["id_shorts"])
        return response_t(Result(submodel_element))

    def put_submodel_submodel_elements_specific_nested(self, request: Request, url_args: Dict,
                                                       map_adapter: MapAdapter) -> Response:
        response_t = get_response_type(request)
        submodel_identifier = url_args["submodel_id"]
        submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
        submodel.update()
        id_short_path = url_args["id_shorts"]
        submodel_element = self._get_nested_submodel_element(submodel, id_short_path)
        current_id_short = submodel_element.id_short
        # TODO: remove the following type: ignore comments when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        new_submodel_element = parse_request_body(request, model.SubmodelElement)  # type: ignore
        if type(submodel_element) is not type(new_submodel_element):
            raise UnprocessableEntity(f"Type of new submodel element {new_submodel_element} doesn't not match "
                                      f"the current submodel element {submodel_element}")
        # TODO: raise conflict if the following fails
        submodel_element.update_from(new_submodel_element)
        submodel_element.commit()
        if new_submodel_element.id_short.upper() != current_id_short.upper():
            created_resource_url = map_adapter.build(self.put_submodel_submodel_elements_specific_nested, {
                "submodel_id": submodel_identifier,
                "id_shorts": id_short_path[:-1] + [submodel_element.id_short]
            }, force_external=True)
            return response_t(Result(submodel_element), status=201, headers={"Location": created_resource_url})
        return response_t(Result(submodel_element))

    def delete_submodel_submodel_elements_specific_nested(self, request: Request, url_args: Dict, **_kwargs) \
            -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        id_shorts: List[str] = url_args["id_shorts"]
        parent: model.UniqueIdShortNamespace = submodel
        if len(id_shorts) > 1:
            parent = self._expect_namespace(
                self._get_nested_submodel_element(submodel, id_shorts[:-1]),
                id_shorts[-1]
            )
        self._namespace_submodel_element_op(parent, parent.remove_referable, id_shorts[-1])
        return response_t(Result(None))

    def get_submodel_submodel_element_constraints(self, request: Request, url_args: Dict, **_kwargs) \
            -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        sm_or_se = self._get_submodel_or_nested_submodel_element(submodel, url_args.get("id_shorts", []))
        qualifier_type = url_args.get("qualifier_type")
        if qualifier_type is None:
            return response_t(Result(tuple(sm_or_se.qualifier)))
        try:
            return response_t(Result(sm_or_se.get_qualifier_by_type(qualifier_type)))
        except KeyError:
            raise NotFound(f"No constraint with type {qualifier_type} found in {sm_or_se}")

    def post_submodel_submodel_element_constraints(self, request: Request, url_args: Dict, map_adapter: MapAdapter) \
            -> Response:
        response_t = get_response_type(request)
        submodel_identifier = url_args["submodel_id"]
        submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
        submodel.update()
        id_shorts: List[str] = url_args.get("id_shorts", [])
        sm_or_se = self._get_submodel_or_nested_submodel_element(submodel, id_shorts)
        qualifier = parse_request_body(request, model.Qualifier)
        if sm_or_se.qualifier.contains_id("type", qualifier.type):
            raise Conflict(f"Qualifier with type {qualifier.type} already exists!")
        sm_or_se.qualifier.add(qualifier)
        sm_or_se.commit()
        created_resource_url = map_adapter.build(self.get_submodel_submodel_element_constraints, {
            "submodel_id": submodel_identifier,
            "id_shorts": id_shorts if len(id_shorts) != 0 else None,
            "qualifier_type": qualifier.type
        }, force_external=True)
        return response_t(Result(qualifier), status=201, headers={"Location": created_resource_url})

    def put_submodel_submodel_element_constraints(self, request: Request, url_args: Dict, map_adapter: MapAdapter) \
            -> Response:
        response_t = get_response_type(request)
        submodel_identifier = url_args["submodel_id"]
        submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
        submodel.update()
        id_shorts: List[str] = url_args.get("id_shorts", [])
        sm_or_se = self._get_submodel_or_nested_submodel_element(submodel, id_shorts)
        new_qualifier = parse_request_body(request, model.Qualifier)
        qualifier_type = url_args["qualifier_type"]
        try:
            qualifier = sm_or_se.get_qualifier_by_type(qualifier_type)
        except KeyError:
            raise NotFound(f"No constraint with type {qualifier_type} found in {sm_or_se}")
        if type(qualifier) is not type(new_qualifier):
            raise UnprocessableEntity(f"Type of new qualifier {new_qualifier} doesn't not match "
                                      f"the current submodel element {qualifier}")
        qualifier_type_changed = qualifier_type != new_qualifier.type
        if qualifier_type_changed and sm_or_se.qualifier.contains_id("type", new_qualifier.type):
            raise Conflict(f"A qualifier of type {new_qualifier.type} already exists for {sm_or_se}")
        sm_or_se.remove_qualifier_by_type(qualifier.type)
        sm_or_se.qualifier.add(new_qualifier)
        sm_or_se.commit()
        if qualifier_type_changed:
            created_resource_url = map_adapter.build(self.get_submodel_submodel_element_constraints, {
                "submodel_id": submodel_identifier,
                "id_shorts": id_shorts if len(id_shorts) != 0 else None,
                "qualifier_type": new_qualifier.type
            }, force_external=True)
            return response_t(Result(new_qualifier), status=201, headers={"Location": created_resource_url})
        return response_t(Result(new_qualifier))

    def delete_submodel_submodel_element_constraints(self, request: Request, url_args: Dict, **_kwargs) \
            -> Response:
        response_t = get_response_type(request)
        submodel_identifier = url_args["submodel_id"]
        submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
        submodel.update()
        id_shorts: List[str] = url_args.get("id_shorts", [])
        sm_or_se = self._get_submodel_or_nested_submodel_element(submodel, id_shorts)
        qualifier_type = url_args["qualifier_type"]
        try:
            sm_or_se.remove_qualifier_by_type(qualifier_type)
        except KeyError:
            raise NotFound(f"No constraint with type {qualifier_type} found in {sm_or_se}")
        sm_or_se.commit()
        return response_t(Result(None))

    # --------- SUBMODEL ROUTE FACTORIES ---------
    def factory_get_submodel_submodel_elements_nested_attr(self, type_: Type[model.Referable], attr: str) \
            -> Callable[[Request, Dict], Response]:
        def route(request: Request, url_args: Dict, **_kwargs) -> Response:
            response_t = get_response_type(request)
            submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
            submodel.update()
            submodel_element = self._get_nested_submodel_element(submodel, url_args["id_shorts"])
            if not isinstance(submodel_element, type_):
                raise UnprocessableEntity(f"Submodel element {submodel_element} is not a(n) {type_.__name__}!")
            return response_t(Result(tuple(getattr(submodel_element, attr))))
        return route

    def factory_post_submodel_submodel_elements_nested_attr(self, type_: Type[model.Referable], attr: str,
                                                            request_body_type: Type[model.SubmodelElement]
                                                            = model.SubmodelElement) \
            -> Callable[[Request, Dict, MapAdapter], Response]:
        def route(request: Request, url_args: Dict, map_adapter: MapAdapter) -> Response:
            response_t = get_response_type(request)
            submodel_identifier = url_args["submodel_id"]
            submodel = self._get_obj_ts(submodel_identifier, model.Submodel)
            submodel.update()
            id_shorts = url_args["id_shorts"]
            submodel_element = self._get_nested_submodel_element(submodel, id_shorts)
            if not isinstance(submodel_element, type_):
                raise UnprocessableEntity(f"Submodel element {submodel_element} is not a(n) {type_.__name__}!")
            new_submodel_element = parse_request_body(request, request_body_type)
            if getattr(submodel_element, attr).contains_id("id_short", new_submodel_element.id_short):
                raise Conflict(f"Submodel element with id_short {new_submodel_element.id_short} already exists!")
            getattr(submodel_element, attr).add(new_submodel_element)
            submodel_element.commit()
            created_resource_url = map_adapter.build(self.get_submodel_submodel_elements_specific_nested, {
                "submodel_id": submodel_identifier,
                "id_shorts": id_shorts + [new_submodel_element.id_short]
            }, force_external=True)
            return response_t(Result(new_submodel_element), status=201, headers={"Location": created_resource_url})
        return route


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    # use example_aas_missing_attributes, because the AAS from example_aas has no views
    from aas.examples.data.example_aas_missing_attributes import create_full_example
    run_simple("localhost", 8080, WSGIApp(create_full_example()), use_debugger=True, use_reloader=True)
