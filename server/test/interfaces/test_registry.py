"""
Endpoint tests for :class:`~app.interfaces.registry.RegistryAPI`.

The routes and status codes follow the *Asset Administration Shell Registry* and *Submodel Registry*
Service Specifications (SSP-001, "full" profile) from ``aas-specs-api``. Only JSON is exercised: the
registry only stores :class:`~app.model.descriptor.Descriptor` objects, which the SDK XML serializer
cannot handle, and the spec only defines ``application/json`` for these routes.

Requests and responses go through the shared :class:`~..format_utils.JsonFormatClient` (as in
``test/interfaces/repository/test_shells.py``), which serializes request bodies with the server's
``ServerAASToJsonEncoder`` so :class:`~app.model.descriptor.Descriptor` objects can be sent.
"""

import unittest
from typing import Any

from app.interfaces.registry import RegistryAPI
from app.model import DictDescriptorStore
from app.model.descriptor import AssetAdministrationShellDescriptor, SubmodelDescriptor
from app.model.endpoint import Endpoint, ProtocolInformation
from app.util.converters import base64url_encode
from basyx.aas import model
from werkzeug.test import Client, TestResponse

from .format_utils import JsonFormatClient


class _InMemoryDescriptorStore(DictDescriptorStore):
    """
    In-memory descriptor store with a no-op ``commit`` and a ``clear``.

    :class:`~app.model.provider.DictDescriptorStore` inherits ``commit`` from the SDK's
    ``AbstractObjectStore``, where it raises ``NotImplementedError``; the registry calls it after every
    write. This mirrors what ``SetIdentifiableStore`` provides for the repository tests.
    """

    def commit(self, x: Any) -> None:
        pass

    def clear(self) -> None:
        self._backend.clear()


def _endpoint(interface: str = "AAS-3.0", href: str = "https://example.org/endpoint") -> Endpoint:
    return Endpoint(interface=interface, protocol_information=ProtocolInformation(href=href))


def _aas_descriptor(id_: str, **kwargs: Any) -> AssetAdministrationShellDescriptor:
    kwargs.setdefault("endpoints", [_endpoint("AAS-3.0")])
    return AssetAdministrationShellDescriptor(id_=id_, **kwargs)


def _submodel_descriptor(id_: str, **kwargs: Any) -> SubmodelDescriptor:
    kwargs.setdefault("endpoints", [_endpoint("SUBMODEL-3.0")])
    return SubmodelDescriptor(id_=id_, **kwargs)


