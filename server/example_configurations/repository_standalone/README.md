# Repository Standalone
The example Docker compose configuration `compose.dev.yml` builds a repository server locally. This is usually only necessary
for development:
```
$ docker compose -f compose.dev.yml up
```
To just run the repository server, use the pre-built image `eclipsebasyx/basyx-python-repository` 
on [DockerHub](https://hub.docker.com/r/eclipsebasyx/basyx-python-repository).

Input files are read from `./input` and stored persistently under `./storage` on your host system. 
The server can be accessed at http://localhost:8080/api/v3.0/ from your host system. 
To get a different setup, the `compose.dev.yml` file can be adapted using the options described in the main server [README.md](../../README.md#options).

Note that the image is built from the `server` directory. The local `sdk` directory is passed in as an additional build context named `sdk`.
To include the package license, a second additional build context `license` passes in the repository root.
