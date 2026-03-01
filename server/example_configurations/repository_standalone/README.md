# Repository Standalone

This example Docker compose configuration starts a repository server. 

The container image can also be built and run via:
```
$ docker compose up
```

Input files are read from `./input` and stored persistently under `./storage` on your host system. 
The server can be accessed at http://localhost:8080/api/v3.0/ from your host system. 
To get a different setup, the `compose.yaml` file can be adapted using the options described in the main server [README.md](../../README.md#options), similar to the third [running example](#running-examples).

Note that the `Dockerfile` has to be specified explicitly via `dockerfile: server/Dockerfile`, as the build context must be set to the parent directory of `/server` to allow access to the local `/sdk`.

