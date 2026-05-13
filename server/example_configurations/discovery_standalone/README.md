# Eclipse BaSyx Python SDK - Discovery Service

This is a Python-based implementation of the **BaSyx Asset Administration Shell (AAS) Discovery Service**.
It provides basic discovery functionality for AAS IDs and their corresponding assets, as specified in the official [Discovery Service Specification v3.1.1_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/DiscoveryServiceSpecification/V3.1.1_SSP-001).

## Overview

The Discovery Service stores and retrieves relations between AAS identifiers and asset identifiers. It acts as a lookup service for resolving asset-related queries to corresponding AAS.

## Features

| Function                                 | Description                                              | Example URL                                                           |
|------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------|
| **get_description**                      | Return the supported Discovery Service profiles          | `GET http://localhost:8084/api/v3.1/description`                      |
| **get_all_aas_ids_by_asset_link**        | Find AAS identifiers by asset link query parameter       | `GET http://localhost:8084/api/v3.1/lookup/shells?assetIds={assetIds}` |
| **search_all_aas_ids_by_asset_link**     | Find AAS identifiers by providing asset link values      | `POST http://localhost:8084/api/v3.1/lookup/shellsByAssetLink`        |
| **get_all_specific_asset_ids_by_aas_id** | Return specific asset ids associated with an AAS ID      | `GET http://localhost:8084/api/v3.1/lookup/shells/{aasIdentifier}`    |
| **post_all_asset_links_by_id**           | Register specific asset ids linked to an AAS             | `POST http://localhost:8084/api/v3.1/lookup/shells/{aasIdentifier}`   |
| **delete_all_asset_links_by_id**         | Delete all asset links associated with a specific AAS ID | `DELETE http://localhost:8084/api/v3.1/lookup/shells/{aasIdentifier}` |


## Configuration
This example Docker compose configuration starts a discovery server. 

The container image can also be built and run via:
```
$ docker compose up
```

## Persistence

The discovery service can run in persistent or non-persistent mode.

### Persistent Mode

Persistent mode configuration is provided in the `compose.yaml`.

Only the AAS-to-asset-ID mapping is persisted. The reverse lookup index is rebuilt in memory when the service starts.

### Non-Persistent Mode

If `storage_path` is not set, the discovery service runs in memory only.

## Notes
- Stop the service before manually editing `discovery_store.json`.

