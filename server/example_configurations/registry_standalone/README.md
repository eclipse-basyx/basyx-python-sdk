# Eclipse BaSyx Python SDK - Registry Service

This is a Python-based implementation of the **Asset Administration Shell (AAS) Registry Service**.
It provides all registry functionality for AAS and submodels descriptors, as specified in the official [Asset Administration Shell Registry Service Specification v3.1.1_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRegistryServiceSpecification/V3.1.1_SSP-001) and [Submodel Registry Service Specification v3.1.1_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRegistryServiceSpecification/V3.1.1_SSP-001).

## Overview

The Registry Service provides the endpoint for a given AAS-ID or Submodel-ID. Such an endpoint for an AAS and the related Submodel-IDs make the AAS and the submodels with their submodelElements accessible.



## Features
# AAS Registry:
| Function                                         | Description                                                          | Example URL                                                                                                           |
|--------------------------------------------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **GetAllAssetAdministrationShellDescriptors**    | Return all AAS descriptor                                            | `GET http://localhost:8083/api/v3.1.1/shell-descriptors`                                                              |
| **GetAssetAdministrationShellDescriptorById**    | Return a specific AAS descriptor                                     | `GET http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}`                                              |
| **PostAssetAdministrationShellDescriptor**       | Register/create a new AAS descriptor                                 | `POST http://localhost:8083/api/v3.1.1/shell-descriptors`                                                             |
| **PutAssetAdministrationShellDescriptorById**    | Create or update an existing AAS descriptor                          | `PUT http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}`                                              |
| **DeleteAssetAdministrationShellDescriptorById** | Delete an AAS descriptor by ID                                       | `DELETE http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}`                                           |
| **GetSubmodelDescriptorsThroughSuperPath**       | Return all submodel descriptors under AAS descriptor                 | `GET http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}/submodel-descriptors`                         |
| **PostSubmodelDescriptorThroughSuperPath**       | Register/create a new submodel descriptor under AAS descriptor       | `POST http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}/submodel-descriptors`                        |
| **GetSubmodelDescriptorThroughSuperPath**        | Return a specific submodel descriptor under AAS descriptor           | `GET http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorThroughSuperPath**        | Create or update a specific submodel descriptor under AAS descriptor | `PUT http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorThroughSuperPath**     | Delete a specific submodel descriptor under AAS descriptor           | `DELETE http://localhost:8083/api/v3.1.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**                               | Return the self‑description of the AAS registry service              | `GET http://localhost:8083/api/v3.1.1/description`                                                                    |

# Submodel Registry:
| Function                         | Description                                                  | Example URL                                                                       |
|----------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **GetAllSubmodelDescriptors**    | Return all submodel descriptors                              | `GET http://localhost:8083/api/v3.0/submodel-descriptors`                         |
| **PostSubmodelDescriptor**       | Register/create a new submodel descriptor                    | `POST http://localhost:8083/api/v3.0/submodel-descriptors`                        |
| **GetSubmodelDescriptorById**    | Return a specific submodel descriptor                        | `GET http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorById**    | Create or update a specific submodel descriptor              | `PUT http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorById** | Delete a specific submodel descriptor                        | `DELETE http://localhost:8083/api/v3.0/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**               | Return the self‑description of the submodel registry service | `GET http://localhost:8083/api/v3.0/description`                                  |



## Configuration

This example Docker compose configuration starts a registry server. 

The container image can also be built and run via:
```
$ docker compose up
```

Input files are read from `./input` and stored persistently under `./storage` on your host system. 
The server can be accessed at http://localhost:8083/api/v3.1.1/ from your host system. 
To get a different setup, the `compose.yaml` file can be adapted using the options described in the main server [README.md](../../README.md#options).

Note that the `Dockerfile` has to be specified explicitly via `dockerfile: server/docker/repository/Dockerfile`, as the build context must be set to the repository root to allow access to the local `/sdk`.

