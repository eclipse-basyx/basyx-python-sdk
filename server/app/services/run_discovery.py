import atexit
import os

from app.interfaces.discovery import DiscoveryAPI, DiscoveryStore

storage_path = os.getenv("storage_path", None)
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path


def load_discovery_store(path: str) -> DiscoveryStore:
    storage_dir = os.path.dirname(path)
    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)

    if os.path.exists(path) and os.path.getsize(path) > 0:
        return DiscoveryStore.from_file(path)

    discovery_store = DiscoveryStore()
    discovery_store.to_file(path)
    return discovery_store


# Load DiscoveryStore from disk, if `storage_path` is set
if storage_path:
    discovery_store: DiscoveryStore = load_discovery_store(storage_path)
else:
    discovery_store = DiscoveryStore()


def persist_store():
    if storage_path:
        storage_dir = os.path.dirname(storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        discovery_store.to_file(storage_path)


atexit.register(persist_store)

application = DiscoveryAPI(discovery_store, **wsgi_optparams)
