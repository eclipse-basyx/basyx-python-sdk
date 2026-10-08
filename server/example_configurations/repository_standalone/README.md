# Repository Standalone
This example Docker compose configuration runs a repository server using the pre-built
`eclipsebasyx/basyx-python-repository` image from [DockerHub](https://hub.docker.com/r/eclipsebasyx/basyx-python-repository):
```
$ docker compose up
```

To build the image locally from source instead, use `compose.dev.yml`. This is usually only necessary for development:
```
$ docker compose -f compose.dev.yml up
```

Input files are read from `./input` and stored persistently under `./storage` on your host system. 
The server can be accessed at http://localhost:8080/api/v3.0/ from your host system. 
To get a different setup, the `compose.yml` (or `compose.dev.yml`) file can be adapted using the options described in the main server [README.md](../../README.md#options).

Note that `compose.dev.yml` builds the image from the `server` directory. The local `sdk` directory is passed in as an additional build context named `sdk`.
To include the package license, a second additional build context `license` passes in the repository root.
