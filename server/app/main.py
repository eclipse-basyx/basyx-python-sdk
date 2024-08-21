import os
import pathlib
import sys

from basyx.aas import model
from basyx.aas.adapter import aasx

from basyx.aas.backend.local_file import LocalFileObjectStore
from basyx.aas.adapter.http import WSGIApp

storage_path = os.getenv("STORAGE_PATH", "/storage")
storage_type = os.getenv("STORAGE_TYPE", "AASX")
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path

if storage_type == "LOCAL_FILE":
    application = WSGIApp(LocalFileObjectStore(storage_path), aasx.DictSupplementaryFileContainer(), **wsgi_optparams)

elif storage_type == "AASX":
    object_store: model.DictObjectStore = model.DictObjectStore()
    file_store: aasx.DictSupplementaryFileContainer = aasx.DictSupplementaryFileContainer()

    for file in pathlib.Path(storage_path).glob("*.aasx"):
        if not file.is_file():
            continue
        print(f"Loading {file}")
        with aasx.AASXReader(file) as reader:
            reader.read_into(object_store=object_store, file_store=file_store)

    application = WSGIApp(object_store, file_store, **wsgi_optparams)

else:
    print(f"STORAGE_TYPE must be either LOCAL_FILE or AASX! Current value: {storage_type}", file=sys.stderr)
