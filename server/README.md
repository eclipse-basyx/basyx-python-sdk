# Eclipse BaSyx Python SDK - HTTP Server

This package contains a Dockerfile to spin up an exemplary HTTP/REST server following the [Specification of the AAS Part 2 API][6] with ease.
The server currently implements the following interfaces:

- [Asset Administration Shell Repository Service][4]
- [Submodel Repository Service][5]

It uses the [HTTP API][1] and the [*AASX*][7], [*JSON*][8], and [*XML*][9] Adapters of the [BaSyx Python SDK][3], to serve regarding files from a given directory.
The files are only read, changes won't persist.

Alternatively, the container can also be told to use the [Local-File Backend][2] instead, which stores Asset Administration Shells (AAS) and Submodels as individual *JSON* files and allows for persistent changes (except supplementary files, i.e. files referenced by `File` SubmodelElements).
See [below](#options) on how to configure this.

## Building

The container image can be built via:
```
$ docker build -t basyx-python-server -f Dockerfile ..
```

Note that when cloning this repository on Windows, Git may convert the line separators to CRLF. This breaks [`entrypoint.sh`](entrypoint.sh) and [`stop-supervisor.sh`](stop-supervisor.sh). Ensure both files use LF line separators (`\n`) before building. 

## Running

### Storage

The server makes use of two directories:

- **`/input`** - *start-up data*: Directory from which the server loads AAS and Submodel files in *AASX*, *JSON* or *XML* format during start-up. The server will not modify these files.
- **`/storage`** - *persistent store*: Directory where all AAS and Submodels are stored as individual *JSON* files if the server is [configured](#options) for persistence. The server will modify these files.

The directories can be mapped via the `-v` option from another image or a local directory.
To mount the host directories into the container, `-v ./input:/input -v ./storage:/storage` can be used.
Both local directories `./input` and `./storage` will be created in the current working directory, if they don't already exist.

### Port

The HTTP server inside the container listens on port 80 by default.
To expose it on the host on port 8080, use the option `-p 8080:80` when running it.

### Options

The container can be configured via environment variables. The most important ones are summarised below:

| Variable              | Description                                                                                                                                                                                                                                                                                                  | Default      |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| `API_BASE_PATH`       | Base path under which the API is served.                                                                                                                                                                                                                                                                     | `/api/v3.0/` |
| `INPUT`               | Path inside the container pointing to the directory from which the server takes its start-up data (*AASX*, *JSON*, *XML*).                                                                                                                                                                                   | `/input`     |
| `STORAGE`             | Path inside the container pointing to the directory used by the server to persistently store data (*JSON*).                                                                                                                                                                                                  | `/storage`   |
| `STORAGE_PERSISTENCY` | Flag to enable data persistence via the [LocalFileBackend][2]. AAS/Submodels are stored as *JSON* files in the directory specified by `STORAGE`. Supplementary files, i.e. files referenced by `File` SubmodelElements, are not stored. If disabled, any changes made via the API are only stored in memory. | `False`      |
| `STORAGE_OVERWRITE`   | Flag to enable storage overwrite if `STORAGE_PERSISTENCY` is enabled. Any AAS/Submodel from the `INPUT` directory already present in the LocalFileBackend replaces its existing version. If disabled, the existing version is kept.                                                                          | `False`      |


This implies the following start-up behaviour:

- Any AAS/Submodel found in `INPUT` is loaded during start-up.
- If `STORAGE_PERSISTENCY = True`:
  - Any AAS/Submodel *not* present in the LocalFileBackend is added to it.
  - Any AAS/Submodel *already present* is skipped, unless `STORAGE_OVERWRITE = True`, in which case it is replaced.
- Supplementary files (e.g., `File` SubmodelElements) are never persisted by the LocalFileBackend.

### Running Examples

Putting it all together, the container can be started via the following command:
```
$ docker run -p 8080:80 -v ./input:/input -v ./storage:/storage basyx-python-server
```

Since Windows uses backslashes instead of forward slashes in paths, you'll have to adjust the path to the storage directory there:
```
> docker run -p 8080:80 -v .\input:/input -v .\storage:/storage basyx-python-server
```

By default, the server will use the standard settings described [above](#options). Those settings can be adapted in the following way:
```
$ docker run -p 8080:80 -v ./input:/input2 -v ./storage:/storage2 -e API_BASE_PATH=/api/v3.1/ -e INPUT=/input2 -e STORAGE=/storage2 -e STORAGE_PERSISTENCY=True -e STORAGE_OVERWRITE=True basyx-python-server
```

## Building and Running the Image with Docker Compose

The container image can also be built and run via:
```
$ docker compose up
```

An exemplary [`compose.yml`](compose.yml) file for the server is given [here](compose.yml):
```yaml
name: basyx-python-server
services:
  app:
    build:
      context: ..
      dockerfile: server/Dockerfile
    ports:
    - "8080:80"
    volumes:
      - ./input:/input
      - ./storage:/storage
    environment:
      STORAGE_PERSISTENCY: True
```

Input files are read from `./input` and stored persistently under `./storage` on your host system. The server can be accessed at http://localhost:8080/api/v3.0/ from your host system. 
To get a different setup, the [`compose.yml`](compose.yml) file can be adapted using the options described [above](#options), similar to the third [running example](#running-examples).

Note that the `Dockerfile` has to be specified explicitly via `dockerfile: server/Dockerfile`, as the build context must be set to the parent directory of `/server` to allow access to the local `/sdk`.

## Running without Docker (Debugging Only)

The server can also be run directly on the host system without Docker, NGINX and supervisord. Although this is not suitable for production, it may be useful for debugging.

> [!warning]
> Not supported for production systems!

1. Install the local SDK and the local server package.
   ```bash
   $ pip install ../sdk
   $ pip install ./app
   ```

2. Run the server by executing the main function in [`./app/interfaces/repository.py`](./app/interfaces/repository.py).
   ```bash
   $ python -m app.interfaces.repository
   ```

The server can be accessed at http://localhost:8080/api/v3.0/ from your host system. 

## Acknowledgments

This Dockerfile is inspired by the [tiangolo/uwsgi-nginx-docker][10] repository.

[1]: https://github.com/eclipse-basyx/basyx-python-sdk/pull/238
[2]: https://basyx-python-sdk.readthedocs.io/en/latest/backend/local_file.html
[3]: https://github.com/eclipse-basyx/basyx-python-sdk
[4]: https://app.swaggerhub.com/apis/Plattform_i40/AssetAdministrationShellRepositoryServiceSpecification/V3.0.1_SSP-001
[5]: https://app.swaggerhub.com/apis/Plattform_i40/SubmodelRepositoryServiceSpecification/V3.0.1_SSP-001
[6]: https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.1.1/index.html
[7]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/aasx.html#adapter-aasx
[8]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/json.html
[9]: https://basyx-python-sdk.readthedocs.io/en/latest/adapter/xml.html
[10]: https://github.com/tiangolo/uwsgi-nginx-docker
