# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements the "Specification of the Asset Administration Shell Part 2 Application Programming Interfaces".
However, several features and routes are currently not supported:

1. Correlation ID: Not implemented because it was deemed unnecessary for this server.

2. Extent Parameter (`withBlobValue/withoutBlobValue`):
   Not implemented due to the lack of support in JSON/XML serialization.

3. Route `/shells/{aasIdentifier}/asset-information/thumbnail`: Not implemented because the specification lacks clarity.

4. Serialization and Description Routes:
   - `/serialization`
   - `/description`
   These routes are not implemented at this time.

5. Value, Path, and PATCH Routes:
   - All `/…/value$`, `/…/path$`, and `PATCH` routes are currently not implemented.

6. Operation Invocation Routes: The following routes are not implemented because operation invocation
   is not yet supported by the `basyx-python-sdk`:
   - `POST /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/invoke`
   - `POST /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/invoke/$value`
   - `POST /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/invoke-async`
   - `POST /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/invoke-async/$value`
   - `GET /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/operation-status/{handleId}`
   - `GET /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/operation-results/{handleId}`
   - `GET /submodels/{submodelIdentifier}/submodel-elements/{idShortPath}/operation-results/{handleId}/$value`
"""

import io
import json
from typing import Type, Iterator, List, Dict, Union, Callable, Tuple, Optional

import werkzeug.exceptions
import werkzeug.routing
import werkzeug.utils
from werkzeug import Response, Request
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from werkzeug.routing import Submount, Rule, MapAdapter

from basyx.aas import model
from basyx.aas.adapter import aasx
from util.converters import Base64URLConverter, IdShortPathConverter, base64url_decode
from .base import ObjectStoreWSGIApp, APIResponse, is_stripped_request, HTTPApiDecoder, T


class WSGIApp(ObjectStoreWSGIApp):
    def __init__(self, object_store: model.AbstractObjectStore, file_store: aasx.AbstractSupplementaryFileContainer,
                 base_path: str = "/api/v3.0"):
        self.object_store: model.AbstractObjectStore = object_store
        self.file_store: aasx.AbstractSupplementaryFileContainer = file_store
        self.url_map = werkzeug.routing.Map([
            Submount(base_path, [
                Rule("/serialization", methods=["GET"], endpoint=self.not_implemented),
                Rule("/description", methods=["GET"], endpoint=self.not_implemented),
                Rule("/shells", methods=["GET"], endpoint=self.get_aas_all),
                Rule("/shells", methods=["POST"], endpoint=self.post_aas),
                Submount("/shells", [
                    Rule("/$reference", methods=["GET"], endpoint=self.get_aas_all_reference),
                    Rule("/<base64url:aas_id>", methods=["GET"], endpoint=self.get_aas),
                    Rule("/<base64url:aas_id>", methods=["PUT"], endpoint=self.put_aas),
                    Rule("/<base64url:aas_id>", methods=["DELETE"], endpoint=self.delete_aas),
                    Submount("/<base64url:aas_id>", [
                        Rule("/$reference", methods=["GET"], endpoint=self.get_aas_reference),
                        Rule("/asset-information", methods=["GET"], endpoint=self.get_aas_asset_information),
                        Rule("/asset-information", methods=["PUT"], endpoint=self.put_aas_asset_information),
                        Rule("/asset-information/thumbnail", methods=["GET", "PUT", "DELETE"],
                             endpoint=self.not_implemented),
                        Rule("/submodel-refs", methods=["GET"], endpoint=self.get_aas_submodel_refs),
                        Rule("/submodel-refs", methods=["POST"], endpoint=self.post_aas_submodel_refs),
                        Rule("/submodel-refs/<base64url:submodel_id>", methods=["DELETE"],
                             endpoint=self.delete_aas_submodel_refs_specific),
                        Submount("/submodels", [
                            Rule("/<base64url:submodel_id>", methods=["PUT"],
                                 endpoint=self.put_aas_submodel_refs_submodel),
                            Rule("/<base64url:submodel_id>", methods=["DELETE"],
                                 endpoint=self.delete_aas_submodel_refs_submodel),
                            Rule("/<base64url:submodel_id>", endpoint=self.aas_submodel_refs_redirect),
                            Rule("/<base64url:submodel_id>/<path:path>", endpoint=self.aas_submodel_refs_redirect)
                        ])
                    ])
                ]),
                Rule("/submodels", methods=["GET"], endpoint=self.get_submodel_all),
                Rule("/submodels", methods=["POST"], endpoint=self.post_submodel),
                Submount("/submodels", [
                    Rule("/$metadata", methods=["GET"], endpoint=self.get_submodel_all_metadata),
                    Rule("/$reference", methods=["GET"], endpoint=self.get_submodel_all_reference),
                    Rule("/$value", methods=["GET"], endpoint=self.not_implemented),
                    Rule("/$path", methods=["GET"], endpoint=self.not_implemented),
                    Rule("/<base64url:submodel_id>", methods=["GET"], endpoint=self.get_submodel),
                    Rule("/<base64url:submodel_id>", methods=["PUT"], endpoint=self.put_submodel),
                    Rule("/<base64url:submodel_id>", methods=["DELETE"], endpoint=self.delete_submodel),
                    Rule("/<base64url:submodel_id>", methods=["PATCH"], endpoint=self.not_implemented),
                    Submount("/<base64url:submodel_id>", [
                        Rule("/$metadata", methods=["GET"], endpoint=self.get_submodels_metadata),
                        Rule("/$metadata", methods=["PATCH"], endpoint=self.not_implemented),
                        Rule("/$value", methods=["GET"], endpoint=self.not_implemented),
                        Rule("/$value", methods=["PATCH"], endpoint=self.not_implemented),
                        Rule("/$reference", methods=["GET"], endpoint=self.get_submodels_reference),
                        Rule("/$path", methods=["GET"], endpoint=self.not_implemented),
                        Rule("/submodel-elements", methods=["GET"], endpoint=self.get_submodel_submodel_elements),
                        Rule("/submodel-elements", methods=["POST"],
                             endpoint=self.post_submodel_submodel_elements_id_short_path),
                        Submount("/submodel-elements", [
                            Rule("/$metadata", methods=["GET"], endpoint=self.get_submodel_submodel_elements_metadata),
                            Rule("/$reference", methods=["GET"],
                                 endpoint=self.get_submodel_submodel_elements_reference),
                            Rule("/$value", methods=["GET"], endpoint=self.not_implemented),
                            Rule("/$path", methods=["GET"], endpoint=self.not_implemented),
                            Rule("/<id_short_path:id_shorts>", methods=["GET"],
                                 endpoint=self.get_submodel_submodel_elements_id_short_path),
                            Rule("/<id_short_path:id_shorts>", methods=["POST"],
                                 endpoint=self.post_submodel_submodel_elements_id_short_path),
                            Rule("/<id_short_path:id_shorts>", methods=["PUT"],
                                 endpoint=self.put_submodel_submodel_elements_id_short_path),
                            Rule("/<id_short_path:id_shorts>", methods=["DELETE"],
                                 endpoint=self.delete_submodel_submodel_elements_id_short_path),
                            Rule("/<id_short_path:id_shorts>", methods=["PATCH"], endpoint=self.not_implemented),
                            Submount("/<id_short_path:id_shorts>", [
                                Rule("/$metadata", methods=["GET"],
                                     endpoint=self.get_submodel_submodel_elements_id_short_path_metadata),
                                Rule("/$metadata", methods=["PATCH"], endpoint=self.not_implemented),
                                Rule("/$reference", methods=["GET"],
                                     endpoint=self.get_submodel_submodel_elements_id_short_path_reference),
                                Rule("/$value", methods=["GET"], endpoint=self.not_implemented),
                                Rule("/$value", methods=["PATCH"], endpoint=self.not_implemented),
                                Rule("/$path", methods=["GET"], endpoint=self.not_implemented),
                                Rule("/attachment", methods=["GET"],
                                     endpoint=self.get_submodel_submodel_element_attachment),
                                Rule("/attachment", methods=["PUT"],
                                     endpoint=self.put_submodel_submodel_element_attachment),
                                Rule("/attachment", methods=["DELETE"],
                                     endpoint=self.delete_submodel_submodel_element_attachment),
                                Rule("/invoke", methods=["POST"], endpoint=self.not_implemented),
                                Rule("/invoke/$value", methods=["POST"], endpoint=self.not_implemented),
                                Rule("/invoke-async", methods=["POST"], endpoint=self.not_implemented),
                                Rule("/invoke-async/$value", methods=["POST"], endpoint=self.not_implemented),
                                Rule("/operation-status/<base64url:handleId>", methods=["GET"],
                                     endpoint=self.not_implemented),
                                Submount("/operation-results", [
                                    Rule("/<base64url:handleId>", methods=["GET"], endpoint=self.not_implemented),
                                    Rule("/<base64url:handleId>/$value", methods=["GET"], endpoint=self.not_implemented)
                                ]),
                                Rule("/qualifiers", methods=["GET"],
                                     endpoint=self.get_submodel_submodel_element_qualifiers),
                                Rule("/qualifiers", methods=["POST"],
                                     endpoint=self.post_submodel_submodel_element_qualifiers),
                                Submount("/qualifiers", [
                                    Rule("/<base64url:qualifier_type>", methods=["GET"],
                                         endpoint=self.get_submodel_submodel_element_qualifiers),
                                    Rule("/<base64url:qualifier_type>", methods=["PUT"],
                                         endpoint=self.put_submodel_submodel_element_qualifiers),
                                    Rule("/<base64url:qualifier_type>", methods=["DELETE"],
                                         endpoint=self.delete_submodel_submodel_element_qualifiers)
                                ])
                            ])
                        ]),
                        Rule("/qualifiers", methods=["GET"], endpoint=self.get_submodel_submodel_element_qualifiers),
                        Rule("/qualifiers", methods=["POST"], endpoint=self.post_submodel_submodel_element_qualifiers),
                        Submount("/qualifiers", [
                            Rule("/<base64url:qualifier_type>", methods=["GET"],
                                 endpoint=self.get_submodel_submodel_element_qualifiers),
                            Rule("/<base64url:qualifier_type>", methods=["PUT"],
                                 endpoint=self.put_submodel_submodel_element_qualifiers),
                            Rule("/<base64url:qualifier_type>", methods=["DELETE"],
                                 endpoint=self.delete_submodel_submodel_element_qualifiers)
                        ])
                    ])
                ]),
                Rule("/concept-descriptions", methods=["GET"], endpoint=self.get_concept_description_all),
                Rule("/concept-descriptions", methods=["POST"], endpoint=self.post_concept_description),
                Submount("/concept-descriptions", [
                    Rule("/<base64url:concept_id>", methods=["GET"], endpoint=self.get_concept_description),
                    Rule("/<base64url:concept_id>", methods=["PUT"], endpoint=self.put_concept_description),
                    Rule("/<base64url:concept_id>", methods=["DELETE"], endpoint=self.delete_concept_description),
                ]),
            ])
        ], converters={
            "base64url": Base64URLConverter,
            "id_short_path": IdShortPathConverter
        }, strict_slashes=False)

    def _resolve_reference(self, reference: model.ModelReference[model.base._RT]) -> model.base._RT:
        try:
            return reference.resolve(self.object_store)
        except (KeyError, TypeError, model.UnexpectedTypeError) as e:
            raise werkzeug.exceptions.InternalServerError(str(e)) from e

    @classmethod
    def _get_nested_submodel_element(cls, namespace: model.UniqueIdShortNamespace, id_shorts: List[str]) \
            -> model.SubmodelElement:
        if not id_shorts:
            raise ValueError("No id_shorts specified!")

        try:
            ret = namespace.get_referable(id_shorts)
        except KeyError as e:
            raise NotFound(e.args[0])
        except (TypeError, ValueError) as e:
            raise BadRequest(e.args[0])

        if not isinstance(ret, model.SubmodelElement):
            raise BadRequest(f"{ret!r} is not a submodel element!")
        return ret

    def _get_submodel_or_nested_submodel_element(self, url_args: Dict) -> Union[model.Submodel, model.SubmodelElement]:
        submodel = self._get_submodel(url_args)
        id_shorts: List[str] = url_args.get("id_shorts", [])
        try:
            return self._get_nested_submodel_element(submodel, id_shorts)
        except ValueError:
            return submodel

    @classmethod
    def _expect_namespace(cls, obj: object, needle: str) -> model.UniqueIdShortNamespace:
        if not isinstance(obj, model.UniqueIdShortNamespace):
            raise BadRequest(f"{obj!r} is not a namespace, can't locate {needle}!")
        return obj

    @classmethod
    def _namespace_submodel_element_op(cls, namespace: model.UniqueIdShortNamespace, op: Callable[[str], T], arg: str) \
            -> T:
        try:
            return op(arg)
        except KeyError as e:
            raise NotFound(f"Submodel element with id_short {arg} not found in {namespace!r}") from e

    @classmethod
    def _qualifiable_qualifier_op(cls, qualifiable: model.Qualifiable, op: Callable[[str], T], arg: str) -> T:
        try:
            return op(arg)
        except KeyError as e:
            raise NotFound(f"Qualifier with type {arg!r} not found in {qualifiable!r}") from e

    @classmethod
    def _get_submodel_reference(cls, aas: model.AssetAdministrationShell, submodel_id: model.NameType) \
            -> model.ModelReference[model.Submodel]:
        # TODO: this is currently O(n), could be O(1) as aas.submodel, but keys would have to precisely match, as they
        #  are hashed including their KeyType
        for ref in aas.submodel:
            if ref.get_identifier() == submodel_id:
                return ref
        raise NotFound(f"The AAS {aas!r} doesn't have a submodel reference to {submodel_id!r}!")

    def _get_shells(self, request: Request) -> Tuple[Iterator[model.AssetAdministrationShell], int]:
        aas: Iterator[model.AssetAdministrationShell] = self._get_all_obj_of_type(model.AssetAdministrationShell)

        id_short = request.args.get("idShort")
        if id_short is not None:
            aas = filter(lambda shell: shell.id_short == id_short, aas)

        asset_ids = request.args.getlist("assetIds")

        if asset_ids:
            specific_asset_ids = []
            global_asset_ids = []

            for asset_id in asset_ids:
                asset_id_json = base64url_decode(asset_id)
                asset_dict = json.loads(asset_id_json)
                name = asset_dict["name"]
                value = asset_dict["value"]

                if name == "specificAssetId":
                    decoded_specific_id = HTTPApiDecoder.json_list(value, model.SpecificAssetId,
                                                                   False, True)[0]
                    specific_asset_ids.append(decoded_specific_id)
                elif name == "globalAssetId":
                    global_asset_ids.append(value)

            # Filter AAS based on both SpecificAssetIds and globalAssetIds
            aas = filter(lambda shell: (
                    (not specific_asset_ids or all(specific_asset_id in shell.asset_information.specific_asset_id
                                                   for specific_asset_id in specific_asset_ids)) and
                    (len(global_asset_ids) <= 1 and
                        (not global_asset_ids or shell.asset_information.global_asset_id in global_asset_ids))
            ), aas)

        paginated_aas, end_index = self._get_slice(request, aas)
        return paginated_aas, end_index

    def _get_shell(self, url_args: Dict) -> model.AssetAdministrationShell:
        return self._get_obj_ts(url_args["aas_id"], model.AssetAdministrationShell)

    def _get_submodels(self, request: Request) -> Tuple[Iterator[model.Submodel], int]:
        submodels: Iterator[model.Submodel] = self._get_all_obj_of_type(model.Submodel)
        id_short = request.args.get("idShort")
        if id_short is not None:
            submodels = filter(lambda sm: sm.id_short == id_short, submodels)
        semantic_id = request.args.get("semanticId")
        if semantic_id is not None:
            spec_semantic_id = HTTPApiDecoder.base64url_json(
                semantic_id, model.Reference, False)  # type: ignore[type-abstract]
            submodels = filter(lambda sm: sm.semantic_id == spec_semantic_id, submodels)
        paginated_submodels, end_index = self._get_slice(request, submodels)
        return paginated_submodels, end_index

    def _get_submodel(self, url_args: Dict) -> model.Submodel:
        return self._get_obj_ts(url_args["submodel_id"], model.Submodel)

    def _get_submodel_submodel_elements(self, request: Request, url_args: Dict) -> \
            Tuple[Iterator[model.SubmodelElement], int]:
        submodel = self._get_submodel(url_args)
        paginated_submodel_elements: Iterator[model.SubmodelElement]
        paginated_submodel_elements, end_index = self._get_slice(request, submodel.submodel_element)
        return paginated_submodel_elements, end_index

    def _get_submodel_submodel_elements_id_short_path(self, url_args: Dict) -> model.SubmodelElement:
        submodel = self._get_submodel(url_args)
        submodel_element = self._get_nested_submodel_element(submodel, url_args["id_shorts"])
        return submodel_element

    def _get_concept_description(self, url_args):
        return self._get_obj_ts(url_args["concept_id"], model.ConceptDescription)

    # ------ all not implemented ROUTES -------
    def not_implemented(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        raise werkzeug.exceptions.NotImplemented("This route is not implemented!")

    # ------ AAS REPO ROUTES -------
    def get_aas_all(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aashells, cursor = self._get_shells(request)
        return response_t(list(aashells), cursor=cursor)

    def post_aas(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                 map_adapter: MapAdapter) -> Response:
        aas = HTTPApiDecoder.request_body(request, model.AssetAdministrationShell, False)
        try:
            self.object_store.add(aas)
        except KeyError as e:
            raise Conflict(f"AssetAdministrationShell with Identifier {aas.id} already exists!") from e
        aas.commit()
        created_resource_url = map_adapter.build(self.get_aas, {
            "aas_id": aas.id
        }, force_external=True)
        return response_t(aas, status=201, headers={"Location": created_resource_url})

    def get_aas_all_reference(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                              **_kwargs) -> Response:
        aashells, cursor = self._get_shells(request)
        references: list[model.ModelReference] = [model.ModelReference.from_referable(aas)
                                                  for aas in aashells]
        return response_t(references, cursor=cursor)

    # --------- AAS ROUTES ---------
    def get_aas(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        return response_t(aas)

    def get_aas_reference(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        reference = model.ModelReference.from_referable(aas)
        return response_t(reference)

    def put_aas(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        aas.update_from(HTTPApiDecoder.request_body(request, model.AssetAdministrationShell,
                                                    is_stripped_request(request)))
        aas.commit()
        return response_t()

    def delete_aas(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        self.object_store.remove(aas)
        return response_t()

    def get_aas_asset_information(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                  **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        return response_t(aas.asset_information)

    def put_aas_asset_information(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                  **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        aas.asset_information = HTTPApiDecoder.request_body(request, model.AssetInformation, False)
        aas.commit()
        return response_t()

    def get_aas_submodel_refs(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                              **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        submodel_refs: Iterator[model.ModelReference[model.Submodel]]
        submodel_refs, cursor = self._get_slice(request, aas.submodel)
        return response_t(list(submodel_refs), cursor=cursor)

    def post_aas_submodel_refs(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                               **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        sm_ref = HTTPApiDecoder.request_body(request, model.ModelReference, False)
        if sm_ref in aas.submodel:
            raise Conflict(f"{sm_ref!r} already exists!")
        aas.submodel.add(sm_ref)
        aas.commit()
        return response_t(sm_ref, status=201)

    def delete_aas_submodel_refs_specific(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                          **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        aas.submodel.remove(self._get_submodel_reference(aas, url_args["submodel_id"]))
        aas.commit()
        return response_t()

    def put_aas_submodel_refs_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                       **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        sm_ref = self._get_submodel_reference(aas, url_args["submodel_id"])
        submodel = self._resolve_reference(sm_ref)
        new_submodel = HTTPApiDecoder.request_body(request, model.Submodel, is_stripped_request(request))
        # determine whether the id changed in advance, in case something goes wrong while updating the submodel
        id_changed: bool = submodel.id != new_submodel.id
        # TODO: https://github.com/eclipse-basyx/basyx-python-sdk/issues/216
        submodel.update_from(new_submodel)
        submodel.commit()
        if id_changed:
            aas.submodel.remove(sm_ref)
            aas.submodel.add(model.ModelReference.from_referable(submodel))
            aas.commit()
        return response_t()

    def delete_aas_submodel_refs_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                          **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        sm_ref = self._get_submodel_reference(aas, url_args["submodel_id"])
        submodel = self._resolve_reference(sm_ref)
        self.object_store.remove(submodel)
        aas.submodel.remove(sm_ref)
        aas.commit()
        return response_t()

    def aas_submodel_refs_redirect(self, request: Request, url_args: Dict, map_adapter: MapAdapter, response_t=None,
                                   **_kwargs) -> Response:
        aas = self._get_shell(url_args)
        # the following makes sure the reference exists
        self._get_submodel_reference(aas, url_args["submodel_id"])
        redirect_url = map_adapter.build(self.get_submodel, {
            "submodel_id": url_args["submodel_id"]
        }, force_external=True)
        if "path" in url_args:
            redirect_url += "/" + url_args["path"]
        if request.query_string:
            redirect_url += "?" + request.query_string.decode("ascii")
        return werkzeug.utils.redirect(redirect_url, 307)

    # ------ SUBMODEL REPO ROUTES -------
    def get_submodel_all(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodels, cursor = self._get_submodels(request)
        return response_t(list(submodels), cursor=cursor, stripped=is_stripped_request(request))

    def post_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                      map_adapter: MapAdapter) -> Response:
        submodel = HTTPApiDecoder.request_body(request, model.Submodel, is_stripped_request(request))
        try:
            self.object_store.add(submodel)
        except KeyError as e:
            raise Conflict(f"Submodel with Identifier {submodel.id} already exists!") from e
        submodel.commit()
        created_resource_url = map_adapter.build(self.get_submodel, {
            "submodel_id": submodel.id
        }, force_external=True)
        return response_t(submodel, status=201, headers={"Location": created_resource_url})

    def get_submodel_all_metadata(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                  **_kwargs) -> Response:
        submodels, cursor = self._get_submodels(request)
        return response_t(list(submodels), cursor=cursor, stripped=True)

    def get_submodel_all_reference(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                   **_kwargs) -> Response:
        submodels, cursor = self._get_submodels(request)
        references: list[model.ModelReference] = [model.ModelReference.from_referable(submodel)
                                                  for submodel in submodels]
        return response_t(references, cursor=cursor, stripped=is_stripped_request(request))

    # --------- SUBMODEL ROUTES ---------

    def delete_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        self.object_store.remove(self._get_obj_ts(url_args["submodel_id"], model.Submodel))
        return response_t()

    def get_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel = self._get_submodel(url_args)
        return response_t(submodel, stripped=is_stripped_request(request))

    def get_submodels_metadata(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                               **_kwargs) -> Response:
        submodel = self._get_submodel(url_args)
        return response_t(submodel, stripped=True)

    def get_submodels_reference(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                **_kwargs) -> Response:
        submodel = self._get_submodel(url_args)
        reference = model.ModelReference.from_referable(submodel)
        return response_t(reference, stripped=is_stripped_request(request))

    def put_submodel(self, request: Request, url_args: Dict, response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel = self._get_submodel(url_args)
        submodel.update_from(HTTPApiDecoder.request_body(request, model.Submodel, is_stripped_request(request)))
        submodel.commit()
        return response_t()

    def get_submodel_submodel_elements(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                       **_kwargs) -> Response:
        submodel_elements, cursor = self._get_submodel_submodel_elements(request, url_args)
        return response_t(list(submodel_elements), cursor=cursor, stripped=is_stripped_request(request))

    def get_submodel_submodel_elements_metadata(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                **_kwargs) -> Response:
        submodel_elements, cursor = self._get_submodel_submodel_elements(request, url_args)
        return response_t(list(submodel_elements), cursor=cursor, stripped=True)

    def get_submodel_submodel_elements_reference(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                 **_kwargs) -> Response:
        submodel_elements, cursor = self._get_submodel_submodel_elements(request, url_args)
        references: list[model.ModelReference] = [model.ModelReference.from_referable(element) for element in
                                                  list(submodel_elements)]
        return response_t(references, cursor=cursor, stripped=is_stripped_request(request))

    def get_submodel_submodel_elements_id_short_path(self, request: Request, url_args: Dict,
                                                     response_t: Type[APIResponse],
                                                     **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        return response_t(submodel_element, stripped=is_stripped_request(request))

    def get_submodel_submodel_elements_id_short_path_metadata(self, request: Request, url_args: Dict,
                                                              response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        if isinstance(submodel_element, model.Capability) or isinstance(submodel_element, model.Operation):
            raise BadRequest(f"{submodel_element.id_short} does not allow the content modifier metadata!")
        return response_t(submodel_element, stripped=True)

    def get_submodel_submodel_elements_id_short_path_reference(self, request: Request, url_args: Dict,
                                                               response_t: Type[APIResponse], **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        reference = model.ModelReference.from_referable(submodel_element)
        return response_t(reference, stripped=is_stripped_request(request))

    def post_submodel_submodel_elements_id_short_path(self, request: Request, url_args: Dict,
                                                      response_t: Type[APIResponse],
                                                      map_adapter: MapAdapter):
        parent = self._get_submodel_or_nested_submodel_element(url_args)
        if not isinstance(parent, model.UniqueIdShortNamespace):
            raise BadRequest(f"{parent!r} is not a namespace, can't add child submodel element!")
        # TODO: remove the following type: ignore comment when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        new_submodel_element = HTTPApiDecoder.request_body(request,
                                                           model.SubmodelElement,  # type: ignore[type-abstract]
                                                           is_stripped_request(request))
        try:
            parent.add_referable(new_submodel_element)
        except model.AASConstraintViolation as e:
            if e.constraint_id != 22:
                raise
            raise Conflict(f"SubmodelElement with idShort {new_submodel_element.id_short} already exists "
                           f"within {parent}!")
        submodel = self._get_submodel(url_args)
        id_short_path = url_args.get("id_shorts", [])
        created_resource_url = map_adapter.build(self.get_submodel_submodel_elements_id_short_path, {
            "submodel_id": submodel.id,
            "id_shorts": id_short_path + [new_submodel_element.id_short]
        }, force_external=True)
        return response_t(new_submodel_element, status=201, headers={"Location": created_resource_url})

    def put_submodel_submodel_elements_id_short_path(self, request: Request, url_args: Dict,
                                                     response_t: Type[APIResponse],
                                                     **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        # TODO: remove the following type: ignore comment when mypy supports abstract types for Type[T]
        # see https://github.com/python/mypy/issues/5374
        new_submodel_element = HTTPApiDecoder.request_body(request,
                                                           model.SubmodelElement,  # type: ignore[type-abstract]
                                                           is_stripped_request(request))
        submodel_element.update_from(new_submodel_element)
        submodel_element.commit()
        return response_t()

    def delete_submodel_submodel_elements_id_short_path(self, request: Request, url_args: Dict,
                                                        response_t: Type[APIResponse],
                                                        **_kwargs) -> Response:
        sm_or_se = self._get_submodel_or_nested_submodel_element(url_args)
        parent: model.UniqueIdShortNamespace = self._expect_namespace(sm_or_se.parent, sm_or_se.id_short)
        self._namespace_submodel_element_op(parent, parent.remove_referable, sm_or_se.id_short)
        return response_t()

    def get_submodel_submodel_element_attachment(self, request: Request, url_args: Dict, **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        if not isinstance(submodel_element, (model.Blob, model.File)):
            raise BadRequest(f"{submodel_element!r} is not a Blob or File, no file content to download!")
        if submodel_element.value is None:
            raise NotFound(f"{submodel_element!r} has no attachment!")

        value: bytes
        if isinstance(submodel_element, model.Blob):
            value = submodel_element.value
        else:
            if not submodel_element.value.startswith("/"):
                raise BadRequest(f"{submodel_element!r} references an external file: {submodel_element.value}")
            bytes_io = io.BytesIO()
            try:
                self.file_store.write_file(submodel_element.value, bytes_io)
            except KeyError:
                raise NotFound(f"No such file: {submodel_element.value}")
            value = bytes_io.getvalue()

        # Blob and File both have the content_type attribute
        return Response(value, content_type=submodel_element.content_type)  # type: ignore[attr-defined]

    def put_submodel_submodel_element_attachment(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                 **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)

        # spec allows PUT only for File, not for Blob
        if not isinstance(submodel_element, model.File):
            raise BadRequest(f"{submodel_element!r} is not a File, no file content to update!")
        elif submodel_element.value is not None:
            raise Conflict(f"{submodel_element!r} already references a file!")

        filename = request.form.get('fileName')
        if filename is None:
            raise BadRequest("No 'fileName' specified!")
        elif not filename.startswith("/"):
            raise BadRequest(f"Given 'fileName' doesn't start with a slash (/): {filename}")

        file_storage: Optional[FileStorage] = request.files.get('file')
        if file_storage is None:
            raise BadRequest("Missing file to upload")
        elif file_storage.mimetype != submodel_element.content_type:
            raise werkzeug.exceptions.UnsupportedMediaType(
                f"Request body is of type {file_storage.mimetype!r}, "
                f"while {submodel_element!r} has content_type {submodel_element.content_type!r}!")

        submodel_element.value = self.file_store.add_file(filename, file_storage.stream, submodel_element.content_type)
        submodel_element.commit()
        return response_t()

    def delete_submodel_submodel_element_attachment(self, request: Request, url_args: Dict,
                                                    response_t: Type[APIResponse],
                                                    **_kwargs) -> Response:
        submodel_element = self._get_submodel_submodel_elements_id_short_path(url_args)
        if not isinstance(submodel_element, (model.Blob, model.File)):
            raise BadRequest(f"{submodel_element!r} is not a Blob or File, no file content to delete!")
        elif submodel_element.value is None:
            raise NotFound(f"{submodel_element!r} has no attachment!")

        if isinstance(submodel_element, model.Blob):
            submodel_element.value = None
        else:
            if not submodel_element.value.startswith("/"):
                raise BadRequest(f"{submodel_element!r} references an external file: {submodel_element.value}")
            try:
                self.file_store.delete_file(submodel_element.value)
            except KeyError:
                pass
            submodel_element.value = None

        submodel_element.commit()
        return response_t()

    def get_submodel_submodel_element_qualifiers(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                 **_kwargs) -> Response:
        sm_or_se = self._get_submodel_or_nested_submodel_element(url_args)
        qualifier_type = url_args.get("qualifier_type")
        if qualifier_type is None:
            return response_t(list(sm_or_se.qualifier))
        return response_t(self._qualifiable_qualifier_op(sm_or_se, sm_or_se.get_qualifier_by_type, qualifier_type))

    def post_submodel_submodel_element_qualifiers(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                  map_adapter: MapAdapter) -> Response:
        sm_or_se = self._get_submodel_or_nested_submodel_element(url_args)
        qualifier = HTTPApiDecoder.request_body(request, model.Qualifier, is_stripped_request(request))
        if sm_or_se.qualifier.contains_id("type", qualifier.type):
            raise Conflict(f"Qualifier with type {qualifier.type} already exists!")
        sm_or_se.qualifier.add(qualifier)
        sm_or_se.commit()
        created_resource_url = map_adapter.build(self.get_submodel_submodel_element_qualifiers, {
            "submodel_id": url_args["submodel_id"],
            "id_shorts": url_args.get("id_shorts") or None,
            "qualifier_type": qualifier.type
        }, force_external=True)
        return response_t(qualifier, status=201, headers={"Location": created_resource_url})

    def put_submodel_submodel_element_qualifiers(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                                 map_adapter: MapAdapter) -> Response:
        sm_or_se = self._get_submodel_or_nested_submodel_element(url_args)
        new_qualifier = HTTPApiDecoder.request_body(request, model.Qualifier, is_stripped_request(request))
        qualifier_type = url_args["qualifier_type"]
        qualifier = self._qualifiable_qualifier_op(sm_or_se, sm_or_se.get_qualifier_by_type, qualifier_type)
        qualifier_type_changed = qualifier_type != new_qualifier.type
        if qualifier_type_changed and sm_or_se.qualifier.contains_id("type", new_qualifier.type):
            raise Conflict(f"A qualifier of type {new_qualifier.type!r} already exists for {sm_or_se!r}")
        sm_or_se.remove_qualifier_by_type(qualifier.type)
        sm_or_se.qualifier.add(new_qualifier)
        sm_or_se.commit()
        if qualifier_type_changed:
            created_resource_url = map_adapter.build(self.get_submodel_submodel_element_qualifiers, {
                "submodel_id": url_args["submodel_id"],
                "id_shorts": url_args.get("id_shorts") or None,
                "qualifier_type": new_qualifier.type
            }, force_external=True)
            return response_t(new_qualifier, status=201, headers={"Location": created_resource_url})
        return response_t(new_qualifier)

    def delete_submodel_submodel_element_qualifiers(self, request: Request, url_args: Dict,
                                                    response_t: Type[APIResponse],
                                                    **_kwargs) -> Response:
        sm_or_se = self._get_submodel_or_nested_submodel_element(url_args)
        qualifier_type = url_args["qualifier_type"]
        self._qualifiable_qualifier_op(sm_or_se, sm_or_se.remove_qualifier_by_type, qualifier_type)
        sm_or_se.commit()
        return response_t()

    # --------- CONCEPT DESCRIPTION ROUTES ---------
    def get_concept_description_all(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                    **_kwargs) -> Response:
        concept_descriptions: Iterator[model.ConceptDescription] = self._get_all_obj_of_type(model.ConceptDescription)
        concept_descriptions, cursor = self._get_slice(request, concept_descriptions)
        return response_t(list(concept_descriptions), cursor=cursor, stripped=is_stripped_request(request))

    def post_concept_description(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                 map_adapter: MapAdapter) -> Response:
        concept_description = HTTPApiDecoder.request_body(request, model.ConceptDescription,
                                                          is_stripped_request(request))
        try:
            self.object_store.add(concept_description)
        except KeyError as e:
            raise Conflict(f"ConceptDescription with Identifier {concept_description.id} already exists!") from e
        concept_description.commit()
        created_resource_url = map_adapter.build(self.get_concept_description, {
            "concept_id": concept_description.id
        }, force_external=True)
        return response_t(concept_description, status=201, headers={"Location": created_resource_url})

    def get_concept_description(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                **_kwargs) -> Response:
        concept_description = self._get_concept_description(url_args)
        return response_t(concept_description, stripped=is_stripped_request(request))

    def put_concept_description(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                **_kwargs) -> Response:
        concept_description = self._get_concept_description(url_args)
        concept_description.update_from(HTTPApiDecoder.request_body(request, model.ConceptDescription,
                                                                    is_stripped_request(request)))
        concept_description.commit()
        return response_t()

    def delete_concept_description(self, request: Request, url_args: Dict, response_t: Type[APIResponse],
                                   **_kwargs) -> Response:
        self.object_store.remove(self._get_concept_description(url_args))
        return response_t()


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8080, WSGIApp(create_full_example(), aasx.DictSupplementaryFileContainer()),
               use_debugger=True, use_reloader=True)
