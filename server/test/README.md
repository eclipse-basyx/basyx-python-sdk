# Server Testing

General, how to execute tests

## Unit Tests

### Format Agnostic Testing
- Decorators, Format Clients

## Integration Tests

[`docker_integration/`](docker_integration) contains one test module per server profile (repository, registry,
discovery). Unlike the unit tests above, these do not start a server themselves — each test runs a
`/description` check plus a full create/retrieve/delete roundtrip against a **real, already-running** server,
e.g. a Docker container started from the built image. This is the only layer that actually exercises uWSGI, nginx
and supervisor together, so it catches deployment/configuration problems the unit tests cannot see.

### `REQUIRE_SERVER_INTEGRATION_TESTS` environment variable

By default, the integration tests are **skipped** if no server is reachable at the URL configured in
`server/test/test_config.default.ini` (override it in your own, `.gitignore`d `server/test/test_config.ini`). This
is implemented in [`_helper/test_helpers.py`](_helper/test_helpers.py): it probes `GET /description` once at
import time and exposes the result as `SERVER_OKAY`. Every integration test class is decorated with
`@unittest.skipUnless(SERVER_OKAY or REQUIRE_SERVER, ...)`, so plain `python -m unittest` still passes locally
without a container running.

Set `REQUIRE_SERVER_INTEGRATION_TESTS` (to `1`/`true`/`yes`) to turn a missing server into a hard **failure**
instead of a skip:

```bash
REQUIRE_SERVER_INTEGRATION_TESTS=1 python -m unittest test.docker_integration.test_docker_integration_repository -v
```

This is what the `server-docker` CI job does for all three profiles: it builds the image, starts the container,
waits until it reports ready, and only then runs the matching test module with `REQUIRE_SERVER_INTEGRATION_TESTS=1`
set — so a container that fails to start is reported as a test failure, not a silently skipped test. The plain
`server-test` CI job, which never starts a container, explicitly sets `REQUIRE_SERVER_INTEGRATION_TESTS=0`, so
these tests are skipped there, as expected.