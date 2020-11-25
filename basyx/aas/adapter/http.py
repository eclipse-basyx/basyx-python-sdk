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
import io
import json
from lxml import etree  # type: ignore
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
from werkzeug.exceptions import BadRequest, Conflict, NotFound
from werkzeug.routing import MapAdapter, Rule, Submount
from werkzeug.wrappers import Request, Response

from aas import model
from .xml import XMLConstructables, read_aas_xml_element, xml_serialization
from .json import StrippedAASToJsonEncoder, StrictStrippedAASFromJsonDecoder
from ._generic import IDENTIFIER_TYPES, IDENTIFIER_TYPES_INVERSE

from typing import Dict, Iterable, Optional, Tuple, Type, TypeVar, Union


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


ResultData = Union[object, Tuple[object, ...]]


class Result:
    def __init__(self, data: Optional[Union[ResultData, Error]]):
        # the following is True when data is None, which is the expected behavior
        self.success: bool = not isinstance(data, Error)
        self.data: Optional[ResultData] = None
        self.error: Optional[Error] = None
        if isinstance(data, Error):
            self.error = data
        else:
            self.data = data


class ResultToJsonEncoder(StrippedAASToJsonEncoder):
    @classmethod
    def _result_to_json(cls, result: Result) -> Dict[str, object]:
        return {
            "success": result.success,
            "error": result.error,
            "data": result.data
        }

    @classmethod
    def _error_to_json(cls, error: Error) -> Dict[str, object]:
        return {
            "type": error.type,
            "code": error.code,
            "text": error.text
        }

    def default(self, obj: object) -> object:
        if isinstance(obj, Result):
            return self._result_to_json(obj)
        if isinstance(obj, Error):
            return self._error_to_json(obj)
        if isinstance(obj, ErrorType):
            return str(obj)
        return super().default(obj)


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
        return json.dumps(result, cls=ResultToJsonEncoder, separators=(",", ":"))


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


def result_to_xml(result: Result, **kwargs) -> etree.Element:
    result_elem = etree.Element("result", **kwargs)
    success_elem = etree.Element("success")
    success_elem.text = xml_serialization.boolean_to_xml(result.success)
    if result.error is None:
        error_elem = etree.Element("error")
    else:
        error_elem = error_to_xml(result.error)
    data_elem = etree.Element("data")
    if result.data is not None:
        for element in result_data_to_xml(result.data):
            data_elem.append(element)
    result_elem.append(success_elem)
    result_elem.append(error_elem)
    result_elem.append(data_elem)
    return result_elem


def error_to_xml(error: Error) -> etree.Element:
    error_elem = etree.Element("error")
    type_elem = etree.Element("type")
    type_elem.text = str(error.type)
    code_elem = etree.Element("code")
    code_elem.text = error.code
    text_elem = etree.Element("text")
    text_elem.text = error.text
    error_elem.append(type_elem)
    error_elem.append(code_elem)
    error_elem.append(text_elem)
    return error_elem


def result_data_to_xml(data: ResultData) -> Iterable[etree.Element]:
    # for xml we can just append multiple elements to the data element
    # so multiple elements will be handled the same as a single element
    if not isinstance(data, tuple):
        data = (data,)
    for obj in data:
        yield aas_object_to_xml(obj)


