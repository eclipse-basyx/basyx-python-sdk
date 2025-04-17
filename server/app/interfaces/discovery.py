import abc
import json
from typing import Dict, List, Set, Any

import werkzeug.exceptions
from pymongo import MongoClient
from pymongo.collection import Collection
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import Request, Response

from basyx.aas import model
from server.app.api_utils.http_api_helpers import Base64URLConverter, HTTPApiDecoder
from server.app.interfaces.base import BaseWSGIApp
from .. import server_model
from ..adapter.jsonization import ServerAASToJsonEncoder

class AbstractDiscoveryStore(metaclass=abc.ABCMeta):
    aas_id_to_asset_ids: Any
    asset_id_to_aas_ids: Any

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_all_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> List[model.SpecificAssetId]:
        pass
    
    @abc.abstractmethod
    def add_specific_asset_ids_to_aas(self, aas_id: model.Identifier, asset_ids: List[model.SpecificAssetId]) -> None:
        pass
    
    @abc.abstractmethod
    def delete_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> None:
        pass
    
    @abc.abstractmethod
    def search_aas_ids_by_asset_link(self, asset_link: server_model.AssetLink) -> List[model.Identifier]:
        pass
    
    @abc.abstractmethod
    def _add_aas_id_to_specific_asset_id(self, asset_id: model.SpecificAssetId, aas_identifier: model.Identifier) -> None:
        pass

    @abc.abstractmethod
    def remove_aas_from_asset_link(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        pass



class InMemoryDiscoveryStore(AbstractDiscoveryStore):
    def __init__(self):
        self.aas_id_to_asset_ids: Dict[model.Identifier, Set[model.SpecificAssetId]] = {}
        self.asset_id_to_aas_ids: Dict[model.SpecificAssetId, Set[model.Identifier]] = {}

    def get_all_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> List[model.SpecificAssetId]:
        return list(self.aas_id_to_asset_ids.get(aas_id, set()))

    def add_specific_asset_ids_to_aas(self, aas_id: model.Identifier,
                                      asset_ids: List[model.SpecificAssetId]) -> None:
        serialized_assets = [ServerAASToJsonEncoder.default(asset_id) for asset_id in asset_ids]
        if aas_id in self.aas_id_to_asset_ids:
            for asset in serialized_assets:
                if asset not in self.aas_id_to_asset_ids[aas_id]:
                    self.aas_id_to_asset_ids[aas_id].append(asset)
        else:
            self.aas_id_to_asset_ids[aas_id] = serialized_assets[:]

    def delete_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> None:
        key = aas_id
        if key in self.aas_id_to_asset_ids:
            del self.aas_id_to_asset_ids[key]

    def search_aas_ids_by_asset_link(self, asset_link: server_model.AssetLink) -> List[model.Identifier]:
        result = []
        for asset_key, aas_ids in self.asset_id_to_aas_ids.items():
            expected_key = f"{asset_link.name}:{asset_link.value}"
            if asset_key == expected_key:
                result.extend(list(aas_ids))
        return result

    def _add_aas_id_to_specific_asset_id(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        asset_key = f"{asset_id.name}:{asset_id.value}"
        aas_key = aas_id
        # FIXME
        if asset_key in self.asset_id_to_aas_ids:
            self.asset_id_to_aas_ids[asset_key].add(aas_key)
        else:
            self.asset_id_to_aas_ids[asset_key] = {aas_key}

    def remove_aas_from_asset_link(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        asset_key = f"{asset_id.name}:{asset_id.value}"
        aas_key = aas_id
        if asset_key in self.asset_id_to_aas_ids:
            self.asset_id_to_aas_ids[asset_key].discard(aas_key)


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

    def get_all_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> List[model.SpecificAssetId]:
        key = aas_id
        doc = self.coll_aas_to_assets.find_one({"_id": key})
        return doc["asset_ids"] if doc and "asset_ids" in doc else []

    def add_specific_asset_ids_to_aas(self, aas_id: model.Identifier, asset_ids: List[model.SpecificAssetId]) -> None:
        key = aas_id
        # Convert each SpecificAssetId using the serialization helper.
        serializable_assets = [ServerAASToJsonEncoder.default(asset_id) for asset_id in asset_ids]
        self.coll_aas_to_assets.update_one(
            {"_id": key},
            {"$addToSet": {"asset_ids": {"$each": serializable_assets}}},
            upsert=True
        )

    def delete_specific_asset_ids_by_aas_id(self, aas_id: model.Identifier) -> None:
        key = aas_id
        self.coll_aas_to_assets.delete_one({"_id": key})

    def search_aas_ids_by_asset_link(self, asset_link: server_model.AssetLink) -> List[model.Identifier]:
        # Query MongoDB for specificAssetIds where 'name' and 'value' match
        doc = self.coll_asset_to_aas.find_one({
            "name": asset_link.name,
            "value": asset_link.value
        })
        return doc["aas_ids"] if doc and "aas_ids" in doc else []

    def _add_aas_id_to_specific_asset_id(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        asset_key = str(ServerAASToJsonEncoder.default(asset_id))
        self.coll_asset_to_aas.update_one(
            {"_id": asset_key},
            {"$addToSet": {"aas_ids": aas_id}},
            upsert=True
        )

    def remove_aas_from_asset_link(self, asset_id: model.SpecificAssetId, aas_id: model.Identifier) -> None:
        asset_key = str(ServerAASToJsonEncoder.default(asset_id))
        aas_key = aas_id
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
                         endpoint=self.get_all_specific_asset_ids_by_aas_id),
                    Rule("/<base64url:aas_id>", methods=["POST"],
                         endpoint=self.post_all_asset_links_by_id),
                    Rule("/<base64url:aas_id>", methods=["DELETE"],
                         endpoint=self.delete_all_asset_links_by_id),
                ]),
            ])
        ], converters={
            "base64url": Base64URLConverter
        }, strict_slashes=False)

    def search_all_aas_ids_by_asset_link(self, request: Request, url_args: dict, response_t: type,
                                         **_kwargs) -> Response:
        asset_links = HTTPApiDecoder.request_body_list(request, server_model.AssetLink, False)
        matching_aas_keys = set()
        for asset_link in asset_links:
            aas_keys = self.persistent_store.search_aas_ids_by_asset_link(asset_link)
            matching_aas_keys.update(aas_keys)
        matching_aas_keys = list(matching_aas_keys)
        paginated_slice, cursor = self._get_slice(request, matching_aas_keys)
        return response_t(list(paginated_slice), cursor=cursor)

    def get_all_specific_asset_ids_by_aas_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        asset_ids = self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)
        return response_t(asset_ids)

    def post_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        specific_asset_ids = HTTPApiDecoder.request_body_list(request, model.SpecificAssetId, False)
        self.persistent_store.add_specific_asset_ids_to_aas(aas_identifier, specific_asset_ids)
        for asset_id in specific_asset_ids:
            self.persistent_store._add_aas_id_to_specific_asset_id(asset_id, aas_identifier)
        updated = {aas_identifier: self.persistent_store.get_all_specific_asset_ids_by_aas_id(aas_identifier)}
        return response_t(updated)

    def delete_all_asset_links_by_id(self, request: Request, url_args: dict, response_t: type, **_kwargs) -> Response:
        aas_identifier = url_args.get("aas_id")
        self.persistent_store.delete_specific_asset_ids_by_aas_id(aas_identifier)
        for key in list(self.persistent_store.asset_id_to_aas_ids.keys()):
            self.persistent_store.asset_id_to_aas_ids[key].discard(aas_identifier)
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    run_simple("localhost", 8084, DiscoveryAPI(InMemoryDiscoveryStore()),
               use_debugger=True, use_reloader=True)
