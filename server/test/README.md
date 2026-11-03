# Server Testing

The `server` package holds the code for three different server profiles: `repository`, `registry` and `discovery`.
We use unit testing as well as integration testing to ensure these servers are working as expected, from the Python
code up to a running Docker container.

To execute all tests, run `python -m unittest` from the parent `server`  directory. If no server is running on your system yet,
the integration tests are skipped. For more details refer to the section about [Integration Tests](#integration-tests).

## Unit Tests
Unit tests are used to cover the complete python implementation of our server. We structure the tests equivalent to the
source files.

In the [`adapter`](adapter) directory serialization of server specific objects is tested (defined in `ResultToJsonEncoder`).
Note that serialization of AAS objects is not tested, because this is already covered in the `sdk` project.

The `DictDescriptorStore` and `LocalFileDescriptorStore` are also tested directly for correctness in directories
[`model`](model) and [`backend`](backend) respectively.

The [`servcies`](services) directory holds tests for the startup of the different servers via the `run_*.py` scripts
(`server/app/services`). The test cases verify that the set environment variables are respected.

The central API logic is defined in `server/app/interfaces`, which is tested in [`interfaces`](interfaces).
Code from `base.py` that is shared among the three interfaces (`repository.py`, `registry.py`, `discovery.py`)
is tested separately. This includes pagination logic, `JsonResponse` and `XmlResponse`.

For the API endpoints of all three interfaces, we write test cases covering the successful path as well as error cases.
We chose not to fully parse responses with the deserializers from the `sdk` to decouple the API testing from testing
the deserialization logic. Instead, we check that the results contain the expected objects (via IDs), that
modifying operations correctly modify the objects in the backing storage (e.g. `object_store` for repository) and that
the responses reflect these changes correctly.

The `registry.py` and `discovery.py` interfaces only allow JSON as content type and are small enough to be tested in
one file each. For the `repository.py` tests are split into separate files inside [`interfaces/repository`](interfaces/repository) 
to keep files of manageable size. Find details on how test cases for this interface are written in the subsection
[Format Agnostic Testing](#format-agnostic-testing).

### Format Agnostic Testing
Our `repository` implementation supports `application/json` and `application/xml` as content types of requests and
responses. This doubles the surface of the API that needs to be tested in the unit tests. We want to ensure that
regardless of the data format the request and response body is serialized to, the server behavior is as expected.
In a naive approach this would require each test case to be mirrored for JSON and XML format, which brings all the
disadvantages of duplicated code.

To solve this challenge, we decided to write the tests in [`interfaces/repository`](interfaces/repository) with
format agnostic methods for requesting and result verification. We encapsulate the format agnostic methods in an
abstract superclass [`FormatClient`](interfaces/format_utils.py) which offers methods to send requests as well as simple
parsing of responses in order to retrieve IDs and other field values.
This allows us to write test cases using the abstract interface of this class for requesting and correctness checking
of the result. The concrete subclasses implement the serialization and deserialization to and from a specific format.
In our case we derive the subclasses `JsonFormatClient` and `XmlFormatClient`. For an example see 
[Writing test cases](#writing-test-cases).

#### Sending requests
Our `FormatClient` wraps the [`Client`](https://werkzeug.palletsprojects.com/en/stable/test/#werkzeug.test.Client)
class of the `Werkzeug` package. It offers methods for the used HTTP requests (`get()`, `post()`, `put()`, `patch()`,
`delete()`) and delegates the execution of these requests to the Werkzeug `Client`.
Subclasses need to define a class variable `content_type` and override the abstract method `serialize()`.
This method is used to serialize request body objects, passed to `post()`, `put()` and `patch()`, into string format,
in order to send the request. All requests are equipped with an `Accept` header.

We use `ServerAASToJsonEncoder` and `object_to_xml_element()` respectively inside the `serialize()` methods 
of our concrete subclasses.

#### Validating responses

For this purpose, our `FormatClient` offers abstract methods `parse_object(response)` and `parse_collection(response)` 
to convert the response body into an intermediate representation (e.g. `dict` or `etree._Element`). To access certain
values of these representations, `identifier(node)`, `field(node, name)` and `reference_target(node)` can be used.

We use `json.loads()` and `etree.fromstring()` in our concrete subclasses to parse the response bodies.


#### Writing test cases
The interface of the abstract `FormatClient` described above can then be used to write format agnostic test cases.
In order to inject a `FormatClient` instance into `test_*()` methods and to keep the different format
instantiations of the same test from interfering with each other, we use decorators on both the test class and the
test methods.

Consider the following `SimpleAPITest` class as an example:

```python
@inject_format_clients
class SimpleAPITest(unittest.TestCase):
    object_store: model.SetIdentifiableStore[model.Identifiable]
    client: werkzeug.test.Client # must exist for @inject_format_clients to work
    server: repository.WSGIApp
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.object_store = model.SetIdentifiableStore() 
        cls.server = repository.WSGIApp(...)
        cls.client = werkzeug.test.Client(cls.server)

    def setUp(self):
        self.object_store.clear()

    @with_json_client
    @with_xml_client
    def test_shells_get(self, format_client: FormatClient):
        self.object_store.update(...)

        response = format_client.get("/shells?idShort=Alpha")
        ids = {format_client.identifier(node) for node in format_client.parse_collection(response)}

        self.assertEqual(
            {"https://example.org/shell-alpha", "https://example.org/shell-gamma"}, ids
        )
```

We use the class decorator `@inject_format_clients` on the test class. This decorator requires the class to have a class
attribute `client` which will be used in the constructor of the `FormatClient` subclasses. We can then add test cases
that take a `FormatClient` as second parameter and decorate them with one or both function decorators
`@with_json_client` and `@with_xml_client`. For each of the function decorators a separate test case 
(`test_*_json()` and `test_*_xml()`) with the correct `JsonFormatClient` or `XmlFormatClient` will be created.
For more details see below.

#### Detail on the decorators
The function decorators `@with_json_client` and `@with_xml_client` mark the function by adding information to the
`_client_types` attribute of the function object.
At runtime, `@inject_format_clients` scans the class for methods that carry a non-empty `_client_types`.
Such a method (`test_shells_get(self, format_client)` in the example) is removed from the class and replaced by
one method per decorated format (`test_shells_get_json(self)`, `test_shells_get_xml(self)`).
The new methods construct an instance of the corresponding `FormatClient` subclass using `cls.client` and call the
original method with it. The decorated class is equivalent to this:

```python
class SimpleAPITest(unittest.TestCase):
    # Omitting class attributes and setUpClass()/setUp()
    
    def test_shells_get_json(self):
        format_client_instance = JsonFormatClient(self.client)
        def test_shells_get(self, format_client):
            ... # Body of the original SimpleAPITest.test_shells_get method
        return test_shells_get(self, format_client_instance)

    def test_shells_get_xml(self):
        format_client_instance = XmlFormatClient(self.client)
        def test_shells_get(self, format_client):
            ... # Body of the original SimpleAPITest.test_shells_get method
        return test_shells_get(self, format_client_instance)
```
As the decorated class no longer has a method called `test_shells_get`, unittest may throw an error if you try to
execute `python -m unittest SimpleAPITest.test_shells_get`. Use the function names with their appended format
(`SimpleAPITest.test_shells_get_json` and `SimpleAPITest.test_shells_get_xml`) instead.

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