def aas_object_to_xml(obj: object) -> etree.Element:
    # TODO: a similar function should be implemented in the xml serialization
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
    if exception.code and exception.code >= 400:
        error = Error(type(exception).__name__, exception.description if exception.description is not None else "",
                      ErrorType.ERROR)
        result = Result(error)
    else:
        result = Result(None)
    return response_type(result, status=exception.code, headers=headers)


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
        model.AASReference: XMLConstructables.AAS_REFERENCE,
        model.View: XMLConstructables.VIEW,
        model.Constraint: XMLConstructables.CONSTRAINT,
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
            rv = json.loads(request.get_data(), cls=StrictStrippedAASFromJsonDecoder)
            # TODO: the following is ugly, but necessary because references aren't self-identified objects
            #  in the json schema
            # TODO: json deserialization will always create an AASReference[Submodel], xml deserialization determines
            #  that automatically
            if expect_type is model.AASReference:
                rv = StrictStrippedAASFromJsonDecoder._construct_aas_reference(rv, model.Submodel)
        else:
            xml_data = io.BytesIO(request.get_data())
            rv = read_aas_xml_element(xml_data, type_constructables_map[expect_type], stripped=True, failsafe=False)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, etree.XMLSyntaxError) as e:
        raise BadRequest(str(e)) from e

    assert isinstance(rv, expect_type)
    return rv


def identifier_uri_encode(id_: model.Identifier) -> str:
    return IDENTIFIER_TYPES[id_.id_type] + ":" + werkzeug.urls.url_quote(id_.id, safe="")


def identifier_uri_decode(id_str: str) -> model.Identifier:
    try:
        id_type_str, id_ = id_str.split(":", 1)
    except ValueError:
        raise ValueError(f"Identifier '{id_str}' is not of format 'ID_TYPE:ID'")
    id_type = IDENTIFIER_TYPES_INVERSE.get(id_type_str)
    if id_type is None:
        raise ValueError(f"IdentifierType '{id_type_str}' is invalid")
    return model.Identifier(werkzeug.urls.url_unquote(id_), id_type)


class IdentifierConverter(werkzeug.routing.UnicodeConverter):
    def to_url(self, value: model.Identifier) -> str:
        return super().to_url(identifier_uri_encode(value))

    def to_python(self, value: str) -> model.Identifier:
        try:
            return identifier_uri_decode(super().to_python(value))
        except ValueError as e:
            raise BadRequest(str(e)) from e


