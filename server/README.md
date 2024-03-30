# Eclipse BaSyx Python SDK - HTTP Server

This repository contains a Dockerfile to spin up an exemplary DotAAS HTTP/REST server with ease.
The server currently implements the following interfaces:

- [Asset Administration Shell Repository Service][4]
- [Submodel Repository Service][5]

It uses the [HTTP Adapter][1] and the [Local-File Backend][2] of the [BaSyx Python SDK][3], which allows server-side data to be stored persistently across container restarts.


## Building
The container image can be built via:
```
$ docker buildx build -t basyx-python-sdk-http-server .
```

## Running
Because the server uses the [Local-File Backend][2], the container needs to be provided with the directory `/storage` to store AAS and Submodel JSON files.
This directory can be mapped via the `-v` option from another image or a local directory.
To map the directory `storage` inside the container, `-v ./storage:/storage` can be used.
The directory `storage` will be created in the current working directory, if it doesn't already exist.

The HTTP server inside the container listens on port 80 by default.
To expose it on the host on port 8080, use the option `-p 8080:80` when running it.

Putting it all together, the container can be started via the following command:
```
$ docker run -p 8080:80 -v ./storage:/storage basyx-python-sdk-http-server
```

[1]: https://github.com/eclipse-basyx/basyx-python-sdk/pull/238
[2]: https://basyx-python-sdk.readthedocs.io/en/latest/backend/local_file.html
[3]: https://github.com/eclipse-basyx/basyx-python-sdk
[4]: https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRepositoryServiceSpecification/V3.0.1_SSP-001
[5]: https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRepositoryServiceSpecification/V3.0.1_SSP-001
