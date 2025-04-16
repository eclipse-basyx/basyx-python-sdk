# Copyright (c) 2024 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements the "Specification of the Asset Administration Shell Part 2 Application Programming Interfaces".
"""

import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import Conflict, NotFound
from werkzeug.routing import MapAdapter, Rule, Submount
from werkzeug.wrappers import Request, Response

from basyx.aas import model
import server.app.server_model as server_model
from server.app.interfaces.base import ObjectStoreWSGIApp

from ..http_api_helpers import HTTPApiDecoder, Base64URLConverter, is_stripped_request
from server.app.response import APIResponse

from typing import Dict, Iterator, List, Type, Tuple


class RegistryAPI(ObjectStoreWSGIApp):
    def __init__(self, object_store: model.AbstractObjectStore, base_path: str = "/api/v3.0"):
        self.object_store: model.AbstractObjectStore = object_store
        self.url_map = werkzeug.routing.Map([
            Submount(base_path, [
                Rule("/shell-descriptors", methods=["GET"], endpoint=self.get_aas_descriptors_all),
                Rule("/shell-descriptors", methods=["POST"], endpoint=self.post_aas_descriptor),
                Submount("/shell-descriptors", [
                    Rule("/<base64url:aas_id>", methods=["GET"], endpoint=self.get_aas_descriptor),
                    Rule("/<base64url:aas_id>", methods=["PUT"], endpoint=self.put_aas_descriptor),
                    Rule("/<base64url:aas_id>", methods=["DELETE"], endpoint=self.delete_aas_descriptor),
                    Submount("/<base64url:aas_id>", [
                        Rule("/submodel-descriptors", methods=["GET"], endpoint=self.get_all_submodel_descriptors_through_superpath),
                        Rule("/submodel-descriptors", methods=["POST"], endpoint=self.post_submodel_descriptor_through_superpath),
                        Submount("/submodel-descriptors", [
                            Rule("/<base64url:submodel_id>", methods=["GET"], endpoint=self.get_submodel_descriptor_by_id_through_superpath),
                            Rule("/<base64url:submodel_id>", methods=["PUT"], endpoint=self.put_submodel_descriptor_by_id_through_superpath),
                            Rule("/<base64url:submodel_id>", methods=["DELETE"], endpoint=self.delete_submodel_descriptor_by_id_through_superpath),
                        ])
                    ])
                ]),
                Rule("/submodel-descriptors", methods=["GET"], endpoint=self.get_all_submodel_descriptors),
                Rule("/submodel-descriptors", methods=["POST"], endpoint=self.post_submodel_descriptor),
                Submount("/submodel-descriptors", [
                    Rule("/<base64url:submodel_id>", methods=["GET"], endpoint=self.get_submodel_descriptor_by_id),
                    Rule("/<base64url:submodel_id>", methods=["PUT"], endpoint=self.put_submodel_descriptor_by_id),
                    Rule("/<base64url:submodel_id>", methods=["DELETE"], endpoint=self.delete_submodel_descriptor_by_id),
                ])
            ])
        ], converters={
            "base64url": Base64URLConverter
        }, strict_slashes=False)

    def _get_descriptors(self, request: "Request") -> Tuple[Iterator[server_model.AssetAdministrationShellDescriptor], int]:
        """
        Returns all Asset Administration Shell Descriptors
        """
        descriptors: Iterator[server_model.AssetAdministrationShellDescriptor] = self._get_all_obj_of_type(
            server_model.AssetAdministrationShellDescriptor
        )

        id_short = request.args.get("idShort")
        if id_short is not None:
            descriptors = filter(lambda desc: desc.id_short == id_short, descriptors)

        asset_ids = request.args.getlist("assetIds")
        if asset_ids:
            # Decode und Instanziierung der SpecificAssetIds
            specific_asset_ids: List[model.SpecificAssetId] = list(
                map(lambda asset_id: HTTPApiDecoder.base64urljson(asset_id, model.SpecificAssetId, False), asset_ids)
            )
            # Filtere anhand der übergebenen SpecificAssetIds
            descriptors = filter(
                lambda desc: all(specific_asset_id in desc.asset_information.specific_asset_id
                                 for specific_asset_id in specific_asset_ids),
                descriptors
            )

        paginated_descriptors, end_index = self._get_slice(request, descriptors)
        return paginated_descriptors, end_index

    def _get_descriptor(self, url_args: Dict) -> server_model.AssetAdministrationShellDescriptor:
        return self._get_obj_ts(url_args["aas_id"], server_model.AssetAdministrationShellDescriptor)

    def _get_submodel_descriptors(self, request: Request) -> Tuple[Iterator[server_model.SubmodelDescriptor], int]:
        submodel_descriptors: Iterator[model.Submodel] = self._get_all_obj_of_type(server_model.SubmodelDescriptor)
        id_short = request.args.get("idShort")
        if id_short is not None:
            submodel_descriptors = filter(lambda sm: sm.id_short == id_short, submodel_descriptors)
        semantic_id = request.args.get("semanticId")
        if semantic_id is not None:
            spec_semantic_id = HTTPApiDecoder.base64urljson(
                semantic_id, model.Reference, False)  # type: ignore[type-abstract]
            submodel_descriptors = filter(lambda sm: sm.semantic_id == spec_semantic_id, submodel_descriptors)
        paginated_submodel_descriptors, end_index = self._get_slice(request, submodel_descriptors)
        return paginated_submodel_descriptors, end_index

    def _get_submodel_descriptor(self, url_args: Dict) -> server_model.SubmodelDescriptor:
        return self._get_obj_ts(url_args["submodel_id"], server_model.SubmodelDescriptor)

    # ------ AAS REGISTRY ROUTES -------
    def get_aas_descriptors_all(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aas_descriptors, cursor = self._get_descriptors(request)
        return response_t(list(aas_descriptors), cursor=cursor)

    def post_aas_descriptor(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                 map_adapter: MapAdapter) -> Response:
        descriptor = HTTPApiDecoder.request_body(request, server_model.AssetAdministrationShellDescriptor, False)
        try:
            self.object_store.add(descriptor)
        except KeyError as e:
            raise Conflict(f"AssetAdministrationShellDescriptor with Identifier {descriptor.id} already exists!") from e
        descriptor.commit()
        created_resource_url = map_adapter.build(self.get_aas_descriptor, {
            "aas_id": descriptor.id
        }, force_external=True)
        return response_t(descriptor, status=201, headers={"Location": created_resource_url})

    def get_aas_descriptor(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        descriptor = self._get_descriptor(url_args)
        return response_t(descriptor)

    def put_aas_descriptor(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        descriptor = self._get_descriptor(url_args)
        descriptor.update_from(HTTPApiDecoder.request_body(request, server_model.AssetAdministrationShellDescriptor,
                                                    is_stripped_request(request)))
        descriptor.commit()
        return response_t()

    def delete_aas_descriptor(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        descriptor = self._get_descriptor(url_args)
        self.object_store.remove(descriptor)
        return response_t()

    def get_all_submodel_descriptors_through_superpath(self,
                                                       request: Request,
                                                       url_args: Dict,
                                                       response_t: Type[
                                                           APIResponse],
                                                       **_kwargs) -> Response:
        aas_descriptor = self._get_descriptor(url_args)
        submodel_descriptors, cursor = self._get_slice(request,
                                                       aas_descriptor.submodel_descriptors)
        return response_t(list(submodel_descriptors), cursor=cursor)

    def get_submodel_descriptor_by_id_through_superpath(self,
                                                        request: Request,
                                                        url_args: Dict,
                                                        response_t:
                                                        Type[
                                                            APIResponse],
                                                        **_kwargs) -> Response:
        aas_descriptor = self._get_descriptor(url_args)
        submodel_id = url_args["submodel_id"]
        submodel_descriptor = next(
            (sd for sd in aas_descriptor.submodel_descriptors if
             sd.id == submodel_id), None)
        if submodel_descriptor is None:
            raise NotFound(
                f"Submodel Descriptor with Identifier {submodel_id} not found in AssetAdministrationShell!")
        return response_t(submodel_descriptor)

    def post_submodel_descriptor_through_superpath(self,
                                                   request: Request,
                                                   url_args: Dict,
                                                   response_t: Type[
                                                       APIResponse],
                                                   map_adapter: MapAdapter) -> Response:
        aas_descriptor = self._get_descriptor(url_args)
        submodel_descriptor = HTTPApiDecoder.request_body(request,
                                                          server_model.SubmodelDescriptor,
                                                          is_stripped_request(
                                                              request))
        if any(sd.id == submodel_descriptor.id for sd in
               aas_descriptor.submodel_descriptors):
            raise Conflict(
                f"Submodel Descriptor with Identifier {submodel_descriptor.id} already exists!")
        aas_descriptor.submodel_descriptors.append(submodel_descriptor)
        aas_descriptor.commit()
        created_resource_url = map_adapter.build(
            self.get_submodel_descriptor_by_id_through_superpath, {
                "aas_id": aas_descriptor.id,
                "submodel_id": submodel_descriptor.id
            }, force_external=True)
        return response_t(submodel_descriptor, status=201,
                          headers={"Location": created_resource_url})

    def put_submodel_descriptor_by_id_through_superpath(self,
                                                        request: Request,
                                                        url_args: Dict,
                                                        response_t:
                                                        Type[
                                                            APIResponse],
                                                        **_kwargs) -> Response:
        aas_descriptor = self._get_descriptor(url_args)
        submodel_id = url_args["submodel_id"]
        submodel_descriptor = next(
            (sd for sd in aas_descriptor.submodel_descriptors if
             sd.id == submodel_id), None)
        if submodel_descriptor is None:
            raise NotFound(
                f"Submodel Descriptor with Identifier {submodel_id} not found in AssetAdministrationShell!")
        submodel_descriptor.update_from(
            HTTPApiDecoder.request_body(request,
                                        server_model.SubmodelDescriptor,
                                        is_stripped_request(request)))
        aas_descriptor.commit()
        return response_t()

    def delete_submodel_descriptor_by_id_through_superpath(self,
                                                           request: Request,
                                                           url_args: Dict,
                                                           response_t:
                                                           Type[
                                                               APIResponse],
                                                           **_kwargs) -> Response:
        aas_descriptor = self._get_descriptor(url_args)
        submodel_id = url_args["submodel_id"]
        submodel_descriptor = next(
            (sd for sd in aas_descriptor.submodel_descriptors if sd.id == submodel_id), None)
        if submodel_descriptor is None:
            raise NotFound(f"Submodel Descriptor with Identifier {submodel_id} not found in AssetAdministrationShell!")
        aas_descriptor.submodel_descriptors.remove(submodel_descriptor)
        aas_descriptor.commit()
        return response_t()

    # ------ Submodel REGISTRY ROUTES -------
    def get_all_submodel_descriptors(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel_descriptors, cursor = self._get_submodel_descriptors(request)
        return response_t(list(submodel_descriptors), cursor=cursor, stripped=is_stripped_request(request))


    def get_submodel_descriptor_by_id(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel_descriptor = self._get_submodel_descriptor(url_args)
        return response_t(submodel_descriptor, stripped=is_stripped_request(request))


    def post_submodel_descriptor(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                 map_adapter: MapAdapter) -> Response:
        submodel_descriptor = HTTPApiDecoder.request_body(request, server_model.SubmodelDescriptor, is_stripped_request(request))
        try:
            self.object_store.add(submodel_descriptor)
        except KeyError as e:
            raise Conflict(f"Submodel Descriptor with Identifier {submodel_descriptor.id} already exists!") from e
        submodel_descriptor.commit()
        created_resource_url = map_adapter.build(self.get_submodel_descriptor_by_id, {
            "submodel_id": submodel_descriptor.id
        }, force_external=True)
        return response_t(submodel_descriptor, status=201, headers={"Location": created_resource_url})


    def put_submodel_descriptor_by_id(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel_descriptor = self._get_submodel_descriptor(url_args)
        submodel_descriptor.update_from(HTTPApiDecoder.request_body(request, server_model.SubmodelDescriptor, is_stripped_request(request)))
        submodel_descriptor.commit()
        return response_t()

    def delete_submodel_descriptor_by_id(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        self.object_store.remove(self._get_obj_ts(url_args["submodel_id"], server_model.SubmodelDescriptor))
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8083, RegistryAPI(create_full_example()),
               use_debugger=True, use_reloader=True)