class RegistryEndpointTestBase(unittest.TestCase):
    __test__ = False

    AAS_ID = "https://example.org/shell-descriptors/1"
    AAS_ID_2 = "https://example.org/shell-descriptors/2"
    SM_ID = "https://example.org/submodel-descriptors/1"
    SM_ID_2 = "https://example.org/submodel-descriptors/2"
    UNKNOWN_ID = "https://example.org/unknown"

    store: _InMemoryDescriptorStore
    registry_server: RegistryAPI
    client: Client
    format_client: JsonFormatClient

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.store = _InMemoryDescriptorStore()
        cls.registry_server = RegistryAPI(cls.store, base_path="")
        cls.client = Client(cls.registry_server)
        cls.format_client = JsonFormatClient(cls.client)

    def setUp(self) -> None:
        self.store.clear()

    # ------------------------------------------------------------------ assertion helpers

    def assert_ok(self, response: TestResponse) -> None:
        self.assertEqual(200, response.status_code, msg=response.get_data(as_text=True))

    def assert_error(self, response: TestResponse, status_code: int) -> None:
        self.assertEqual(status_code, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn("success", response.get_data(as_text=True), msg=response.get_data(as_text=True))

    def ids(self, response: TestResponse) -> list:
        return [self.format_client.identifier(node) for node in self.format_client.parse_collection(response)]


# ====================================================================== /description


class RegistryServiceDescriptionTest(RegistryEndpointTestBase):
    __test__ = True

    def test_description_ok(self) -> None:
        response = self.format_client.get("/description")

        self.assert_ok(response)
        profiles = self.format_client.parse_object(response)["profiles"]
        self.assertIn(
            "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-001", profiles
        )
        self.assertIn("https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-001", profiles)
        self.assertIn(
            "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-002", profiles
        )
        self.assertIn("https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-002", profiles)


# ====================================================================== /shell-descriptors


class ShellDescriptorsEndpointTest(RegistryEndpointTestBase):
    """Tests for the ``/shell-descriptors`` and ``/shell-descriptors/{aasIdentifier}`` routes."""

    __test__ = True

    # ------------------------------------------------------------------ GET /shell-descriptors

    def test_get_all_empty(self) -> None:
        response = self.format_client.get("/shell-descriptors")

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    def test_get_all_returns_registered_descriptors(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))
        self.store.add(_aas_descriptor(self.AAS_ID_2))

        response = self.format_client.get("/shell-descriptors")

        self.assert_ok(response)
        self.assertEqual({self.AAS_ID, self.AAS_ID_2}, set(self.ids(response)))

    def test_get_all_only_returns_aas_descriptors(self) -> None:
        # The store is shared between the AAS- and Submodel-registry routes, so this route must filter by type.
        self.store.add(_aas_descriptor(self.AAS_ID))
        self.store.add(_submodel_descriptor(self.SM_ID))

        response = self.format_client.get("/shell-descriptors")

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID], self.ids(response))

    def test_get_all_supports_pagination(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))
        self.store.add(_aas_descriptor(self.AAS_ID_2))

        pages = self.format_client.get_paginated("/shell-descriptors", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])
        seen = [self.format_client.identifier(node) for page in pages for node in page]
        self.assertEqual({self.AAS_ID, self.AAS_ID_2}, set(seen))
        self.assertEqual(len(seen), len(set(seen)), "an item was returned on more than one page")

    def test_get_all_negative_limit_returns_400(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))

        self.assert_error(self.format_client.get("/shell-descriptors?limit=-1"), 400)

    def test_get_all_filter_by_asset_kind(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID, asset_kind=model.AssetKind.INSTANCE))
        self.store.add(_aas_descriptor(self.AAS_ID_2, asset_kind=model.AssetKind.TYPE))

        response = self.format_client.get("/shell-descriptors?assetKind=INSTANCE")

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID], self.ids(response))

    def test_get_all_filter_by_asset_kind_invalid_returns_400(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID, asset_kind=model.AssetKind.INSTANCE))

        # The enum member names are upper-case; the serialized ("Instance") spelling is rejected.
        self.assert_error(self.format_client.get("/shell-descriptors?assetKind=Instance"), 400)

    def test_get_all_filter_by_asset_type(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID, asset_type="https://example.org/type/a"))
        self.store.add(_aas_descriptor(self.AAS_ID_2, asset_type="https://example.org/type/b"))

        response = self.format_client.get(
            f"/shell-descriptors?assetType={base64url_encode('https://example.org/type/b')}"
        )

        self.assert_ok(response)
        self.assertEqual([self.AAS_ID_2], self.ids(response))

    def test_get_all_filter_by_asset_type_no_match(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID, asset_type="https://example.org/type/a"))

        response = self.format_client.get(
            f"/shell-descriptors?assetType={base64url_encode('https://example.org/type/none')}"
        )

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    # ------------------------------------------------------------------ POST /shell-descriptors

    def test_post_success(self) -> None:
        descriptor = _aas_descriptor(self.AAS_ID)

        response = self.format_client.post("/shell-descriptors", obj=descriptor)

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.AAS_ID), response.headers["Location"])
        self.assertEqual(self.AAS_ID, self.format_client.identifier(self.format_client.parse_object(response)))
        self.assertIsNotNone(self.store.get(self.AAS_ID))

    def test_post_missing_id_returns_400(self) -> None:
        response = self.format_client.post(
            "/shell-descriptors", data=b'{"endpoints": []}', content_type="application/json"
        )

        self.assert_error(response, 400)

    def test_post_malformed_json_returns_400(self) -> None:
        response = self.format_client.post("/shell-descriptors", data=b"not json", content_type="application/json")

        self.assert_error(response, 400)

    def test_post_unsupported_content_type_returns_415(self) -> None:
        response = self.format_client.post(
            "/shell-descriptors",
            data=self.format_client.serialize(_aas_descriptor(self.AAS_ID)),
            content_type="text/plain",
        )

        self.assert_error(response, 415)

    def test_post_conflict_returns_409(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))

        self.assert_error(self.format_client.post("/shell-descriptors", obj=_aas_descriptor(self.AAS_ID)), 409)

    # ------------------------------------------------------------------ GET /shell-descriptors/{aasIdentifier}

    def test_get_by_id_success(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))

        response = self.format_client.get(f"/shell-descriptors/{base64url_encode(self.AAS_ID)}")

        self.assert_ok(response)
        self.assertEqual(self.AAS_ID, self.format_client.identifier(self.format_client.parse_object(response)))

    def test_get_by_id_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.get(f"/shell-descriptors/{base64url_encode(self.UNKNOWN_ID)}"), 404)

    # ------------------------------------------------------------------ PUT /shell-descriptors/{aasIdentifier}

    def test_put_creates_when_absent_returns_201(self) -> None:
        response = self.format_client.put(
            f"/shell-descriptors/{base64url_encode(self.AAS_ID)}", obj=_aas_descriptor(self.AAS_ID)
        )

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.AAS_ID), response.headers["Location"])
        self.assertIsNotNone(self.store.get(self.AAS_ID))

    def test_put_updates_when_present_returns_204(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID, id_short="Original"))
        updated = _aas_descriptor(self.AAS_ID, id_short="Updated")

        response = self.format_client.put(f"/shell-descriptors/{base64url_encode(self.AAS_ID)}", obj=updated)

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        stored = self.store.get(self.AAS_ID)
        assert isinstance(stored, AssetAdministrationShellDescriptor)  # make mypy happy
        self.assertEqual("Updated", stored.id_short)

    # ------------------------------------------------------------------ DELETE /shell-descriptors/{aasIdentifier}

    def test_delete_success_returns_204(self) -> None:
        self.store.add(_aas_descriptor(self.AAS_ID))

        response = self.format_client.delete(f"/shell-descriptors/{base64url_encode(self.AAS_ID)}")

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        self.assertIsNone(self.store.get(self.AAS_ID))

    def test_delete_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.delete(f"/shell-descriptors/{base64url_encode(self.UNKNOWN_ID)}"), 404)


