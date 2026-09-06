import base64
import json
from typing import Iterable

from app.util.converters import base64url_encode
from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
    create_example_submodel,
)

from ..format_utils import (
    FormatClient,
    inject_format_clients,
    with_json_client,
    with_xml_client,
)
from .test_base import RepositoryEndpointTestBase


def _encode_name_value_pair(name: str, value: str) -> str:
    payload = json.dumps({"name": name, "value": value})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _encode_global_asset_id(value: str) -> str:
    return _encode_name_value_pair("globalAssetId", value)


def _encode_specific_asset_id(specific_asset_id: model.SpecificAssetId) -> str:
    return _encode_name_value_pair("specificAssetId", json.dumps(specific_asset_id, cls=AASToJsonEncoder))


@inject_format_clients
class ShellsEndpointsTest(RepositoryEndpointTestBase):
    """
    Endpoint tests for the implemented ``/shells`` routes of :class:`~app.interfaces.repository.WSGIApp`.

    Bodies are written once against the format-agnostic ``format_client`` helper.
    For each test two variants are generated where the :class:`~..format_utils.JsonFormatClient` and
    :class:`~..format_utils.XmlFormatClient` are injected respectively.
    """

    __test__ = True

    # ------------------------------------------------------------------ GET /shells

    @with_json_client
    @with_xml_client
    def test_shells_get(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())

        response = format_client.get("/shells")

        self.assert_ok(response)
        self.assertEqual(2, len(format_client.parse_collection(response)))

    @with_json_client
    @with_xml_client
    def test_shells_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())

        pages = format_client.get_paginated("/shells", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ GET /shells?idShort=...&assetIds=...

    @staticmethod
    def _specific_asset_id(name: str, value: str, subject: str) -> model.SpecificAssetId:
        return model.SpecificAssetId(
            name=name,
            value=value,
            external_subject_id=model.ExternalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, subject),)),
        )

    @staticmethod
    def _shell(
        id_: str,
        id_short: str,
        global_asset_id: str,
        specific_asset_ids: Iterable[model.SpecificAssetId] = (),
    ) -> model.AssetAdministrationShell:
        return model.AssetAdministrationShell(
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=global_asset_id,
                specific_asset_id=specific_asset_ids,
            ),
            id_=id_,
            id_short=id_short,
        )

    def shells_for_filtering_store(self):
        store = model.DictIdentifiableStore()
        store.add(
            self._shell(
                "https://example.org/shell-alpha",
                "Alpha",
                "https://example.org/asset-alpha",
                [self._specific_asset_id("Serial", "111", "https://example.org/subject-alpha")],
            )
        )
        store.add(
            self._shell(
                "https://example.org/shell-beta",
                "Beta",
                "https://example.org/asset-beta",
                [
                    self._specific_asset_id("Serial", "222", "https://example.org/subject-beta"),
                    self._specific_asset_id("Batch", "xyz", "https://example.org/subject-beta"),
                ],
            )
        )
        store.add(self._shell("https://example.org/shell-gamma", "Alpha", "https://example.org/asset-alpha"))
        return store

    def _get_shell_ids(self, format_client: FormatClient, query: str) -> set:
        response = format_client.get(f"/shells?{query}")
        self.assert_ok(response)
        return {format_client.identifier(node) for node in format_client.parse_collection(response)}

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_id_short(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())

        ids = self._get_shell_ids(format_client, "idShort=Alpha")

        self.assertEqual(
            {"https://example.org/shell-alpha", "https://example.org/shell-gamma"}, ids
        )

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_id_short_no_match(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())

        ids = self._get_shell_ids(format_client, "idShort=Unknown")

        self.assertEqual(set(), ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_global_asset_id(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())

        query = f"assetIds={_encode_global_asset_id('https://example.org/asset-alpha')}"
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual(
            {"https://example.org/shell-alpha", "https://example.org/shell-gamma"}, ids
        )

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_multiple_global_asset_ids_is_or(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())

        query = "&".join(
            [
                f"assetIds={_encode_global_asset_id('https://example.org/asset-beta')}",
                f"assetIds={_encode_global_asset_id('https://example.org/nonexistent-asset')}",
            ]
        )
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual({"https://example.org/shell-beta"}, ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_specific_asset_id(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())
        specific_id = self._specific_asset_id("Serial", "222", "https://example.org/subject-beta")

        query = f"assetIds={_encode_specific_asset_id(specific_id)}"
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual({"https://example.org/shell-beta"}, ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_multiple_specific_asset_ids_requires_all(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())
        serial = self._specific_asset_id("Serial", "222", "https://example.org/subject-beta")
        batch = self._specific_asset_id("Batch", "xyz", "https://example.org/subject-beta")

        query = "&".join(
            [f"assetIds={_encode_specific_asset_id(serial)}", f"assetIds={_encode_specific_asset_id(batch)}"]
        )
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual({"https://example.org/shell-beta"}, ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_specific_asset_ids_from_different_shells_matches_none(
        self, format_client: FormatClient
    ):
        self.object_store.update(self.shells_for_filtering_store())
        alpha_specific_id = self._specific_asset_id("Serial", "111", "https://example.org/subject-alpha")
        beta_specific_id = self._specific_asset_id("Serial", "222", "https://example.org/subject-beta")

        query = "&".join(
            [
                f"assetIds={_encode_specific_asset_id(alpha_specific_id)}",
                f"assetIds={_encode_specific_asset_id(beta_specific_id)}",
            ]
        )
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual(set(), ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_specific_and_global_asset_id_is_and(self, format_client: FormatClient):
        # shell-beta has this specificAssetId, but not this globalAssetId (that's shell-alpha's) -- combining
        # both must AND the two conditions together, so neither shell matches.
        self.object_store.update(self.shells_for_filtering_store())
        beta_specific_id = self._specific_asset_id("Serial", "222", "https://example.org/subject-beta")

        query = "&".join(
            [
                f"assetIds={_encode_specific_asset_id(beta_specific_id)}",
                f"assetIds={_encode_global_asset_id('https://example.org/asset-alpha')}",
            ]
        )
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual(set(), ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_id_short_and_asset_ids_is_and(self, format_client: FormatClient):
        # idShort=Alpha matches shell-alpha and shell-gamma, but only shell-alpha carries this specificAssetId.
        self.object_store.update(self.shells_for_filtering_store())
        alpha_specific_id = self._specific_asset_id("Serial", "111", "https://example.org/subject-alpha")

        query = f"idShort=Alpha&assetIds={_encode_specific_asset_id(alpha_specific_id)}"
        ids = self._get_shell_ids(format_client, query)

        self.assertEqual({"https://example.org/shell-alpha"}, ids)

    @with_json_client
    @with_xml_client
    def test_shells_get_filter_by_malformed_asset_id_returns_400(self, format_client: FormatClient):
        self.object_store.update(self.shells_for_filtering_store())
        malformed = base64.urlsafe_b64encode(json.dumps({"name": "globalAssetId"}).encode()).decode()

        response = format_client.get(f"/shells?assetIds={malformed}")

        self.assert_error(response, 400)

    # ------------------------------------------------------------------ POST /shells

    @with_json_client
    @with_xml_client
    def test_shells_post_success(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()

        response = format_client.post("/shells", obj=example_shell)

        self.assertEqual(201, response.status_code)
        self.assertIsNotNone(self.object_store.get(example_shell.id, None))

    @with_json_client
    @with_xml_client
    def test_shells_post_bad(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        example_shell.id = None  # type: ignore

        response = format_client.post("/shells", obj=example_shell)

        self.assert_error(response, 400)

    @with_json_client
    @with_xml_client
    def test_shells_post_conflict(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)

        response = format_client.post("/shells", obj=example_shell)

        self.assert_error(response, 409)

    # ------------------------------------------------------------------ GET /shells/$reference

    @with_json_client
    @with_xml_client
    def test_shells_reference_get(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())
        example_shell = next(iter(self.object_store))

        response = format_client.get("/shells/$reference")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertEqual(2, len(references))
        self.assertIn(example_shell.id, [format_client.reference_target(ref) for ref in references])

    @with_json_client
    @with_xml_client
    def test_shells_reference_get_supports_pagination(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())

        pages = format_client.get_paginated("/shells/$reference", limit=1, max_pages=2)

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ GET /shells/<aas_id>

    @with_json_client
    @with_xml_client
    def test_shell_get_success(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())
        example_shell = next(iter(self.object_store))

        response = format_client.get(f"/shells/{base64url_encode(example_shell.id)}")

        self.assert_ok(response)
        self.assertEqual(example_shell.id, format_client.identifier(format_client.parse_object(response)))

    @with_json_client
    @with_xml_client
    def test_shell_get_not_found(self, format_client: FormatClient):
        response = format_client.get(f"/shells/{base64url_encode('https://example.org/unknown')}")

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ GET /shells/<aas_id>/$reference

    @with_json_client
    @with_xml_client
    def test_shell_reference_get(self, format_client: FormatClient):
        self.object_store.update(self.two_shells_store())
        example_shell = next(iter(self.object_store))

        response = format_client.get(f"/shells/{base64url_encode(example_shell.id)}/$reference")

        self.assert_ok(response)
        self.assertEqual(example_shell.id, format_client.reference_target(format_client.parse_object(response)))

    # ------------------------------------------------------------------ PUT /shells/<aas_id>

    @with_json_client
    @with_xml_client
    def test_shell_put_success(self, format_client: FormatClient):
        self.object_store.add(create_example_asset_administration_shell())
        updated_shell = create_example_asset_administration_shell()
        updated_shell.id_short = "UpdatedIdShort"

        response = format_client.put(f"/shells/{base64url_encode(updated_shell.id)}", obj=updated_shell)

        self.assertEqual(204, response.status_code)
        retrieved_shell = self.object_store.get(updated_shell.id, None)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy
        self.assertEqual("UpdatedIdShort", retrieved_shell.id_short)

    @with_json_client
    @with_xml_client
    def test_shell_put_not_found(self, format_client: FormatClient):
        updated_shell = create_example_asset_administration_shell()

        response = format_client.put(
            f"/shells/{base64url_encode('https://example.org/unknown')}", obj=updated_shell
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ DELETE /shells/<aas_id>

    @with_json_client
    @with_xml_client
    def test_shell_delete_success(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)

        response = format_client.delete(f"/shells/{base64url_encode(example_shell.id)}")

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self.object_store.get(example_shell.id, None))

    @with_json_client
    @with_xml_client
    def test_shell_delete_not_found(self, format_client: FormatClient):
        response = format_client.delete(f"/shells/{base64url_encode('https://example.org/unknown')}")

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ GET /shells/<aas_id>/asset-information

    @with_json_client
    @with_xml_client
    def test_shell_asset_information_get(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)

        response = format_client.get(f"/shells/{base64url_encode(example_shell.id)}/asset-information")

        self.assert_ok(response)
        self.assertEqual(
            example_shell.asset_information.global_asset_id,
            format_client.field(format_client.parse_object(response), "globalAssetId"),
        )

    # ------------------------------------------------------------------ PUT /shells/<aas_id>/asset-information

    @with_json_client
    @with_xml_client
    def test_shell_asset_information_put(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        new_asset_information = model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id="http://example.org/changed_asset",
        )

        response = format_client.put(
            f"/shells/{base64url_encode(example_shell.id)}/asset-information",
            obj=new_asset_information,
        )

        self.assertEqual(204, response.status_code)
        retrieved_shell = self.object_store.get(example_shell.id)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy
        self.assertEqual(
            "http://example.org/changed_asset",
            retrieved_shell.asset_information.global_asset_id,
        )

    # ------------------------------------------------------------------ GET /shells/<aas_id>/submodel-refs

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_get(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)

        response = format_client.get(f"/shells/{base64url_encode(example_shell.id)}/submodel-refs")

        self.assert_ok(response)
        references = format_client.parse_collection(response)
        self.assertEqual(1, len(references))
        self.assertEqual(
            "https://example.org/Test_Submodel_Missing", format_client.reference_target(references[0])
        )

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_get_supports_pagination(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        example_shell.submodel.add(
            model.ModelReference(
                (model.Key(model.KeyTypes.SUBMODEL, "https://example.org/Second_Submodel_Ref"),), model.Submodel
            )
        )
        self.object_store.add(example_shell)

        pages = format_client.get_paginated(
            f"/shells/{base64url_encode(example_shell.id)}/submodel-refs", limit=1, max_pages=2
        )

        self.assertEqual([1, 1], [len(page) for page in pages])

    # ------------------------------------------------------------------ POST /shells/<aas_id>/submodel-refs

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_post_success(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        new_ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "https://example.org/NewSubmodel"),), model.Submodel
        )

        response = format_client.post(f"/shells/{base64url_encode(example_shell.id)}/submodel-refs", obj=new_ref)

        self.assertEqual(201, response.status_code)
        retrieved_shell = self.object_store.get(example_shell.id)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy
        identifiers = {ref.get_identifier() for ref in retrieved_shell.submodel}
        self.assertIn("https://example.org/NewSubmodel", identifiers)

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_post_conflict(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        existing_ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "https://example.org/Test_Submodel_Missing"),), model.Submodel
        )

        response = format_client.post(
            f"/shells/{base64url_encode(example_shell.id)}/submodel-refs", obj=existing_ref
        )

        self.assert_error(response, 409)

    # ------------------------------------------------------------------ DELETE /shells/<aas_id>/submodel-refs/<sm_id>

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_delete_success(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        submodel_id = "https://example.org/Test_Submodel_Missing"

        response = format_client.delete(
            f"/shells/{base64url_encode(example_shell.id)}/submodel-refs/{base64url_encode(submodel_id)}"
        )

        self.assertEqual(204, response.status_code)
        retrieved_shell = self.object_store.get(example_shell.id)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy
        self.assertEqual(0, len(list(retrieved_shell.submodel)))

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_delete_not_found(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)

        response = format_client.delete(
            f"/shells/{base64url_encode(example_shell.id)}/submodel-refs/"
            f"{base64url_encode('https://example.org/unknown')}"
        )

        self.assert_error(response, 404)

    # ------------------------------------------------------------------ PUT /shells/<aas_id>/submodels/<sm_id>

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_submodel_put(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        self.object_store.add(create_example_submodel())
        updated_submodel = create_example_submodel()
        updated_submodel.id_short = "UpdatedSubmodel"

        response = format_client.put(
            f"/shells/{base64url_encode(example_shell.id)}/submodels/{base64url_encode(updated_submodel.id)}",
            obj=updated_submodel,
        )

        self.assertEqual(204, response.status_code)
        retrieved_sm = self.object_store.get(updated_submodel.id)
        self.assertIsInstance(retrieved_sm, model.Submodel)
        assert isinstance(retrieved_sm, model.Submodel)  # make mypy happy
        self.assertEqual("UpdatedSubmodel", retrieved_sm.id_short)

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_submodel_put_changed_id_success(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        self.object_store.add(create_example_submodel())
        updated_submodel = create_example_submodel()
        old_sm_id = updated_submodel.id
        updated_submodel.id = "https://example.org/Test_Submodel_Updated"

        response = format_client.put(
            f"/shells/{base64url_encode(example_shell.id)}/submodels/{base64url_encode(old_sm_id)}",
            obj=updated_submodel,
        )

        self.assertEqual(204, response.status_code)
        retrieved_shell = self.object_store.get(example_shell.id)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy

        self.assertIn(model.ModelReference.from_referable(updated_submodel), retrieved_shell.submodel)
        self.assertNotIn(model.ModelReference.from_referable(create_example_submodel()), retrieved_shell.submodel)

    # ------------------------------------------------------------------ DELETE /shells/<aas_id>/submodels/<sm_id>

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_submodel_delete(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        example_submodel = create_example_submodel()
        self.object_store.add(example_submodel)

        response = format_client.delete(
            f"/shells/{base64url_encode(example_shell.id)}/submodels/{base64url_encode(example_submodel.id)}"
        )

        self.assertEqual(204, response.status_code)
        self.assertIsNone(self.object_store.get(example_submodel.id, None))
        retrieved_shell = self.object_store.get(example_shell.id)
        self.assertIsInstance(retrieved_shell, model.AssetAdministrationShell)
        assert isinstance(retrieved_shell, model.AssetAdministrationShell)  # make mypy happy
        self.assertEqual(0, len(list(retrieved_shell.submodel)))

    # ------------------------------------------------------------------ /shells/<aas_id>/submodels/<sm_id> redirect

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_submodel_redirect(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        submodel_id = "https://example.org/Test_Submodel_Missing"

        response = format_client.get(
            f"/shells/{base64url_encode(example_shell.id)}/submodels/{base64url_encode(submodel_id)}"
        )

        self.assertEqual(307, response.status_code)
        self.assertIn(f"/submodels/{base64url_encode(submodel_id)}", response.headers["Location"])

    @with_json_client
    @with_xml_client
    def test_shell_submodel_refs_submodel_redirect_with_path(self, format_client: FormatClient):
        example_shell = create_example_asset_administration_shell()
        self.object_store.add(example_shell)
        submodel_id = "https://example.org/Test_Submodel_Missing"

        response = format_client.get(
            f"/shells/{base64url_encode(example_shell.id)}/submodels/{base64url_encode(submodel_id)}"
            f"/submodel-elements"
        )

        self.assertEqual(307, response.status_code)
        self.assertTrue(response.headers["Location"].endswith("/submodel-elements"))
