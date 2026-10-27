# Eclipse BaSyx Python SDK - Registry Service

This is a Python-based implementation of the **Asset Administration Shell (AAS) Registry Service**.
It provides all registry functionality for AAS and submodels descriptors, as specified in the official [Asset Administration Shell Registry Service Specification v3.1.1_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRegistryServiceSpecification/V3.1.1_SSP-001) and [Submodel Registry Service Specification v3.1.1_SSP-001](https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRegistryServiceSpecification/V3.1.1_SSP-001).

## Overview

The Registry Service provides the endpoint for a given AAS-ID or Submodel-ID. Such an endpoint for an AAS and the related Submodel-IDs make the AAS and the submodels with their submodelElements accessible.



## Features
# AAS Registry:
| Function                                         | Description                                                          | Example URL                                                                                                           |
|--------------------------------------------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **GetAllAssetAdministrationShellDescriptors**    | Return all AAS descriptor                                            | `GET http://localhost:8083/api/v3.1/shell-descriptors`                                                              |
| **GetAssetAdministrationShellDescriptorById**    | Return a specific AAS descriptor                                     | `GET http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}`                                              |
| **PostAssetAdministrationShellDescriptor**       | Register/create a new AAS descriptor                                 | `POST http://localhost:8083/api/v3.1/shell-descriptors`                                                             |
| **PutAssetAdministrationShellDescriptorById**    | Create or update an existing AAS descriptor                          | `PUT http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}`                                              |
| **DeleteAssetAdministrationShellDescriptorById** | Delete an AAS descriptor by ID                                       | `DELETE http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}`                                           |
| **GetSubmodelDescriptorsThroughSuperPath**       | Return all submodel descriptors under AAS descriptor                 | `GET http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}/submodel-descriptors`                         |
| **PostSubmodelDescriptorThroughSuperPath**       | Register/create a new submodel descriptor under AAS descriptor       | `POST http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}/submodel-descriptors`                        |
| **GetSubmodelDescriptorThroughSuperPath**        | Return a specific submodel descriptor under AAS descriptor           | `GET http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorThroughSuperPath**        | Create or update a specific submodel descriptor under AAS descriptor | `PUT http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorThroughSuperPath**     | Delete a specific submodel descriptor under AAS descriptor           | `DELETE http://localhost:8083/api/v3.1/shell-descriptors/{aasIdentifier}/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**                               | Return the self‑description of the AAS registry service              | `GET http://localhost:8083/api/v3.1/description`                                                                    |

# Submodel Registry:
| Function                         | Description                                                  | Example URL                                                                       |
|----------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **GetAllSubmodelDescriptors**    | Return all submodel descriptors                              | `GET http://localhost:8083/api/v3.1/submodel-descriptors`                         |
| **PostSubmodelDescriptor**       | Register/create a new submodel descriptor                    | `POST http://localhost:8083/api/v3.1/submodel-descriptors`                        |
| **GetSubmodelDescriptorById**    | Return a specific submodel descriptor                        | `GET http://localhost:8083/api/v3.1/submodel-descriptors/{submodelIdentifier}`    |
| **PutSubmodelDescriptorById**    | Create or update a specific submodel descriptor              | `PUT http://localhost:8083/api/v3.1/submodel-descriptors/{submodelIdentifier}`    |
| **DeleteSubmodelDescriptorById** | Delete a specific submodel descriptor                        | `DELETE http://localhost:8083/api/v3.1/submodel-descriptors/{submodelIdentifier}` |
| **GetDescription**               | Return the self‑description of the submodel registry service | `GET http://localhost:8083/api/v3.1/description`                                  |



## Configuration

This example Docker compose configuration runs a registry server using the pre-built
`eclipsebasyx/basyx-python-registry:latest` image from [DockerHub](https://hub.docker.com/r/eclipsebasyx/basyx-python-registry):
```
$ docker compose up
```

To build the image locally from source instead, use `compose.dev.yml`. This is usually only necessary for development:
```
$ docker compose -f compose.dev.yml up
```

Input files are read from `./input` and stored persistently under `./storage` on your host system. 
The server can be accessed at http://localhost:8083/api/v3.1/ from your host system. 
To get a different setup, the `compose.yml` (or `compose.dev.yml`) file can be adapted using the options described in the main server [README.md](../../README.md#options).

Note that `compose.dev.yml` builds the image from the `server` directory. The local `sdk` directory is passed in as an additional build context named `sdk`.
To include the package license, a second additional build context `license` passes in the repository root.
