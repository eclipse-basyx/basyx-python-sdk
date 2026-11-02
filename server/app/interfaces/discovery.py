# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

"""
This module implements the Discovery interface defined in the
'Specification of the Asset Administration Shell Part 2
– Application Programming Interface'.
"""

import json
import os
from typing import Dict, List, Set, Type

import werkzeug.exceptions
from basyx.aas import model
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request, Response

from app import model as server_model
from app._config import API_BASE_PATH
from app.adapter import jsonization
from app.interfaces.base import APIResponse, BaseWSGIApp, HTTPApiDecoder
from app.model import ServiceDescription, ServiceSpecificationProfileEnum
from app.util.converters import IdentifierToBase64URLConverter, base64url_decode

SUPPORTED_PROFILES: ServiceDescription = ServiceDescription(
    [
        ServiceSpecificationProfileEnum.DISCOVERY_FULL,
        ServiceSpecificationProfileEnum.DISCOVERY_READ,
    ]
)


class DiscoveryStore:
    def __init__(self) -> None:
        self.aas_id_to_asset_ids: Dict[model.Identifier, Set[model.SpecificAssetId]] = {}
        self.asset_id_to_aas_ids: Dict[model.SpecificAssetId, Set[model.Identifier]] = {}

    def get_all_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> List[model.SpecificAssetId]:
        return list(self.aas_id_to_asset_ids.get(aas_id, set()))

    def add_specific_asset_ids_to_aas(self, aas_id: model.Identifier, asset_ids: List[model.SpecificAssetId]) -> None:
        self.aas_id_to_asset_ids.setdefault(aas_id, set()).update(asset_ids)
        for asset_id in asset_ids:
            self.asset_id_to_aas_ids.setdefault(asset_id, set()).add(aas_id)

    def delete_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> None:
        for asset_id in self.aas_id_to_asset_ids.pop(aas_id, set()):
            aas_ids = self.asset_id_to_aas_ids.get(asset_id)
            if aas_ids is None:
                continue
            aas_ids.discard(aas_id)
            if not aas_ids:
                del self.asset_id_to_aas_ids[asset_id]

    def search_aas_ids_by_asset_link(self, asset_link: server_model.AssetLink) -> List[model.Identifier]:
        result = []
        for asset_key, aas_ids in self.asset_id_to_aas_ids.items():
            if asset_key.name == asset_link.name and asset_key.value == asset_link.value:
                result.extend(list(aas_ids))
        return result

    @classmethod
    def from_file(cls, filename: str) -> "DiscoveryStore":
        """
        Load a persisted discovery store from JSON.

        The file stores the AAS-to-asset-id mapping as the source of truth.
        While loading, the reverse asset-id-to-AAS index is rebuilt in memory so
        lookup by asset ID works without persisting duplicate state.
        """
        with open(filename, "r") as file:
            data = json.load(file, cls=jsonization.ServerAASFromJsonDecoder)

        discovery_store = DiscoveryStore()

        for aas_id, asset_ids in data.get("aas_id_to_asset_ids", {}).items():
            parsed_asset_ids = [
                asset_id
                if isinstance(asset_id, model.SpecificAssetId)
                else model.SpecificAssetId(name=asset_id["name"], value=asset_id["value"])
                for asset_id in asset_ids
            ]
            discovery_store.add_specific_asset_ids_to_aas(aas_id, parsed_asset_ids)

        return discovery_store

    def to_file(self, filename: str) -> None:
        """
        Persist the discovery store as JSON.

        Only the AAS-to-asset-id mapping is written because the reverse lookup
        index can be rebuilt when the store is loaded. The data is written to a
        temporary file first and then atomically moved into place to avoid
        corrupting the existing store if serialization fails.
        """
        data = {
            "aas_id_to_asset_ids": {aas_id: list(asset_ids) for aas_id, asset_ids in self.aas_id_to_asset_ids.items()}
        }

        temp_filename = f"{filename}.tmp"
        with open(temp_filename, "w") as file:
            json.dump(data, file, cls=jsonization.ServerAASToJsonEncoder, indent=4)

        os.replace(temp_filename, filename)


