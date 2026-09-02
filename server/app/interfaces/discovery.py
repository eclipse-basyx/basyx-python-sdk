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

        if aas_id not in self.aas_id_to_asset_ids:
            self.aas_id_to_asset_ids[aas_id] = set()

        for asset in asset_ids:
            self.aas_id_to_asset_ids[aas_id].add(asset)

    def delete_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> None:
        key = aas_id
        if key in self.aas_id_to_asset_ids:
            del self.aas_id_to_asset_ids[key]

    def search_aas_ids_by_asset_link(self, asset_link: server_model.AssetLink) -> List[model.Identifier]:
        result = []
        for asset_key, aas_ids in self.asset_id_to_aas_ids.items():
            if asset_key.name == asset_link.name and asset_key.value == asset_link.value:
                result.extend(list(aas_ids))
        return result

    def _add_aas_id_to_specific_asset_id(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        if asset_id in self.asset_id_to_aas_ids:
            self.asset_id_to_aas_ids[asset_id].add(aas_id)
        else:
            self.asset_id_to_aas_ids[asset_id] = {aas_id}

    def _delete_aas_id_from_specific_asset_ids(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        if asset_id in self.asset_id_to_aas_ids:
            self.asset_id_to_aas_ids[asset_id].discard(aas_id)

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
            parsed_asset_ids = set()

            for asset_id in asset_ids:
                if isinstance(asset_id, model.SpecificAssetId):
                    parsed_asset_id = asset_id
                else:
                    parsed_asset_id = model.SpecificAssetId(
                        name=asset_id["name"],
                        value=asset_id["value"],
                    )

                parsed_asset_ids.add(parsed_asset_id)
                discovery_store._add_aas_id_to_specific_asset_id(parsed_asset_id, aas_id)

            discovery_store.aas_id_to_asset_ids[aas_id] = parsed_asset_ids

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
    def __init__(self, persistent_store: DiscoveryStore, base_path: str = "/api/v3.1"):
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
        self.persistent_store.add_specific_asset_ids_to_aas(aas_identifier, specific_asset_ids)
        for asset_id in specific_asset_ids:
            self.persistent_store._add_aas_id_to_specific_asset_id(asset_id, aas_identifier)
        updated = {aas_identifier: self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)}
        return response_t(updated)

    def delete_all_asset_links_by_id(
        self, request: Request, url_args: dict, response_t: Type[APIResponse], **_kwargs
    ) -> Response:
        aas_identifier = str(url_args["aas_id"])
        self.persistent_store.delete_specific_asset_ids_by_aas_id(aas_identifier)
        for key in list(self.persistent_store.asset_id_to_aas_ids.keys()):
            self.persistent_store.asset_id_to_aas_ids[key].discard(aas_identifier)
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    run_simple("localhost", 8084, DiscoveryAPI(DiscoveryStore()), use_debugger=True, use_reloader=True)
