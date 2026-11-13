# Combined
This example Docker compose configuration runs the repository, registry and discovery servers together, using the
pre-built images from DockerHub:

- [`eclipsebasyx/basyx-python-repository:latest`](https://hub.docker.com/r/eclipsebasyx/basyx-python-repository)
- [`eclipsebasyx/basyx-python-registry:latest`](https://hub.docker.com/r/eclipsebasyx/basyx-python-registry)
- [`eclipsebasyx/basyx-python-discovery:latest`](https://hub.docker.com/r/eclipsebasyx/basyx-python-discovery)

```
$ docker compose up
```

To build the images locally from source instead, use `compose.dev.yml`. This is usually only necessary for development:
```
$ docker compose -f compose.dev.yml up
```

The servers can be accessed from your host system at:

| Service    | URL                            | Input                | Storage                |
|------------|--------------------------------|----------------------|------------------------|
| Repository | http://localhost:8080/api/v3.1 | `./repository/input` | `./repository/storage` |
| Registry   | http://localhost:8083/api/v3.1 | `./registry/input`   | `./registry/storage`   |
| Discovery  | http://localhost:8084/api/v3.1 | -                    | `./discovery/storage`  |

Each service stores its data persistently in its own directory on your host system.
For the available endpoints of each service, see the
[repository](../repository_standalone/README.md), [registry](../registry_standalone/README.md) and
[discovery](../discovery_standalone/README.md) examples.
To get a different setup, the `compose.yml` (or `compose.dev.yml`) file can be adapted using the options described in
the main server [README.md](../../README.md#options).

Note that `compose.dev.yml` builds the images from the `server` directory. The local `sdk` directory is passed in as an
additional build context named `sdk`. To include the package license, a second additional build context `license`
passes in the repository root.