# ====================================================================== /shell-descriptors/{aasId}/submodel-descriptors


class SubmodelDescriptorsThroughSuperpathEndpointTest(RegistryEndpointTestBase):
    """Tests for the ``/shell-descriptors/{aasIdentifier}/submodel-descriptors`` routes."""

    __test__ = True

    def setUp(self) -> None:
        super().setUp()
        self.store.add(_aas_descriptor(self.AAS_ID))

    @property
    def _base(self) -> str:
        return f"/shell-descriptors/{base64url_encode(self.AAS_ID)}/submodel-descriptors"

    @property
    def _missing_base(self) -> str:
        return f"/shell-descriptors/{base64url_encode(self.UNKNOWN_ID)}/submodel-descriptors"

    # ------------------------------------------------------------------ GET (collection)

    def test_get_all_empty(self) -> None:
        response = self.format_client.get(self._base)

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    def test_get_all_returns_nested_descriptors(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID_2))

        response = self.format_client.get(self._base)

        self.assert_ok(response)
        self.assertEqual({self.SM_ID, self.SM_ID_2}, set(self.ids(response)))

    def test_get_all_supports_pagination(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID_2))

        pages = self.format_client.get_paginated(self._base, limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    def test_get_all_aas_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.get(self._missing_base), 404)

    # ------------------------------------------------------------------ POST

    def test_post_success(self) -> None:
        response = self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.SM_ID), response.headers["Location"])
        self.assertEqual([self.SM_ID], self.ids(self.format_client.get(self._base)))

    def test_post_conflict_returns_409(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))

        self.assert_error(self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID)), 409)

    def test_post_aas_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.post(self._missing_base, obj=_submodel_descriptor(self.SM_ID)), 404)

    # ------------------------------------------------------------------ GET (single)

    def test_get_by_id_success(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))

        response = self.format_client.get(f"{self._base}/{base64url_encode(self.SM_ID)}")

        self.assert_ok(response)
        self.assertEqual(self.SM_ID, self.format_client.identifier(self.format_client.parse_object(response)))

    def test_get_by_id_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.get(f"{self._base}/{base64url_encode(self.UNKNOWN_ID)}"), 404)

    def test_get_by_id_aas_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.get(f"{self._missing_base}/{base64url_encode(self.SM_ID)}"), 404)

    # ------------------------------------------------------------------ PUT

    def test_put_updates_when_present_returns_204(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID, id_short="Original"))
        updated = _submodel_descriptor(self.SM_ID, id_short="Updated")

        response = self.format_client.put(f"{self._base}/{base64url_encode(self.SM_ID)}", obj=updated)

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        fetched = self.format_client.parse_object(
            self.format_client.get(f"{self._base}/{base64url_encode(self.SM_ID)}")
        )
        self.assertEqual("Updated", self.format_client.field(fetched, "idShort"))

    def test_put_creates_when_absent_returns_201(self) -> None:
        response = self.format_client.put(
            f"{self._base}/{base64url_encode(self.SM_ID)}", obj=_submodel_descriptor(self.SM_ID)
        )

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.SM_ID), response.headers["Location"])
        self.assertEqual([self.SM_ID], self.ids(self.format_client.get(self._base)))

    def test_put_aas_not_found_returns_404(self) -> None:
        self.assert_error(
            self.format_client.put(
                f"{self._missing_base}/{base64url_encode(self.SM_ID)}", obj=_submodel_descriptor(self.SM_ID)
            ),
            404,
        )

    # ------------------------------------------------------------------ DELETE

    def test_delete_success_returns_204(self) -> None:
        self.format_client.post(self._base, obj=_submodel_descriptor(self.SM_ID))

        response = self.format_client.delete(f"{self._base}/{base64url_encode(self.SM_ID)}")

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        self.assertEqual([], self.format_client.parse_collection(self.format_client.get(self._base)))

    def test_delete_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.delete(f"{self._base}/{base64url_encode(self.UNKNOWN_ID)}"), 404)

    def test_delete_aas_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.delete(f"{self._missing_base}/{base64url_encode(self.SM_ID)}"), 404)