class DiscoveryAPI(BaseWSGIApp):
    def __init__(self, persistent_store: DiscoveryStore, base_path: str = API_BASE_PATH):
        self.persistent_store: DiscoveryStore = persistent_store
        self.url_map = werkzeug.routing.Map(
            [
                Submount(
                    base_path,
                    [
                        Rule("/description", methods=["GET"], endpoint=self.get_description),
                        Rule(
                            "/lookup/shellsByAssetLink",
                            methods=["POST"],
                            endpoint=self.search_all_aas_ids_by_asset_link,
                        ),
                        Submount(
                            "/lookup/shells",
                            [
                                # Todo: This route is deprecated in the specification, but needed for interoperability
                                #  with the BaSyx UI https://github.com/eclipse-basyx/basyx-aas-web-ui.
                                #  Once this route is no longer needed, we should consider removing it.
                                Rule("/", methods=["GET"], endpoint=self.get_all_aas_ids_by_asset_link),
                                Rule(
                                    "/<base64url:aas_id>",
                                    methods=["GET"],
                                    endpoint=self.get_all_specific_asset_ids_by_aas_id,
                                ),
                                Rule("/<base64url:aas_id>", methods=["POST"], endpoint=self.post_all_asset_links_by_id),
                                Rule(
                                    "/<base64url:aas_id>",
                                    methods=["DELETE"],
                                    endpoint=self.delete_all_asset_links_by_id,
                                ),
                            ],
                        ),
                    ],
                )
            ],
            converters={"base64url": IdentifierToBase64URLConverter},
            strict_slashes=False,
        )

    def get_description(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        return response_t(SUPPORTED_PROFILES.to_dict())

    def get_all_aas_ids_by_asset_link(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        asset_ids_param = request.args.get("assetIds", "")
        if not asset_ids_param:
            raise werkzeug.exceptions.BadRequest("Missing query parameter 'assetIds'")

        try:
            decoded_str = base64url_decode(asset_ids_param)
            payload = json.loads(decoded_str)
        except (ValueError, json.JSONDecodeError) as exc:
            raise werkzeug.exceptions.BadRequest(f"Invalid query parameter 'assetIds': {exc}") from exc

        if isinstance(payload, dict):
            payload = [payload]

        if not isinstance(payload, list):
            raise werkzeug.exceptions.BadRequest("Decoded assetIds payload must be a JSON object or list")

        matching_aas_keys = set()
        for item in payload:
            if not isinstance(item, dict):
                raise werkzeug.exceptions.BadRequest("Each asset link must be a JSON object")

            asset_link = server_model.AssetLink(item["name"], item["value"])
            aas_keys = self.persistent_store.search_aas_ids_by_asset_link(asset_link)
            matching_aas_keys.update(aas_keys)

        paginated_slice, paging_metadata = self._get_slice(request, list(matching_aas_keys))
        return response_t(list(paginated_slice), paging_metadata=paging_metadata)

    def search_all_aas_ids_by_asset_link(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        asset_links = HTTPApiDecoder.request_body_list(request, server_model.AssetLink, False)
        matching_aas_keys = set()
        for asset_link in asset_links:
            aas_keys = self.persistent_store.search_aas_ids_by_asset_link(asset_link)
            matching_aas_keys.update(aas_keys)
        paginated_slice, paging_metadata = self._get_slice(request, list(matching_aas_keys))
        return response_t(list(paginated_slice), paging_metadata=paging_metadata)

    def get_all_specific_asset_ids_by_aas_id(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        aas_identifier = str(url_args["aas_id"])
        asset_ids = self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)
        return response_t(asset_ids)

    def post_all_asset_links_by_id(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        aas_identifier = str(url_args["aas_id"])
        specific_asset_ids = HTTPApiDecoder.request_body_list(request, model.SpecificAssetId, False)
        self.persistent_store.delete_specific_asset_ids_by_aas_id(aas_identifier)
        self.persistent_store.add_specific_asset_ids_to_aas(aas_identifier, specific_asset_ids)
        updated = {aas_identifier: self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)}
        return response_t(updated, status=201)

    def delete_all_asset_links_by_id(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        aas_identifier = str(url_args["aas_id"])
        if aas_identifier not in self.persistent_store.aas_id_to_asset_ids:
            raise werkzeug.exceptions.NotFound(f"No AssetAdministrationShell with {aas_identifier} found!")
        self.persistent_store.delete_specific_asset_ids_by_aas_id(aas_identifier)
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    run_simple("localhost", 8084, DiscoveryAPI(DiscoveryStore()), use_debugger=True, use_reloader=True)
