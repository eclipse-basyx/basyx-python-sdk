import atexit
import os

from app.interfaces.discovery import DiscoveryAPI, DiscoveryStore

storage_path = os.getenv("storage_path", None)
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path


# Load DiscoveryStore from disk, if `storage_path` is set
if storage_path:
    discovery_store: DiscoveryStore = DiscoveryStore.from_file(storage_path)
else:
    discovery_store = DiscoveryStore()


def persist_store():
    if storage_path:
        discovery_store.to_file(storage_path)


atexit.register(persist_store)

application = DiscoveryAPI(discovery_store, **wsgi_optparams)