# ====================================================================== /submodel-descriptors


class SubmodelDescriptorsEndpointTest(RegistryEndpointTestBase):
    """Tests for the standalone ``/submodel-descriptors`` and ``/submodel-descriptors/{submodelIdentifier}`` routes."""

    __test__ = True

    # ------------------------------------------------------------------ GET /submodel-descriptors

    def test_get_all_empty(self) -> None:
        response = self.format_client.get("/submodel-descriptors")

        self.assert_ok(response)
        self.assertEqual([], self.format_client.parse_collection(response))

    def test_get_all_returns_registered_descriptors(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))
        self.store.add(_submodel_descriptor(self.SM_ID_2))

        response = self.format_client.get("/submodel-descriptors")

        self.assert_ok(response)
        self.assertEqual({self.SM_ID, self.SM_ID_2}, set(self.ids(response)))

    def test_get_all_only_returns_submodel_descriptors(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))
        self.store.add(_aas_descriptor(self.AAS_ID))

        response = self.format_client.get("/submodel-descriptors")

        self.assert_ok(response)
        self.assertEqual([self.SM_ID], self.ids(response))

    def test_get_all_supports_pagination(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))
        self.store.add(_submodel_descriptor(self.SM_ID_2))

        pages = self.format_client.get_paginated("/submodel-descriptors", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    def test_get_all_negative_limit_returns_400(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))

        self.assert_error(self.format_client.get("/submodel-descriptors?limit=-1"), 400)

    # ------------------------------------------------------------------ POST /submodel-descriptors

    def test_post_success(self) -> None:
        response = self.format_client.post("/submodel-descriptors", obj=_submodel_descriptor(self.SM_ID))

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.SM_ID), response.headers["Location"])
        self.assertIsNotNone(self.store.get(self.SM_ID))

    def test_post_missing_id_returns_400(self) -> None:
        response = self.format_client.post(
            "/submodel-descriptors", data=b'{"endpoints": []}', content_type="application/json"
        )

        self.assert_error(response, 400)

    def test_post_conflict_returns_409(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))

        self.assert_error(self.format_client.post("/submodel-descriptors", obj=_submodel_descriptor(self.SM_ID)), 409)

    # ------------------------------------------------------------------ GET /submodel-descriptors/{submodelIdentifier}

    def test_get_by_id_success(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))

        response = self.format_client.get(f"/submodel-descriptors/{base64url_encode(self.SM_ID)}")

        self.assert_ok(response)
        self.assertEqual(self.SM_ID, self.format_client.identifier(self.format_client.parse_object(response)))

    def test_get_by_id_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.get(f"/submodel-descriptors/{base64url_encode(self.UNKNOWN_ID)}"), 404)

    def test_get_by_id_wrong_type_returns_404(self) -> None:
        # A descriptor with this id exists, but it is an AAS descriptor, not a submodel descriptor.
        self.store.add(_aas_descriptor(self.AAS_ID))

        self.assert_error(self.format_client.get(f"/submodel-descriptors/{base64url_encode(self.AAS_ID)}"), 404)

    # ------------------------------------------------------------------ PUT /submodel-descriptors/{submodelIdentifier}

    def test_put_creates_when_absent_returns_201(self) -> None:
        response = self.format_client.put(
            f"/submodel-descriptors/{base64url_encode(self.SM_ID)}", obj=_submodel_descriptor(self.SM_ID)
        )

        self.assertEqual(201, response.status_code, msg=response.get_data(as_text=True))
        self.assertIn(base64url_encode(self.SM_ID), response.headers["Location"])
        self.assertIsNotNone(self.store.get(self.SM_ID))

    def test_put_updates_when_present_returns_204(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID, id_short="Original"))
        updated = _submodel_descriptor(self.SM_ID, id_short="Updated")

        response = self.format_client.put(f"/submodel-descriptors/{base64url_encode(self.SM_ID)}", obj=updated)

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        stored = self.store.get(self.SM_ID)
        assert isinstance(stored, SubmodelDescriptor)  # make mypy happy
        self.assertEqual("Updated", stored.id_short)

    # --------------------------------------------------------------- DELETE /submodel-descriptors/{submodelIdentifier}

    def test_delete_success_returns_204(self) -> None:
        self.store.add(_submodel_descriptor(self.SM_ID))

        response = self.format_client.delete(f"/submodel-descriptors/{base64url_encode(self.SM_ID)}")

        self.assertEqual(204, response.status_code, msg=response.get_data(as_text=True))
        self.assertIsNone(self.store.get(self.SM_ID))

    def test_delete_not_found_returns_404(self) -> None:
        self.assert_error(self.format_client.delete(f"/submodel-descriptors/{base64url_encode(self.UNKNOWN_ID)}"), 404)
