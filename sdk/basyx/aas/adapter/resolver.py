# Copyright (c) 2024 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements the "Specification of the Asset Administration Shell Part 2 Application Programming Interfaces".
"""

import abc
import base64
import binascii
import datetime
import enum
import io
import json
import itertools

from lxml import etree
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnprocessableEntity
from werkzeug.routing import MapAdapter, Rule, Submount
from werkzeug.wrappers import Request, Response
from werkzeug.datastructures import FileStorage

from basyx.aas import model
from ._generic import XML_NS_MAP
from .xml import XMLConstructables, read_aas_xml_element, xml_serialization, object_to_xml_element
from .json import AASToJsonEncoder, StrictAASFromJsonDecoder, StrictStrippedAASFromJsonDecoder
from . import aasx
from .http import Base64URLConverter, APIResponse, XmlResponse, JsonResponse, XmlResponseAlt, Message, MessageType, Result, HTTPApiDecoder

from .http import get_response_type, http_exception_to_response, is_stripped_request

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Type, TypeVar, Union, Tuple


T = TypeVar("T")

BASE64URL_ENCODING = "utf-8"

# Klasse, die das externe Mapping verwaltet


class ResolverAPI:
    def __init__(self, object_store: model.AbstractObjectStore,
                 base_path: str = "/api/v3.0"):
        self.object_store: model.AbstractObjectStore = object_store
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

    def _get_obj_ts(self, identifier: model.Identifier, type_: Type[
        model.provider._IT]) -> model.provider._IT:
        identifiable = self.object_store.get(identifier)
        if not isinstance(identifiable, type_):
            raise NotFound(
                f"No {type_.__name__} with {identifier} found!")
        identifiable.update()
        return identifiable

    def _get_all_obj_of_type(self, type_: Type[model.provider._IT]) -> \
            Iterator[model.provider._IT]:
        for obj in self.object_store:
            if isinstance(obj, type_):
                obj.update()
                yield obj

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

    def _get_assets(self, request: Request) -> Tuple[
        Iterator[model.SpecificAssetId], int]:
        specific_asset_ids: Iterator[
            model.SpecificAssetId] = self._get_all_obj_of_type(
            model.SpecificAssetId)

        asset_name = request.args.get("name")
        if asset_name is not None:
            specific_asset_ids = filter(
                lambda asset: asset.name == asset_name,
                specific_asset_ids)

        paginated_assets, end_index = self._get_slice(request,
                                                      specific_asset_ids)
        return paginated_assets, end_index

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
                                                      True)

        matching_aas_ids = []
        for asset_link in asset_links:
            if asset_link.name == "globalAssetId":
                for aas in self._get_all_obj_of_type(
                            model.AssetAdministrationShell):
                    if aas.asset_information.global_asset_id == asset_link.value:
                            matching_aas_ids.append(aas.id_)
            else:
                for aas in self._get_all_obj_of_type(
                            model.AssetAdministrationShell):
                    for specific_asset_id in aas.asset_information.specific_asset_id:
                        if specific_asset_id.name == asset_link.name and specific_asset_id.value == asset_link.value:
                            matching_aas_ids.append(aas.id)

        paginated_ids, end_index = self._get_slice(request, iter(
                matching_aas_ids))
        return response_t(matching_aas_ids, cursor=end_index)

    def get_all_asset_links_by_id(self, request: Request,
                                  url_args: Dict,
                                  response_t: Type[APIResponse],
                                  **_kwargs) -> Response:
        """
        Returns a list of specific asset identifiers based on an Asset Administration Shell ID to edit discoverable content.
        The global asset ID is returned as specific asset ID with "name" equal to "globalAssetId" (see Constraint AASd-116).
        """
        aas_identifier = url_args.get("aas_id")
        try:
            aas = self._get_obj_ts(aas_identifier,
                                   model.AssetAdministrationShell)
        except NotFound:
            raise NotFound(
                f"Asset Administration Shell with ID '{aas_identifier}' not found.")

        specific_asset_ids = list(aas.asset_information.specific_asset_id)

        if aas.asset_information.global_asset_id:
            specific_asset_ids.append(model.SpecificAssetId(
                name="globalAssetId",
                value=aas.asset_information.global_asset_id
            ))
        
        return response_t(specific_asset_ids)

    def post_all_asset_links_by_id(self, request: Request,
                                   url_args: Dict,
                                   response_t: Type[APIResponse],
                                   **_kwargs) -> Response:
        """
        Creates specific asset identifiers linked to an Asset Administration Shell to edit discoverable content.
        """
        aas_identifier = url_args.get("aas_id")

        # Try to retrieve the Asset Administration Shell by its identifier
        try:
            aas = self._get_obj_ts(aas_identifier,
                                   model.AssetAdministrationShell)
        except NotFound:
            raise NotFound(
                f"Asset Administration Shell with ID '{aas_identifier}' not found.")

        # Decode the request body to retrieve specific asset identifiers
        specific_asset_ids = HTTPApiDecoder.request_body_list(
                request, model.SpecificAssetId, False)

        # Check for conflicts with existing specific asset identifiers
        existing_ids = {id.value for id in
                        aas.asset_information.specific_asset_id}
        for specific_asset_id in specific_asset_ids:
            if specific_asset_id.value in existing_ids:
                raise Conflict(
                    f"Specific asset identifier with value '{specific_asset_id.value}' already exists.")
            else:
                aas.asset_information.specific_asset_id.add(specific_asset_id)

        return response_t(specific_asset_ids)

    def delete_all_asset_links_by_id(self, request: Request,
                                     url_args: Dict,
                                     response_t: Type[APIResponse],
                                     **_kwargs) -> Response:
        """
        Deletes all specific asset identifiers linked to an Asset Administration Shell to edit discoverable content.
        """
        aas_identifier = url_args.get("aas_id")

        # Try to retrieve the Asset Administration Shell by its identifier
        try:
            aas = self._get_obj_ts(aas_identifier,
                                   model.AssetAdministrationShell)
        except NotFound:
            raise NotFound(
                f"Asset Administration Shell with ID '{aas_identifier}' not found.")

        # Clear all specific asset identifiers from the AAS
        aas.asset_information.specific_asset_id.clear()

        # Return 204 No Content response
        return Response(status=204)


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8084, ResolverAPI(create_full_example()),
               use_debugger=True, use_reloader=True)
