import os
from basyx.aas.adapter.discovery import DiscoveryAPI, MongoDiscoveryStore,InMemoryDiscoveryStore

def get_discovery_store():
    storage_type = os.getenv("STORAGE_TYPE", "inmemory").lower()
    if storage_type == "mongodb":
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        dbname = os.getenv("MONGODB_DBNAME", "basyx_registry")
        return MongoDiscoveryStore(uri=uri, db_name=dbname)
    else:
        return InMemoryDiscoveryStore()


if __name__ == "__main__":
    persistent_store = get_discovery_store()
    run_simple("localhost", 8084, DiscoveryAPI(persistent_store=persistent_store),
               use_debugger=True, use_reloader=True)