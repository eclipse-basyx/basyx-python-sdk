# Eclipse BaSyx Python SDK - Discovery Service

This is a Python-based implementation of the **BaSyx Asset Administration Shell (AAS) Discovery Service**.
It provides basic discovery functionality for AAS IDs and their corresponding assets, as specified in the official [Discovery Service Specification v3.1.0_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/DiscoveryServiceSpecification/V3.1.0_SSP-001).

## Overview

The Discovery Service stores and retrieves relations between AAS identifiers and asset identifiers. It acts as a lookup service for resolving asset-related queries to corresponding AAS.

## Features

| Function                                 | Description                                              | Example URL                                                           |
|------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------|
| **search_all_aas_ids_by_asset_link**     | Find AAS identifiers by providing asset link values      | `POST http://localhost:8084/api/v3.0/lookup/shellsByAssetLink`        |
| **get_all_specific_asset_ids_by_aas_id** | Return specific asset ids associated with an AAS ID      | `GET http://localhost:8084/api/v3.0/lookup/shells/{aasIdentifier}`    |
| **post_all_asset_links_by_id**           | Register specific asset ids linked to an AAS             | `POST http://localhost:8084/api/v3.0/lookup/shells/{aasIdentifier}`   |
| **delete_all_asset_links_by_id**         | Delete all asset links associated with a specific AAS ID | `DELETE http://localhost:8084/api/v3.0/lookup/shells/{aasIdentifier}` |
| 

## Configuration

The service can be configured to use either:

- **In-memory storage** (default): Temporary data storage that resets on service restart.
- **MongoDB storage**: Persistent backend storage using MongoDB.

### Configuration via Environment Variables

| Variable         | Description                                | Default                     |
|------------------|--------------------------------------------|-----------------------------|
| `STORAGE_TYPE`   | `inmemory` or `mongodb`                    | `inmemory`                  |
| `MONGODB_URI`    | MongoDB connection URI                     | `mongodb://localhost:27017` |
| `MONGODB_DBNAME` | Name of the MongoDB database               | `basyx_registry`            |

## Deployment via Docker

A `Dockerfile` and `docker-compose.yml` are provided for simple deployment.
The container image can be built and run via:
```bash
docker compose up --build
```
## Test

Examples of asset links and specific asset IDs for testing purposes are provided as JSON files in the [storage](./storage) folder.

## Acknowledgments

This Dockerfile is inspired by the [tiangolo/uwsgi-nginx-docker](https://github.com/tiangolo/uwsgi-nginx-docker) repository.
