# Copyright (c) 2024 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements the "Specification of the Asset Administration Shell Part 2 Application Programming Interfaces".
"""

import base64
import datetime
import io
import json
import itertools

import werkzeug.exceptions
import werkzeug.routing
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnprocessableEntity
from werkzeug.routing import MapAdapter, Rule, Submount
from werkzeug.wrappers import Request, Response

from basyx.aas import model
from .http import Base64URLConverter, APIResponse, XmlResponse, JsonResponse, XmlResponseAlt, Message, MessageType, Result, HTTPApiDecoder, get_response_type, http_exception_to_response, is_stripped_request

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Type, TypeVar, Union, Tuple, Set


T = TypeVar("T")

BASE64URL_ENCODING = "utf-8"

# Klasse, die das externe Mapping verwaltet
from basyx.aas import model

class ResolverAPI:
    def __init__(self, object_store: model.AbstractObjectStore,
                 base_path: str = "/api/v3.0"):
        self.object_store: model.AbstractObjectStore = object_store
        self.aas_to_assets: Dict[model.Identifier, Set[model.SpecificAssetId]] = {}
        self.asset_to_aas: Dict[model.SpecificAssetId, Set[model.Identifier]] = {}
        self.url_map = werkzeug.routing.Map([
            Submount(base_path, [
                Rule("/lookup/shellsByAssetLink", methods=["POST"],
                     endpoint=self.search_all_aas_ids_by_asset_link),
                Submount("/lookup/shells", [
                    Rule("/<base64url:aas_id>", methods=["GET"],
                         endpoint=self.get_all_asset_links_by_id),
                    Rule("/<base64url:aas_id>", methods=["POST"],
                         endpoint=self.post_all_asset_links_by_id),
                    Rule("/<base64url:aas_id>", methods=["DELETE"],
                         endpoint=self.delete_all_asset_links_by_id),
                ]),
            ])
        ], converters={
            "base64url": Base64URLConverter
        }, strict_slashes=False)

    def __call__(self, environ, start_response) -> Iterable[bytes]:
        response: Response = self.handle_request(Request(environ))
        return response(environ, start_response)

    @classmethod
    def _get_slice(cls, request: Request, iterator: Iterable[T]) -> Tuple[Iterator[T], int]:
        limit_str = request.args.get('limit', default="10")
        cursor_str = request.args.get('cursor', default="0")
        try:
            limit, cursor = int(limit_str), int(cursor_str)
            if limit < 0 or cursor < 0:
                raise ValueError
        except ValueError:
            raise BadRequest("Cursor and limit must be positive integers!")
        start_index = cursor
        end_index = cursor + limit
        paginated_slice = itertools.islice(iterator, start_index, end_index)
        return paginated_slice, end_index

    def handle_request(self, request: Request):
        map_adapter: MapAdapter = self.url_map.bind_to_environ(
            request.environ)
        try:
            response_t = get_response_type(request)
        except werkzeug.exceptions.NotAcceptable as e:
            return e
        try:
            endpoint, values = map_adapter.match()
            return endpoint(request, values, response_t=response_t,
                            map_adapter=map_adapter)
        # any raised error that leaves this function will cause a 500 internal server error
        # so catch raised http exceptions and return them
        except werkzeug.exceptions.HTTPException as e:
            return http_exception_to_response(e, response_t)

    # ------ Discovery ROUTES -------
    def search_all_aas_ids_by_asset_link(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                         **_kwargs) -> Response:
        """
        Returns a list of Asset Administration Shell IDs linked to specific asset identifiers or the global asset ID
        """
        asset_links = HTTPApiDecoder.request_body_list(request, model.AssetLink,
                                                       False)
        matching_aas_ids = set()
        for asset_link in asset_links:
            for asset_id, aas_ids in self.asset_to_aas.items():
                if asset_link.name==asset_id.name and asset_link.value==asset_id.value:
                    matching_aas_ids=aas_ids
        matching_aas_ids = list(matching_aas_ids)
        paginated_slice, cursor= self._get_slice(request, matching_aas_ids)

        return response_t(list(paginated_slice), cursor=cursor)

    def get_all_asset_links_by_id(self, request: Request,
                                  url_args: Dict,
                                  response_t: Type[APIResponse],
                                  **_kwargs) -> Response:
        """
        Returns a list of specific asset identifiers based on an Asset Administration Shell ID to edit discoverable content.
        The global asset ID is returned as specific asset ID with "name" equal to "globalAssetId" (see Constraint AASd-116).
        """
        aas_identifier = url_args.get("aas_id")
        matching_asset_ids = set()
        for ass_id, asset_ids in self.aas_to_assets.items():
            if ass_id==aas_identifier:
                matching_asset_ids=asset_ids
        matching_asset_ids = list(matching_asset_ids)
        return response_t(matching_asset_ids)

    def post_all_asset_links_by_id(self, request: Request,
                                   url_args: Dict,
                                   response_t: Type[APIResponse],
                                   **_kwargs) -> Response:
        """
        Creates specific asset identifiers linked to an Asset Administration Shell to edit discoverable content.
        """
        aas_identifier = url_args.get("aas_id")
        # Decode the request body to retrieve specific asset identifiers
        specific_asset_ids = HTTPApiDecoder.request_body_list(
            request, model.SpecificAssetId, False)

        # Ensure the aas_identifier exists in the dictionary
        if aas_identifier not in self.aas_to_assets:
            self.aas_to_assets[aas_identifier] = set()

        # Add specific asset IDs to the aas_to_assets dictionary
        asset_ids = self.aas_to_assets[aas_identifier]
        for specific_asset_id in specific_asset_ids:
            asset_ids.add(specific_asset_id)

        # Update asset_to_aas dictionary
        for specific_asset_id in specific_asset_ids:
            if specific_asset_id not in self.asset_to_aas:
                self.asset_to_aas[specific_asset_id] = set()
            self.asset_to_aas[specific_asset_id].add(aas_identifier)

        # Convert sets to lists for JSON serialization
        serializable_aas_to_assets = {key: list(value) for key, value in self.aas_to_assets.items()}

        return response_t(serializable_aas_to_assets)

    def delete_all_asset_links_by_id(self, request: Request,
                                     url_args: Dict,
                                     response_t: Type[APIResponse],
                                     **_kwargs) -> Response:
        """
        Deletes all specific asset identifiers linked to an Asset Administration Shell to edit discoverable content.
        """
        aas_identifier = url_args.get("aas_id")
        # Ensure the aas_identifier exists in the dictionary
        if aas_identifier in self.aas_to_assets:
            # Remove the links from aas_to_asset dictionary
            del self.aas_to_assets[aas_identifier]

        # Remove the aas_identifier from asset_to_aas dictionary
        for asset_id, aas_ids in list(self.asset_to_aas.items()):
            if aas_identifier in aas_ids:
                aas_ids.discard(aas_identifier)
                # Clean up empty sets
                if not aas_ids:
                    del self.asset_to_aas[asset_id]

        return response_t()

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8084, ResolverAPI(create_full_example()),
               use_debugger=True, use_reloader=True)