class WSGIApp:
    def __init__(self, object_store: model.AbstractObjectStore):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map = werkzeug.routing.Map([
            Submount("/api/v1", [
                Submount("/aas/<identifier:aas_id>", [
                    Rule("/", methods=["GET"], endpoint=self.get_aas),
                    Submount("/submodels", [
                        Rule("/", methods=["GET"], endpoint=self.get_aas_submodel_refs),
                        Rule("/", methods=["POST"], endpoint=self.post_aas_submodel_refs),
                        Rule("/<identifier:sm_id>", methods=["GET"],
                             endpoint=self.get_aas_submodel_refs_specific),
                        Rule("/<identifier:sm_id>", methods=["DELETE"],
                             endpoint=self.delete_aas_submodel_refs_specific)
                    ]),
                    Submount("/views", [
                        Rule("/", methods=["GET"], endpoint=self.get_aas_views),
                        Rule("/", methods=["POST"], endpoint=self.post_aas_views),
                        Rule("/<string(minlength=1):view_idshort>", methods=["GET"],
                             endpoint=self.get_aas_views_specific),
                        Rule("/<string(minlength=1):view_idshort>", methods=["PUT"],
                             endpoint=self.put_aas_views_specific),
                        Rule("/<string(minlength=1):view_idshort>", methods=["DELETE"],
                             endpoint=self.delete_aas_views_specific)
                    ])
                ]),
                Submount("/submodels/<identifier:submodel_id>", [
                    Rule("/", methods=["GET"], endpoint=self.get_submodel),
                ])
            ])
        ], converters={"identifier": IdentifierConverter}, strict_slashes=False)

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

    def handle_request(self, request: Request):
        map_adapter: MapAdapter = self.url_map.bind_to_environ(request.environ)
        try:
            # redirect requests with a trailing slash to the path without trailing slash
            # if the path without trailing slash exists.
            # if not, map_adapter.match() will raise NotFound() in both cases
            if request.path != "/" and request.path.endswith("/"):
                map_adapter.match(request.path[:-1], request.method)
                # from werkzeug's internal routing redirection
                raise werkzeug.routing.RequestRedirect(
                    map_adapter.make_redirect_url(
                        werkzeug.urls.url_quote(request.path[:-1], map_adapter.map.charset, safe="/:|+"),
                        map_adapter.query_args
                    )
                )
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
        return response_t(Result(aas))

    def get_aas_submodel_refs(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        return response_t(Result(tuple(aas.submodel)))

    def post_aas_submodel_refs(self, request: Request, url_args: Dict, map_adapter: MapAdapter) -> Response:
        response_t = get_response_type(request)
        aas_identifier = url_args["aas_id"]
        aas = self._get_obj_ts(aas_identifier, model.AssetAdministrationShell)
        aas.update()
        sm_ref = parse_request_body(request, model.AASReference)
        # to give a location header in the response we have to be able to get the submodel identifier from the reference
        try:
            submodel_identifier = sm_ref.get_identifier()
        except ValueError as e:
            raise BadRequest(f"Can't resolve submodel identifier for given reference!") from e
        if sm_ref in aas.submodel:
            raise Conflict(f"{sm_ref!r} already exists!")
        aas.submodel.add(sm_ref)
        aas.commit()
        created_resource_url = map_adapter.build(self.get_aas_submodel_refs_specific, {
            "aas_id": aas_identifier,
            "sm_id": submodel_identifier
        }, force_external=True)
        return response_t(Result(sm_ref), status=201, headers={"Location": created_resource_url})

    def get_aas_submodel_refs_specific(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        sm_ref = self._get_aas_submodel_reference_by_submodel_identifier(aas, url_args["sm_id"])
        return response_t(Result(sm_ref))

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
        return response_t(Result(None))

    def get_aas_views(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        return response_t(Result(tuple(aas.view)))

    def post_aas_views(self, request: Request, url_args: Dict, map_adapter: MapAdapter) -> Response:
        response_t = get_response_type(request)
        aas_identifier = url_args["aas_id"]
        aas = self._get_obj_ts(aas_identifier, model.AssetAdministrationShell)
        aas.update()
        view = parse_request_body(request, model.View)
        if view.id_short in aas.view:
            raise Conflict(f"View with idShort {view.id_short} already exists!")
        aas.view.add(view)
        aas.commit()
        created_resource_url = map_adapter.build(self.get_aas_views_specific, {
            "aas_id": aas_identifier,
            "view_idshort": view.id_short
        }, force_external=True)
        return response_t(Result(view), status=201, headers={"Location": created_resource_url})

    def get_aas_views_specific(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        view_idshort = url_args["view_idshort"]
        view = aas.view.get(view_idshort)
        if view is None:
            raise NotFound(f"No view with idShort {view_idshort} found!")
        return response_t(Result(view))

    def put_aas_views_specific(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        view_idshort = url_args["view_idshort"]
        view = aas.view.get(view_idshort)
        if view is None:
            raise NotFound(f"No view with idShort {view_idshort} found!")
        new_view = parse_request_body(request, model.View)
        if new_view.id_short != view.id_short:
            raise BadRequest(f"idShort of new {new_view} doesn't match the old {view}")
        aas.view.remove(view)
        aas.view.add(new_view)
        return response_t(Result(new_view))

    def delete_aas_views_specific(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        aas = self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)
        aas.update()
        view_idshort = url_args["view_idshort"]
        if view_idshort not in aas.view:
            raise NotFound(f"No view with idShort {view_idshort} found!")
        aas.view.remove(view_idshort)
        return response_t(Result(None))

    # --------- SUBMODEL ROUTES ---------
    def get_submodel(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        response_t = get_response_type(request)
        submodel = self._get_obj_ts(url_args["submodel_id"], model.Submodel)
        submodel.update()
        return response_t(Result(submodel))


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    # use example_aas_missing_attributes, because the AAS from example_aas has no views
    from aas.examples.data.example_aas_missing_attributes import create_full_example
    run_simple("localhost", 8080, WSGIApp(create_full_example()), use_debugger=True, use_reloader=True)
