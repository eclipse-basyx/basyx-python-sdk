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


import urllib.parse
import werkzeug
from werkzeug.exceptions import BadRequest, NotAcceptable, NotFound, NotImplemented
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request

from aas import model

from .response import APIResponse, get_response_type, http_exception_to_response
from .._generic import IDENTIFIER_TYPES, IDENTIFIER_TYPES_INVERSE

from typing import Dict, Iterable, Optional, Type


def identifier_uri_encode(id_: model.Identifier) -> str:
    return IDENTIFIER_TYPES[id_.id_type] + ":" + urllib.parse.quote(id_.id, safe="")


def identifier_uri_decode(id_str: str) -> model.Identifier:
    try:
        id_type_str, id_ = id_str.split(":", 1)
    except ValueError as e:
        raise ValueError(f"Identifier '{id_str}' is not of format 'ID_TYPE:ID'")
    id_type = IDENTIFIER_TYPES_INVERSE.get(id_type_str)
    if id_type is None:
        raise ValueError(f"Identifier Type '{id_type_str}' is invalid")
    return model.Identifier(urllib.parse.unquote(id_), id_type)


class IdentifierConverter(werkzeug.routing.UnicodeConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_url(self, value: model.Identifier) -> str:
        return super().to_url(identifier_uri_encode(value))

    def to_python(self, value: str) -> model.Identifier:
        try:
            return identifier_uri_decode(super().to_python(value))
        except ValueError as e:
            raise BadRequest(str(e))


class WSGIApp:
    def __init__(self, object_store: model.AbstractObjectStore):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map = werkzeug.routing.Map([
            Submount("/api/v1.0", [
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

    # this is not used yet
    @classmethod
    def mandatory_request_param(cls, request: Request, param: str) -> str:
        req_param = request.args.get(param)
        if req_param is None:
            raise BadRequest(f"Parameter '{param}' is mandatory")
        return req_param

    def get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(f"No {type_.__name__} with {identifier} found!")
        return identifiable

    def handle_request(self, request: Request):
        adapter = self.url_map.bind_to_environ(request.environ)
        # determine response content type
        try:
            endpoint, values = adapter.match()
            if endpoint is None:
                return NotImplemented("This route is not yet implemented.")
            return endpoint(request, values)
        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.HTTPException as e:
            return http_exception_to_response(e, get_response_type(request))

    def get_aas(self, request: Request, url_args: Dict) -> APIResponse:
        # TODO: depth parameter
        response = get_response_type(request)
        return response(self.get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell))

    def get_sm(self, request: Request, url_args: Dict) -> APIResponse:
        # TODO: depth parameter
        response = get_response_type(request)
        return response(self.get_obj_ts(url_args["sm_id"], model.Submodel))
