import werkzeug.exceptions
from werkzeug.wrappers import Request, Response

from basyx.aas import model
from server.app.interfaces.base import BaseWSGIApp

from .. import server_model
from ..adapter.jsonization import ServerAASToJsonEncoder

from werkzeug.routing import Rule, Submount
from ..http_api_helpers import Base64URLConverter, HTTPApiDecoder
from typing import Dict, List, Set

import abc

from pymongo import MongoClient
from pymongo.collection import Collection

import json

def specific_asset_to_json_obj(asset_id: model.SpecificAssetId) -> dict:
    # Encode the asset to a JSON string and then decode to a dict.
    json_str = ServerAASToJsonEncoder().encode(asset_id)
    return json.loads(json_str)

class AbstractDiscoveryStore(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        pass

class InMemoryDiscoveryStore(AbstractDiscoveryStore):
    def __init__(self):
        self.aas_to_assets: Dict[model.Identifier, Set[model.SpecificAssetId]] = {}
        self.asset_to_aas: Dict[model.SpecificAssetId, Set[model.Identifier]] = {}

    def get_asset_links_by_aas(self, aas_identifier: model.Identifier) -> List[dict]:
        key = aas_identifier
        return list(self.aas_to_assets.get(key, set()))

    def add_asset_links(self, aas_identifier: model.Identifier, asset_ids: List[model.SpecificAssetId]) -> None:
        key = aas_identifier
        serialized_assets = [specific_asset_to_json_obj(aid) for aid in asset_ids]
        if key in self.aas_to_assets:
            for asset in serialized_assets:
                if asset not in self.aas_to_assets[key]:
                    self.aas_to_assets[key].append(asset)
        else:
            self.aas_to_assets[key] = serialized_assets[:]

    def delete_asset_links_by_aas(self, aas_identifier: model.Identifier) -> None:
        key = aas_identifier
        if key in self.aas_to_assets:
            del self.aas_to_assets[key]

    def search_aas_by_asset_link(self, asset_link: server_model.AssetLink) -> List[str]:
        result = []
        for asset_key, aas_ids in self.asset_to_aas.items():
            expected_key = f"{asset_link.name}:{asset_link.value}"
            if asset_key == expected_key:
                result.extend(list(aas_ids))
        return result

    def add_aas_for_asset_link(self, asset_id: model.SpecificAssetId, aas_identifier: model.Identifier) -> None:
        asset_key = f"{asset_id.name}:{asset_id.value}"
        aas_key = aas_identifier
        if asset_key in self.asset_to_aas:
            self.asset_to_aas[asset_key].add(aas_key)
        else:
            self.asset_to_aas[asset_key] = {aas_key}

    def remove_aas_from_asset_link(self, asset_id: model.SpecificAssetId, aas_identifier: model.Identifier) -> None:
        asset_key = f"{asset_id.name}:{asset_id.value}"
        aas_key = aas_identifier
        if asset_key in self.asset_to_aas:
            self.asset_to_aas[asset_key].discard(aas_key)

class MongoDiscoveryStore(AbstractDiscoveryStore):
    def __init__(self,
                 uri: str = "mongodb://localhost:27017",
                 db_name: str = "basyx",
                 coll_aas_to_assets: str = "aas_to_assets",
                 coll_asset_to_aas: str = "asset_to_aas"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.coll_aas_to_assets: Collection = self.db[coll_aas_to_assets]
        self.coll_asset_to_aas: Collection = self.db[coll_asset_to_aas]
        # Create an index for fast asset reverse lookups.
        self.coll_asset_to_aas.create_index("_id")

    def get_asset_links_by_aas(self, aas_identifier: model.Identifier) -> List[dict]:
        key = aas_identifier
        doc = self.coll_aas_to_assets.find_one({"_id": key})
        return doc["asset_ids"] if doc and "asset_ids" in doc else []

    def add_asset_links(self, aas_identifier: model.Identifier, asset_ids: List[model.SpecificAssetId]) -> None:
        key = aas_identifier
        # Convert each SpecificAssetId using the serialization helper.
        serializable_assets = [specific_asset_to_json_obj(aid) for aid in asset_ids]
        self.coll_aas_to_assets.update_one(
            {"_id": key},
            {"$addToSet": {"asset_ids": {"$each": serializable_assets}}},
            upsert=True
        )

    def delete_asset_links_by_aas(self, aas_identifier: model.Identifier) -> None:
        key = aas_identifier
        self.coll_aas_to_assets.delete_one({"_id": key})

    def search_aas_by_asset_link(self, asset_link: server_model.AssetLink) -> List[str]:
        # Query MongoDB for specificAssetIds where 'name' and 'value' match
        doc = self.coll_asset_to_aas.find_one({
            "name": asset_link.name,
            "value": asset_link.value
        })
        return doc["aas_ids"] if doc and "aas_ids" in doc else []

    def add_aas_for_asset_link(self, asset_id: model.SpecificAssetId, aas_identifier: model.Identifier) -> None:
        asset_key = str(specific_asset_to_json_obj(asset_id))
        aas_key = aas_identifier
        self.coll_asset_to_aas.update_one(
            {"_id": asset_key},
            {"$addToSet": {"aas_ids": aas_key}},
            upsert=True
        )

    def remove_aas_from_asset_link(self, asset_id: model.SpecificAssetId, aas_identifier: model.Identifier) -> None:
        asset_key = str(specific_asset_to_json_obj(asset_id))
        aas_key = aas_identifier
        self.coll_asset_to_aas.update_one(
            {"_id": asset_key},
            {"$pull": {"aas_ids": aas_key}}
        )


class DiscoveryAPI(BaseWSGIApp):
    def __init__(self,
                 persistent_store: AbstractDiscoveryStore, base_path: str = "/api/v3.0"):
        self.persistent_store: AbstractDiscoveryStore = persistent_store
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

    def search_all_aas_ids_by_asset_link(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        asset_links = HTTPApiDecoder.request_body_list(request, server_model.AssetLink, False)
        matching_aas_keys = set()
        for asset_link in asset_links:
            aas_keys = self.persistent_store.search_aas_by_asset_link(asset_link)
            matching_aas_keys.update(aas_keys)
        matching_aas_keys = list(matching_aas_keys)
        paginated_slice, cursor = self._get_slice(request, matching_aas_keys)
        return response_t(list(paginated_slice), cursor=cursor)

    def get_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        asset_ids = self.persistent_store.get_asset_links_by_aas(aas_identifier)
        return response_t(asset_ids)

    def post_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        specific_asset_ids = HTTPApiDecoder.request_body_list(request, model.SpecificAssetId, False)
        self.persistent_store.add_asset_links(aas_identifier, specific_asset_ids)
        for asset_id in specific_asset_ids:
            self.persistent_store.add_aas_for_asset_link(asset_id, aas_identifier)
        updated = {aas_identifier: self.persistent_store.get_asset_links_by_aas(aas_identifier)}
        return response_t(updated)

    def delete_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        self.persistent_store.delete_asset_links_by_aas(aas_identifier)
        for key in list(self.persistent_store.asset_to_aas.keys()):
            self.persistent_store.asset_to_aas[key].discard(aas_identifier)
        return response_t()

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("localhost", 8084, DiscoveryAPI(InMemoryDiscoveryStore()),
               use_debugger=True, use_reloader=True)
