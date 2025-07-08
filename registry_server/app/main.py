import sys
import os
sys.path.insert(0, "/")
from basyx.aas.backend.local_file import LocalFileObjectStore
from basyx.aas import model
from server.app.interfaces.registry import RegistryAPI

storage_path = os.getenv("STORAGE_PATH", "/storage")
storage_type = os.getenv("STORAGE_TYPE", "LOCAL_FILE_READ_ONLY")
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path

if storage_type == "LOCAL_FILE_BACKEND":
    application = RegistryAPI(LocalFileObjectStore(storage_path), **wsgi_optparams)

elif storage_type in "LOCAL_FILE_READ_ONLY":
    object_store: model.DictObjectStore = model.DictObjectStore()

    application = RegistryAPI(object_store, **wsgi_optparams)

else:
    print(f"STORAGE_TYPE must be either LOCAL_FILE or LOCAL_FILE_READ_ONLY! Current value: {storage_type}",
          file=sys.stderr)