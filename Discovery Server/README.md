# Eclipse BaSyx Python SDK - Discovery Service

This is a Python-based implementation of the **BaSyx Asset Administration Shell (AAS) Discovery Service**.
It provides basic discovery functionality for AAS IDs and their corresponding assets, as specified in the official [Discovery Service Specification v3.1.0_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/DiscoveryServiceSpecification/V3.1.0_SSP-001).

## Overview

The Discovery Service is a core component in the Asset Administration Shell ecosystem. Its main responsibility is to store and retrieve relations between AAS identifiers and asset identifiers. It acts as a lookup service for resolving asset-related queries to corresponding AAS.

This implementation supports:

- Adding links between AAS and assets
- Querying AAS by asset links
- Querying asset links by AAS ID
- Removing AAS-related asset links
- Configurable in-memory or MongoDB-based persistent storage

## Features

| Feature                                      | Description                                           |
|---------------------------------------------|-------------------------------------------------------|
| `add_asset_links`                           | Register specific asset ids linked to an AAS          |
| `get_all_specific_asset_ids_by_aas_id`      | Retrieve specific asset ids associated with an AAS    |
| `search_aas_by_asset_link`                  | Find AAS identifiers by providing asset link values   |
| `remove_asset_links_for_aas`                | Delete all asset links associated with a specific AAS |

## Specification Compliance

- Complies with: **Discovery Service Specification v3.1.0_SSP-001**

## Configuration

The service can be configured to use either:

- **In-memory storage** (default): Temporary data storage that resets on service restart.
- **MongoDB storage**: Persistent backend storage using MongoDB.

### Configuration via Environment Variables

| Variable        | Description                                | Default                 |
|----------------|--------------------------------------------|-------------------------|
| `STORAGE_TYPE` | `inmemory` or `mongodb`                    | `inmemory`              |
| `MONGODB_URI`  | MongoDB connection URI                     | `mongodb://localhost:27017` |
| `MONGODB_DBNAME` | Name of the MongoDB database               | `basyx_registry`        |

## Deployment via Docker

A `Dockerfile` and `docker-compose.yml` are provided for simple deployment.

## Acknowledgments

This Dockerfile is inspired by the [tiangolo/uwsgi-nginx-docker][10] repository.

[1]: https://github.com/eclipse-basyx/basyx-python-sdk/pull/238
[2]: https://basyx-python-sdk.readthedocs.io/en/latest/backend/local_file.html
[3]: https://github.com/eclipse-basyx/basyx-python-sdk
[4]: https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRepositoryServiceSpecification/V3.0.1_SSP-001
[5]: https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRepositoryServiceSpecification/V3.0.1_SSP-001
[6]: https://industrialdigitaltwin.org/content-hub/aasspecifications/idta_01002-3-0_application_programming_interfaces
[7]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/aasx.html#adapter-aasx
[8]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/json.html
[9]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/xml.html
[10]: https://github.com/tiangolo/uwsgi-nginx-docker
