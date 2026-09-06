from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
    create_example_concept_description,
)

from ..format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from .test_base import RepositoryEndpointTestBase


@inject_format_clients
class ConceptDescriptionsEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the implemented ``/concept-descriptions`` routes of
    :class:`~app.interfaces.repository.WSGIApp`.

    Bodies are written once against the format-agnostic ``format_client`` helper. For each test two
    variants are generated where the :class:`~..format_utils.JsonFormatClient` and
    :class:`~..format_utils.XmlFormatClient` are injected respectively.
    """

    __test__ = True

    EXAMPLE_ID = "https://example.org/Test_ConceptDescription_Missing"
    SECOND_ID = "https://example.org/Test_ConceptDescription_Second"

    def two_concept_descriptions_store(self) -> model.DictIdentifiableStore:
        store: model.DictIdentifiableStore = model.DictIdentifiableStore()
        store.add(create_example_concept_description())
        second = create_example_concept_description()
        second.id = self.SECOND_ID
        second.id_short = "SecondConceptDescription"
        store.add(second)
        return store

    def _get_concept_description_ids(self, format_client: FormatClient, query: str) -> set:
        response = format_client.get(f"/concept-descriptions?{query}")
        self.assert_ok(response)
        return {format_client.identifier(node) for node in format_client.parse_collection(response)}

    # ------------------------------------------------------------------ GET /concept-descriptions

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_get(self, format_client: FormatClient):
        self.object_store.update(self.two_concept_descriptions_store())

        response = format_client.get("/concept-descriptions")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_get_empty(self, format_client: FormatClient):
        response = format_client.get("/concept-descriptions")

        self.assert_ok(response)
        self.assertEqual(0, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_get_only_returns_concept_descriptions(self, format_client: FormatClient):
        # The object store is shared between the shell/submodel/concept-description repositories, so the
        # collection endpoint has to filter by type.
        self.object_store.add(create_example_concept_description())
        self.object_store.add(create_example_asset_administration_shell())

        ids = self._get_concept_description_ids(format_client, "")

        self.assertEqual({self.EXAMPLE_ID}, ids)

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_concept_descriptions_store())

        pages = format_client.get_paginated("/concept-descriptions", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ POST /concept-descriptions

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_post_success(self, format_client: FormatClient):
        example_cd = create_example_concept_description()

        response = format_client.post("/concept-descriptions", obj=example_cd)

        self.assertEqual(201, response.status_code)
        self.assertIn(base64url_encode(example_cd.id), response.headers["Location"])
        self.assertIsNotNone(self.object_store.get(example_cd.id, None))

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_post_bad(self, format_client: FormatClient):
        example_cd = create_example_concept_description()
        example_cd.id = None  # type: ignore

        response = format_client.post("/concept-descriptions", obj=example_cd)

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_concept_descriptions_post_conflict(self, format_client: FormatClient):
        example_cd = create_example_concept_description()
        self.object_store.add(example_cd)

        response = format_client.post("/concept-descriptions", obj=example_cd)

        self.assert_error(response, 409)

    # ------------------------------------------------------------------ GET /concept-descriptions/<concept_id>

    @with_json_client
    @with_xml_client
    def test_concept_description_get_success(self, format_client: FormatClient):
        self.object_store.update(self.two_concept_descriptions_store())

        response = format_client.get(f"/concept-descriptions/{base64url_encode(self.EXAMPLE_ID)}")

        self.assert_ok(response)
        self.assertEqual(self.EXAMPLE_ID, format_client.identifier(format_client.parse_object(response)))

    @with_json_client
    @with_xml_client
    def test_concept_description_get_not_found(self, format_client: FormatClient):
        response = format_client.get(
            f"/concept-descriptions/{base64url_encode('https://example.org/unknown')}"
        )

        self.assert_error(response, 404)

    @with_json_client
    @with_xml_client
    def test_concept_description_get_wrong_type_returns_404(self, format_client: FormatClient):
        # An Identifiable with this id exists, but it is a shell, not a ConceptDescription.
        shell = create_example_asset_administration_shell()
        self.object_store.add(shell)

        response = format_client.get(f"/concept-descriptions/{base64url_encode(shell.id)}")

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ PUT /concept-descriptions/<concept_id>

    @with_json_client
    @with_xml_client
    def test_concept_description_put_success(self, format_client: FormatClient):
        self.object_store.add(create_example_concept_description())
        updated_cd = create_example_concept_description()
        updated_cd.id_short = "UpdatedIdShort"

        response = format_client.put(
            f"/concept-descriptions/{base64url_encode(updated_cd.id)}", obj=updated_cd
        )

        self.assertEqual(204, response.status_code)
        retrieved_cd = self.object_store.get(updated_cd.id, None)
        self.assertIsInstance(retrieved_cd, model.ConceptDescription)
        assert isinstance(retrieved_cd, model.ConceptDescription)  # make mypy happy
        self.assertEqual("UpdatedIdShort", retrieved_cd.id_short)

    @with_json_client
    @with_xml_client
    def test_concept_description_put_not_found(self, format_client: FormatClient):
        updated_cd = create_example_concept_description()
        updated_cd.id = "https://example.org/unknown"

        response = format_client.put(
            f"/concept-descriptions/{base64url_encode(updated_cd.id)}", obj=updated_cd
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ DELETE /concept-descriptions/<concept_id>

    @with_json_client
    @with_xml_client
    def test_concept_description_delete_success(self, format_client: FormatClient):
        example_cd = create_example_concept_description()
        self.object_store.add(example_cd)

        response = format_client.delete(f"/concept-descriptions/{base64url_encode(example_cd.id)}")

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self.object_store.get(example_cd.id, None))

    @with_json_client
    @with_xml_client
    def test_concept_description_delete_not_found(self, format_client: FormatClient):
        response = format_client.delete(
            f"/concept-descriptions/{base64url_encode('https://example.org/unknown')}"
        )

        self.assert_error(response, 404)
