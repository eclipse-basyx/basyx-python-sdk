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
    # If the storage file exists, we load it
    if os.path.exists(storage_path) and os.path.getsize(storage_path) > 0:
        discovery_store = DiscoveryStore.from_file(storage_path)

    # If the file doesn't exist at the given path, we initiate a new file
    else:
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        discovery_store = DiscoveryStore()
        discovery_store.to_file(storage_path)
else:
    discovery_store = DiscoveryStore()


def persist_store():
    if storage_path:
        discovery_store.to_file(storage_path)


atexit.register(persist_store)

application = DiscoveryAPI(discovery_store, **wsgi_optparams)
