import os
import pathlib
import sys

from basyx.aas import model, adapter
from basyx.aas.adapter import aasx

from basyx.aas.backend.local_file import LocalFileObjectStore
from basyx.aas.adapter.http import WSGIApp

storage_path = os.getenv("STORAGE_PATH", "storage")
storage_type = os.getenv("STORAGE_TYPE", "LOCAL_FILE_READ_ONLY")
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path

if storage_type == "LOCAL_FILE_BACKEND":
    application = WSGIApp(LocalFileObjectStore(storage_path), aasx.DictSupplementaryFileContainer(), **wsgi_optparams)

elif storage_type in "LOCAL_FILE_READ_ONLY":
    object_store: model.DictObjectStore = model.DictObjectStore()
    file_store: aasx.DictSupplementaryFileContainer = aasx.DictSupplementaryFileContainer()

    for file in pathlib.Path(storage_path).iterdir():
        if not file.is_file():
            continue
        print(f"Loading {file}")

        if file.suffix == ".json":
            with open(file) as f:
                adapter.json.read_aas_json_file_into(object_store, f)
        elif file.suffix == ".xml":
            with open(file) as f:
                adapter.xml.read_aas_xml_file_into(object_store, file)
        elif file.suffix == ".aasx":
            with aasx.AASXReader(file) as reader:
                reader.read_into(object_store=object_store, file_store=file_store)

    application = WSGIApp(object_store, file_store, **wsgi_optparams)

else:
    print(f"STORAGE_TYPE must be either LOCAL_FILE or LOCAL_FILE_READ_ONLY! Current value: {storage_type}",
          file=sys.stderr)
