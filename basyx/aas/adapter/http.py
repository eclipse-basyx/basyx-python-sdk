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

import base64
from binascii import Error as Base64Error
from werkzeug.datastructures import MIMEAccept, Headers
from werkzeug.exceptions import BadRequest, HTTPException, NotAcceptable, NotImplemented
from werkzeug.http import parse_accept_header
from werkzeug.routing import Map, Rule, Submount
from werkzeug.wrappers import Request, Response

from .. import model
from ._generic import IDENTIFIER_TYPES_INVERSE
from .json.json_serialization import asset_administration_shell_to_json

from typing import Dict, Iterable, Optional, Type


class JsonResponse(Response):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, content_type="application/json")


class XmlResponse(Response):
    def __init__(self, *args, content_type="application/xml", **kwargs):
        super().__init__(*args, **kwargs, content_type=content_type)


class XmlResponseAlt(XmlResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, content_type="text/xml")


    """
    A mapping of supported content types to their respective ResponseType.
    The first content type in this dict will be preferred if the requester doesn't specify preferred content types using
    and HTTP-"Accept" header.
    """
RESPONSE_TYPES = {
    "application/json": JsonResponse,
#    "application/xml": XmlResponse,
#    "text/xml": XmlResponseAlt
}


class WSGIApp:
    def __init__(self, object_store: model.AbstractObjectStore):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map: Map = Map([
            Submount("/api/v1", [
                # TODO: custom decoder for base64
                Rule("/shells/<string:aas_id>/aas", methods=["GET"], endpoint=self.get_aas),
                Rule("/shells/<string:aas_id>/abc")  # no endpoint => 501 not implemented
            ])
        ])

    def __call__(self, environ, start_response):
        response = self.handle_request(Request(environ))
        return response(environ, start_response)

    @classmethod
    def preferred_content_type(cls, headers: Headers, content_types: Iterable[str]) -> Optional[str]:
        accept_str: Optional[str] = headers.get("accept")
        if accept_str is None:
            # return first content type in case accept http header is not specified
            return next(iter(content_types))
        accept: MIMEAccept = parse_accept_header(accept_str, MIMEAccept)
        return accept.best_match(content_types)

    @classmethod
    def base64_param(cls, args: Dict[str, str], param: str) -> str:
        try:
            b64decoded = base64.b64decode(args[param])
        except Base64Error:
            raise BadRequest(f"URL-Parameter '{param}' with value '{args[param]}' is not a valid base64 string!")
        try:
            return b64decoded.decode("utf-8")
        except UnicodeDecodeError:
            raise BadRequest(f"URL-Parameter '{param}' with base64 decoded value '{b64decoded!r}' is not valid utf-8!")

    @classmethod
    def identifier_from_param(cls, args: Dict[str, str], param: str) -> model.Identifier:
        id_type, id_ = cls.base64_param(args, param).split(":", 1)
        try:
            return model.Identifier(id_, IDENTIFIER_TYPES_INVERSE[id_type])
        except KeyError:
            raise BadRequest(f"'{id_type}' is not a valid identifier type!")

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
            raise BadRequest(f"Object specified by id {identifier} is of unexpected type {type(identifiable)}! "
                             f"Expected type: {type_}")
        return identifiable

    def handle_request(self, request: Request):
        adapter = self.url_map.bind_to_environ(request.environ)
        # determine response content type
        # TODO: implement xml responses
        content_type = self.preferred_content_type(request.headers, RESPONSE_TYPES.keys())
        if content_type is None:
            return NotAcceptable(f"This server supports the following content types: "
                                 + ", ".join(RESPONSE_TYPES.keys()))
        response_type = RESPONSE_TYPES[content_type]
        try:
            endpoint, values = adapter.match()
            if endpoint is None:
                return NotImplemented("This route is not yet implemented.")
            endpoint(request, values, response_type)
        except HTTPException as e:
            # raised error leaving this function => 500
            return e

    # http api issues (depth parameter, repository interface (id encoding))
    def get_aas(self, request: Request, args: Dict[str, str], response_type: Type[Response]):
        # TODO: depth parameter
        aas_id = self.identifier_from_param(args, "aas_id")
        aas = self.get_obj_ts(aas_id, model.AssetAdministrationShell)
        # TODO: encode with xml for xml responses
        return response_type(asset_administration_shell_to_json(aas))


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from aas.examples.data.example_aas import create_full_example
    run_simple("localhost", 8080, WSGIApp(create_full_example()), use_debugger=True, use_reloader=True)
