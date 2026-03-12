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
| **PostSubmodelDescriptorThroughSuperPath**       | Register/create a new submodel descriptor under AAS descriptor | `POST http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors`                        |
| **GetSubmodelDescriptorThroughSuperPath**        | Return a specific submodel descriptor under AAS descriptor     | `GET http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorThroughSuperPath**        | Update a specific submodel descriptor under AAS descriptor     | `PUT http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorThroughSuperPath**     | Delete a specific submodel descriptor under AAS descriptor     | `DELETE http://localhost:8083/api/v3.0/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**                               | Return the self‑description of the AAS registry service        | `GET http://localhost:8083/api/v3.0/description`                                                                    |

# Submodel Registry:
| Function                         | Description                                                  | Example URL                                                                       |
|----------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **GetAllSubmodelDescriptors**    | Return all submodel descriptors                              | `GET http://localhost:8083/api/v3.0/submodel-descriptors`                         |
| **PostSubmodelDescriptor**       | Register/create a new submodel descriptor                    | `POST http://localhost:8083/api/v3.0/submodel-descriptors`                        |
| **GetSubmodelDescriptorById**    | Return a specific submodel descriptor                        | `GET http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorById**    | Update a specific submodel descriptor                        | `PUT http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorById** | Delete a specific submodel descriptor                        | `DELETE http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**               | Return the self‑description of the submodel registry service | `GET http://localhost:8083/api/v3.0/description`                                  |



## Configuration

The container can be configured via environment variables:

- `API_BASE_PATH` determines the base path under which all other API paths are made available. Default: `/api/v3.0`
- `STORAGE_TYPE` can be one of `LOCAL_FILE_READ_ONLY` or `LOCAL_FILE_BACKEND`:
  - When set to `LOCAL_FILE_READ_ONLY` (the default), the server will read and serve JSON files from the storage directory. The files are not modified, all changes done via the API are only stored in memory.
  - When instead set to `LOCAL_FILE_BACKEND`, the server makes use of the [LocalFileBackend](https://github.com/eclipse-basyx/basyx-python-sdk/tree/main/backend/basyx_backend/local_file), where AAS and Submodels descriptors are persistently stored as JSON files.
- `STORAGE_PATH` sets the directory to read the files from *within the container*. If you bind your files to a directory different from the default `/storage`, you can use this variable to adjust the server accordingly.


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

