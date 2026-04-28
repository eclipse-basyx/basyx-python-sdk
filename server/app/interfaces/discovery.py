"""
This module implements the Discovery interface defined in the
'Specification of the Asset Administration Shell Part 2
– Application Programming Interface'.
"""

import json
from typing import Dict, List, Set

import werkzeug.exceptions
from basyx.aas import model
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request, Response

from app import model as server_model
from app.adapter import jsonization
from app.interfaces.base import BaseWSGIApp, HTTPApiDecoder
from app.util.converters import IdentifierToBase64URLConverter


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
        Load the state of the `DiscoveryStore` from a local file.
        Safely handles files that are missing expected keys.

        """
        with open(filename, "r") as file:
            data = json.load(file, cls=jsonization.ServerAASFromJsonDecoder)
            discovery_store = DiscoveryStore()
            discovery_store.aas_id_to_asset_ids = data.get("aas_id_to_asset_ids", {})
            discovery_store.asset_id_to_aas_ids = data.get("asset_id_to_aas_ids", {})
            return discovery_store

    def to_file(self, filename: str) -> None:
        """
        Write the current state of the `DiscoveryStore` to a local JSON file for persistence.
        """
        with open(filename, "w") as file:
            data = {
                "aas_id_to_asset_ids": self.aas_id_to_asset_ids,
                "asset_id_to_aas_ids": self.asset_id_to_aas_ids,
            }
            json.dump(data, file, cls=jsonization.ServerAASToJsonEncoder, indent=4)


class DiscoveryAPI(BaseWSGIApp):
    def __init__(self, persistent_store: DiscoveryStore, base_path: str = "/api/v3.1.1"):
        self.persistent_store: DiscoveryStore = persistent_store
        self.url_map = werkzeug.routing.Map(
            [
                Submount(
                    base_path,
                    [
                        Rule(
                            "/lookup/shellsByAssetLink",
                            methods=["POST"],
                            endpoint=self.search_all_aas_ids_by_asset_link,
                        ),
                        Submount(
                            "/lookup/shells",
                            [
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

    def search_all_aas_ids_by_asset_link(
        self, request: Request, url_args: dict, response_t: type, **_kwargs
    ) -> Response:
        asset_links = HTTPApiDecoder.request_body_list(request, server_model.AssetLink, False)
        matching_aas_keys = set()
        for asset_link in asset_links:
            aas_keys = self.persistent_store.search_aas_ids_by_asset_link(asset_link)
            matching_aas_keys.update(aas_keys)
        paginated_slice, cursor = self._get_slice(request, list(matching_aas_keys))
        return response_t(list(paginated_slice), cursor=cursor)

    def get_all_specific_asset_ids_by_aas_id(
        self, request: Request, url_args: dict, response_t: type, **_kwargs
    ) -> Response:
        aas_identifier = str(url_args["aas_id"])
        asset_ids = self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)
        return response_t(asset_ids)

    def post_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = str(url_args["aas_id"])
        specific_asset_ids = HTTPApiDecoder.request_body_list(request, model.SpecificAssetId, False)
        self.persistent_store.add_specific_asset_ids_to_aas(aas_identifier, specific_asset_ids)
        for asset_id in specific_asset_ids:
            self.persistent_store._add_aas_id_to_specific_asset_id(asset_id, aas_identifier)
        updated = {aas_identifier: self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)}
        return response_t(updated)

    def delete_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = str(url_args["aas_id"])
        self.persistent_store.delete_specific_asset_ids_by_aas_id(aas_identifier)
        for key in list(self.persistent_store.asset_id_to_aas_ids.keys()):
            self.persistent_store.asset_id_to_aas_ids[key].discard(aas_identifier)
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    run_simple("localhost", 8084, DiscoveryAPI(DiscoveryStore()), use_debugger=True, use_reloader=True)
