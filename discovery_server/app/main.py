import os
import sys
from server.app.interfaces.discovery import DiscoveryAPI, MongoDiscoveryStore,InMemoryDiscoveryStore

storage_type = os.getenv("STORAGE_TYPE", "inmemory")
base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {}

if base_path is not None:
    wsgi_optparams["base_path"] = base_path

if storage_type == "inmemory":
    application = DiscoveryAPI(InMemoryDiscoveryStore(), **wsgi_optparams)

elif storage_type == "mongodb":
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    dbname = os.getenv("MONGODB_DBNAME", "basyx_registry")

    application = DiscoveryAPI(MongoDiscoveryStore(uri,dbname), **wsgi_optparams)

else:
    print(f"STORAGE_TYPE must be either inmemory or mongodb! Current value: {storage_type}",
          file=sys.stderr)

