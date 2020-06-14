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

import json
from lxml import etree  # type: ignore
import werkzeug
from werkzeug.exceptions import BadRequest, NotAcceptable, NotFound, NotImplemented
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request, Response

from .. import model
from ._generic import IDENTIFIER_TYPES_INVERSE
from .json import json_serialization
from .xml import xml_serialization

from typing import Dict, Iterable, Optional, Type


def xml_element_to_str(element: etree.Element) -> str:
    # namespaces will just get assigned a prefix like nsX, where X is a positive integer
    # "aas" would be a better prefix for the AAS namespace
    # TODO: find a way to specify a namespace map when serializing
    return etree.tostring(element, xml_declaration=True, encoding="utf-8")


class APIResponse(Response):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(data, model.AssetAdministrationShell):
            self.data = self.serialize_aas(data)
        elif isinstance(data, model.Submodel):
            self.data = self.serialize_sm(data)
        # TODO: encode non-data responses with json/xml as well (e.g. results and errors)

    def serialize_aas(self, aas: model.AssetAdministrationShell) -> str:
        pass

    def serialize_sm(self, aas: model.Submodel) -> str:
        pass


class JsonResponse(APIResponse):
    def __init__(self, *args, content_type="application/json", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize_aas(self, aas: model.AssetAdministrationShell) -> str:
        return json.dumps(aas, cls=json_serialization.AASToJsonEncoder)

    def serialize_sm(self, sm: model.Submodel) -> str:
        return json.dumps(sm, cls=json_serialization.AASToJsonEncoder)


class XmlResponse(APIResponse):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)

    def serialize_aas(self, aas: model.AssetAdministrationShell) -> str:
        return xml_element_to_str(xml_serialization.asset_administration_shell_to_xml(aas))

    def serialize_sm(self, sm: model.Submodel) -> str:
        return xml_element_to_str(xml_serialization.submodel_to_xml(sm))


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, content_type="text/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


"""
A mapping of supported content types to their respective ResponseType.
The first content type in this dict will be preferred if the requester
doesn't specify preferred content types using the HTTP Accept header.
"""
RESPONSE_TYPES = {
    "application/json": JsonResponse,
    "application/xml": XmlResponse,
    "text/xml": XmlResponseAlt
}


class IdentifierConverter(werkzeug.routing.PathConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value) -> model.Identifier:
        id_type, id_ = super().to_python(value).split(":", 1)
        try:
            return model.Identifier(id_, IDENTIFIER_TYPES_INVERSE[id_type])
        except KeyError:
            raise BadRequest(f"'{id_type}' is not a valid identifier type!")


class WSGIApp:
    def __init__(self, object_store: model.AbstractObjectStore):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map = werkzeug.routing.Map([
            Submount("/api/v1", [
                Submount("/shells/<identifier:aas_id>", [
                    Rule("/aas", methods=["GET"], endpoint=self.get_aas)
                ]),
                Submount("/submodels/<identifier:sm_id>", [
                    Rule("/submodel", methods=["GET"], endpoint=self.get_sm)
                ])
            ])
        ], converters={"identifier": IdentifierConverter})

    def __call__(self, environ, start_response):
        response = self.handle_request(Request(environ))
        return response(environ, start_response)

    @classmethod
    def preferred_content_type(cls, headers: werkzeug.datastructures.Headers, content_types: Iterable[str]) \
            -> Optional[str]:
        accept_str: Optional[str] = headers.get("accept")
        if accept_str is None:
            # return first content type in case accept http header is not specified
            return next(iter(content_types))
        accept = werkzeug.http.parse_accept_header(accept_str, werkzeug.datastructures.MIMEAccept)
        return accept.best_match(content_types)

    # this is not used yet
    @classmethod
    def mandatory_request_param(cls, request: Request, param: str) -> str:
        try:
            return request.args[param]
        except KeyError:
            raise BadRequest(f"Parameter '{param}' is mandatory")

    def get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(f"No '{type_.__name__}' with id '{identifier}' found!")
        return identifiable

    def handle_request(self, request: Request):
        adapter = self.url_map.bind_to_environ(request.environ)
        # determine response content type
        content_type = self.preferred_content_type(request.headers, RESPONSE_TYPES.keys())
        if content_type is None:
            return NotAcceptable(f"This server supports the following content types: "
                                 + ", ".join(RESPONSE_TYPES.keys()))
        response_type = RESPONSE_TYPES[content_type]
        try:
            endpoint, values = adapter.match()
            if endpoint is None:
                return NotImplemented("This route is not yet implemented.")
            return endpoint(request, values, response_type)
        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        # TODO: apply response types to http exceptions
        except werkzeug.exceptions.HTTPException as e:
            return e

    # http api issues (depth parameter, repository interface (id encoding))
    def get_aas(self, request: Request, args: Dict, response_type: Type[APIResponse]) -> APIResponse:
        # TODO: depth parameter
        aas = self.get_obj_ts(args["aas_id"], model.AssetAdministrationShell)
        return response_type(aas)

    def get_sm(self, request: Request, args: Dict, response_type: Type[APIResponse]) -> APIResponse:
        # TODO: depth parameter
        sm = self.get_obj_ts(args["sm_id"], model.Submodel)
        return response_type(sm)


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from aas.examples.data.example_aas import create_full_example
    run_simple("localhost", 8080, WSGIApp(create_full_example()), use_debugger=True, use_reloader=True)
