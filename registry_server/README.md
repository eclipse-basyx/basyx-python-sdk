# Eclipse BaSyx Python SDK - Registry Service

This is a Python-based implementation of the **BaSyx Asset Administration Shell (AAS) Registry Service**.
It provides basic registry functionality for AAS and submodels descriptors, as specified in the official [Asset Administration Shell Registry Service Specification v3.1.0_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRegistryServiceSpecification/V3.1.0_SSP-001) and [Submodel Registry Service Specification v3.1.0_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRegistryServiceSpecification/V3.1.0_SSP-001).

## Overview

The Registry Service provides the endpoint for a given AAS-ID or Submodel-ID. Such an endpoint for an AAS and the related Submodel-IDs make the AAS and the submodels with their submodelElements accessible.



## Features
# AAS Registry:
| Function                                         | Description                                                    | Example URL                                                                                                         |
|--------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| **GetAllAssetAdministrationShellDescriptors**    | Return all AAS descriptor                                      | `GET http://localhost:8083/api/v3.0/shell-descriptors`                                                              |
| **GetAssetAdministrationShellDescriptorById**    | Return a specific AAS descriptor                               | `GET http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}`                                              |
| **PostAssetAdministrationShellDescriptor**       | Register/create a new AAS descriptor                           | `POST http://localhost:8083/api/v3.0/shell-descriptors`                                                             |
| **PutAssetAdministrationShellDescriptorById**    | Update an existing AAS descriptor                              | `PUT http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}`                                              |
| **DeleteAssetAdministrationShellDescriptorById** | Delete an AAS descriptor by ID                                 | `DELETE http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}`                                           |
| **GetSubmodelDescriptorsThroughSuperPath**       | Return all submodel descriptors under AAS descriptor           | `GET http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors`                         |
| **PostSubmodelDescriptorThroughSuperPath**       | Register/create a new submodel descriptor under AAS descriptor | `Post http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors`                        |
| **GetSubmodelDescriptorThroughSuperPath**        | Return a specific submodel descriptor under AAS descriptor     | `GET http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorThroughSuperPath**        | Update a specific submodel descriptor under AAS descriptor     | `PUT http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorThroughSuperPath**     | Delete a specific submodel descriptor under AAS descriptor     | `DELETE http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**                               | Return the self‑description of the AAS registry service        | `GET http://localhost:8083/api/v3.0/description`                                                                    |

# Submodel Registry:
| Function                         | Description                                                  | Example URL                                                                       |
|----------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **GetAllSubmodelDescriptors**    | Return all submodel descriptors                              | `GET http://localhost:8083/api/v3.0/submodel-descriptors`                         |
| **PostSubmodelDescriptor**       | Register/create a new submodel descriptor                    | `Post http://localhost:8083/api/v3.0/submodel-descriptors`                        |
| **GetSubmodelDescriptorById**    | Return a specific submodel descriptor                        | `GET http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorById**    | Update a specific submodel descriptor                        | `PUT http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorById** | Delete a specific submodel descriptor                        | `DELETE http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**               | Return the self‑description of the submodel registry service | `GET http://localhost:8083/api/v3.0/description`                                  |



## Specification Compliance

- Complies with: **Asset Administration Shell Registry Service Specification v3.1.0_SSP-001** and **Submodel Registry Service Specification v3.1.0_SSP-001**

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
The container image can be built and run via:
```bash
docker compose up --build
```

## Test

An example descriptor for testing purposes is provided as a JSON file in the [storage](./storage) folder.

## Acknowledgments

This Dockerfile is inspired by the [tiangolo/uwsgi-nginx-docker](https://github.com/tiangolo/uwsgi-nginx-docker) repository.

