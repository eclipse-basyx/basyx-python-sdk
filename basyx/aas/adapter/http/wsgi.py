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


import werkzeug
from werkzeug.exceptions import BadRequest, NotAcceptable, NotFound, NotImplemented
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request

from aas import model

from .response import RESPONSE_TYPES, MessageType, ResponseData, create_result_response
from .._generic import identifier_uri_decode, identifier_uri_encode

from typing import Dict, Iterable, Optional, Type


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
        req_param = request.args.get(param)
        if req_param is None:
            raise create_result_response("mandatory_param_missing", f"Parameter '{param}' is mandatory",
                                         MessageType.ERROR, 400)
        return req_param

    def get_obj_ts(self, identifier: model.Identifier, type_: Type[model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise create_result_response("identifier_not_found", f"No {type_.__name__} with {identifier} found!",
                                         MessageType.ERROR, 404)
        return identifiable

    def handle_request(self, request: Request):
        adapter = self.url_map.bind_to_environ(request.environ)
        # determine response content type
        preferred_response_type = self.preferred_content_type(request.headers, RESPONSE_TYPES.keys())
        if preferred_response_type is None:
            return NotAcceptable(f"This server supports the following content types: "
                                 + ", ".join(RESPONSE_TYPES.keys()))
        response_type = RESPONSE_TYPES[preferred_response_type]
        try:
            endpoint, values = adapter.match()
            if endpoint is None:
                return NotImplemented("This route is not yet implemented.")
            return response_type(endpoint(request, values))
        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.HTTPException as e:
            return e
        except ResponseData as rd:
            return response_type(rd)

    def get_aas(self, request: Request, url_args: Dict) -> ResponseData:
        # TODO: depth parameter
        return ResponseData(self.get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell))

    def get_sm(self, request: Request, url_args: Dict) -> ResponseData:
        # TODO: depth parameter
        return ResponseData(self.get_obj_ts(url_args["sm_id"], model.Submodel))
