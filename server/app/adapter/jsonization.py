from typing import Dict, Set, ContextManager, IO, get_args, Optional, Type, List

import server.app.server_model as server_model
from basyx.aas import model
from basyx.aas.adapter import _generic
from basyx.aas.adapter._generic import ASSET_KIND_INVERSE, Path, PathOrIO
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.adapter.json.json_deserialization import _get_ts, AASFromJsonDecoder, _select_decoder

import json
import logging
from typing import Callable

import contextlib


logger = logging.getLogger(__name__)


class ServerAASFromJsonDecoder(AASFromJsonDecoder):
    @classmethod
    def _get_aas_class_parsers(cls) -> Dict[str, Callable[[Dict[str, object]], object]]:
        aas_class_parsers = super()._get_aas_class_parsers()
        aas_class_parsers.update({
            'AssetAdministrationShellDescriptor': cls._construct_asset_administration_shell_descriptor,
            'SubmodelDescriptor': cls._construct_submodel_descriptor,
            'AssetLink': cls._construct_asset_link,
            'ProtocolInformation': cls._construct_protocol_information,
            'Endpoint': cls._construct_endpoint
        })
        return aas_class_parsers

    # ##################################################################################################
    # Utility Methods used in constructor methods to add general attributes (from abstract base classes)
    # ##################################################################################################

    @classmethod
    def _amend_abstract_attributes(cls, obj: object, dct: Dict[str, object]) -> None:
        super()._amend_abstract_attributes(obj, dct)

        if isinstance(obj, server_model.Descriptor):
            if 'description' in dct:
                obj.description = cls._construct_lang_string_set(_get_ts(dct, 'description', list),
                                                                 model.MultiLanguageTextType)
            if 'displayName' in dct:
                obj.display_name = cls._construct_lang_string_set(_get_ts(dct, 'displayName', list),
                                                                  model.MultiLanguageNameType)
            if 'extensions' in dct:
                for extension in _get_ts(dct, 'extensions', list):
                    obj.extension.add(cls._construct_extension(extension))

    @classmethod
    def _construct_asset_administration_shell_descriptor(
            cls, dct: Dict[str, object],
            object_class=server_model.AssetAdministrationShellDescriptor) -> server_model.AssetAdministrationShellDescriptor:
        ret = object_class(id_=_get_ts(dct, 'id', str))
        cls._amend_abstract_attributes(ret, dct)
        if 'administration' in dct:
            ret.administration = cls._construct_administrative_information(_get_ts(dct, 'administration', dict))
        if 'assetkind' in dct:
            # FIXME
            asset_kind = ASSET_KIND_INVERSE[_get_ts(dct, 'assetKind', str)]
        if 'assetType' in dct:
            ret.asset_type = _get_ts(dct, 'assetType', str)
        global_asset_id = None
        if 'globalAssetId' in dct:
            # FIXME
            global_asset_id = _get_ts(dct, 'globalAssetId', str)
        specific_asset_id = set()
        if 'specificAssetIds' in dct:
            for desc_data in _get_ts(dct, "specificAssetIds", list):
                specific_asset_id.add(cls._construct_specific_asset_id(desc_data, model.SpecificAssetId))
        if 'endpoints' in dct:
            for endpoint_dct in _get_ts(dct, 'endpoints', list):
                if 'protocolInformation' in endpoint_dct:
                    ret.endpoints.append(
                        cls._construct_endpoint(endpoint_dct,
                                                server_model.Endpoint))
                elif 'href' in endpoint_dct:
                    protocol_info = server_model.ProtocolInformation(
                        href=_get_ts(endpoint_dct['href'], 'href', str),
                        endpoint_protocol=_get_ts(endpoint_dct['href'],
                                                  'endpointProtocol',
                                                  str) if 'endpointProtocol' in
                                                          endpoint_dct[
                                                              'href'] else None,
                        endpoint_protocol_version=_get_ts(
                            endpoint_dct['href'],
                            'endpointProtocolVersion',
                            list) if 'endpointProtocolVersion' in
                                     endpoint_dct['href'] else None
                    )
                    ret.endpoints.append(server_model.Endpoint(
                        protocol_information=protocol_info,
                        interface=_get_ts(endpoint_dct, 'interface',
                                          str)))
        if 'idShort' in dct:
            ret.id_short = _get_ts(dct, 'idShort', str)
        if 'submodelDescriptors' in dct:
            ret.submodel_descriptors = cls._construct_submodel_descriptor(_get_ts(dct, 'submodelDescriptors', list),
                                                                          server_model.SubmodelDescriptor)
        return ret

    @classmethod
    def _construct_protocol_information(cls, dct: Dict[str, object],
                                        object_class=server_model.ProtocolInformation) -> server_model.ProtocolInformation:
        ret = object_class(
            href=_get_ts(dct, 'href', str),
            endpoint_protocol=_get_ts(dct, 'endpointProtocol',
                                      str) if 'endpointProtocol' in dct else None,
            endpoint_protocol_version=_get_ts(dct,
                                              'endpointProtocolVersion',
                                              list) if 'endpointProtocolVersion' in dct else None,
            subprotocol=_get_ts(dct, 'subprotocol',
                                str) if 'subprotocol' in dct else None,
            subprotocol_body=_get_ts(dct, 'subprotocolBody',
                                     str) if 'subprotocolBody' in dct else None,
            subprotocol_body_encoding=_get_ts(dct,
                                              'subprotocolBodyEncoding',
                                              str) if 'subprotocolBodyEncoding' in dct else None
        )
        return ret

    @classmethod
    def _construct_endpoint(cls, dct: Dict[str, object],
                            object_class=server_model.Endpoint) -> server_model.Endpoint:
        ret = object_class(
            protocol_information=cls._construct_protocol_information(
                _get_ts(dct, 'protocolInformation', dict),
                server_model.ProtocolInformation
            ),
            interface=_get_ts(dct, 'interface',
                              str)
        )
        cls._amend_abstract_attributes(ret, dct)
        return ret

    @classmethod
    def _construct_submodel_descriptor(
            cls, dct: Dict[str, object], object_class=server_model.SubmodelDescriptor) -> server_model.SubmodelDescriptor:
        ret = object_class(id_=_get_ts(dct, 'id', str),
                           endpoints=[])
        cls._amend_abstract_attributes(ret, dct)
        for endpoint_dct in _get_ts(dct, 'endpoints', list):
            if 'protocolInformation' in endpoint_dct:
                ret.endpoints.append(
                    cls._construct_endpoint(endpoint_dct,
                                            server_model.Endpoint))
            elif 'href' in endpoint_dct:
                protocol_info = server_model.ProtocolInformation(
                    href=_get_ts(endpoint_dct['href'], 'href', str),
                    endpoint_protocol=_get_ts(endpoint_dct['href'],
                                              'endpointProtocol',
                                              str) if 'endpointProtocol' in
                                                      endpoint_dct[
                                                          'href'] else None,
                    endpoint_protocol_version=_get_ts(
                        endpoint_dct['href'],
                        'endpointProtocolVersion',
                        list) if 'endpointProtocolVersion' in
                                 endpoint_dct['href'] else None
                )
                ret.endpoints.append(server_model.Endpoint(
                    protocol_information=protocol_info,
                    interface=_get_ts(endpoint_dct, 'interface',
                                      str)))
        if 'administration' in dct:
            ret.administration = cls._construct_administrative_information(
                _get_ts(dct, 'administration', dict))
        if 'idShort' in dct:
            ret.id_short = _get_ts(dct, 'idShort', str)
        if 'semanticId' in dct:
            ret.semantic_id = cls._construct_reference(_get_ts(dct, 'semanticId', dict))
        if 'supplementalSemanticIds' in dct:
            for ref in _get_ts(dct, 'supplementalSemanticIds', list):
                ret.supplemental_semantic_id.append(cls._construct_reference(ref))
        return ret

    @classmethod
    def _construct_asset_link(
            cls, dct: Dict[str, object], object_class=server_model.AssetLink) -> server_model.AssetLink:
        ret = object_class(name=_get_ts(dct, 'name', str),
                           value=_get_ts(dct, 'value', str))
        return ret


class ServerStrictAASFromJsonDecoder(ServerAASFromJsonDecoder):
    """
    A strict version of the AASFromJsonDecoder class for deserializing Asset Administration Shell data from the
    official JSON format

    This version has set ``failsafe = False``, which will lead to Exceptions raised for every missing attribute or wrong
    object type.
    """
    failsafe = False


class ServerStrippedAASFromJsonDecoder(ServerAASFromJsonDecoder):
    """
    Decoder for stripped JSON objects. Used in the HTTP adapter.
    """
    stripped = True


class ServerStrictStrippedAASFromJsonDecoder(ServerStrictAASFromJsonDecoder, ServerStrippedAASFromJsonDecoder):
    """
    Non-failsafe decoder for stripped JSON objects.
    """
    pass


def read_aas_json_file_into(object_store: model.AbstractObjectStore, file: PathOrIO, replace_existing: bool = False,
                            ignore_existing: bool = False, failsafe: bool = True, stripped: bool = False,
                            decoder: Optional[Type[AASFromJsonDecoder]] = None) -> Set[model.Identifier]:
    """
    Read an Asset Administration Shell JSON file according to 'Details of the Asset Administration Shell', chapter 5.5
    into a given object store.

    :param object_store: The :class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` in which the
                         identifiable objects should be stored
    :param file: A filename or file-like object to read the JSON-serialized data from
    :param replace_existing: Whether to replace existing objects with the same identifier in the object store or not
    :param ignore_existing: Whether to ignore existing objects (e.g. log a message) or raise an error.
                            This parameter is ignored if replace_existing is ``True``.
    :param failsafe: If ``True``, the document is parsed in a failsafe way: Missing attributes and elements are logged
                     instead of causing exceptions. Defect objects are skipped.
                     This parameter is ignored if a decoder class is specified.
    :param stripped: If ``True``, stripped JSON objects are parsed.
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if a decoder class is specified.
    :param decoder: The decoder class used to decode the JSON objects
    :raises KeyError: **Non-failsafe**: Encountered a duplicate identifier
    :raises KeyError: Encountered an identifier that already exists in the given ``object_store`` with both
                     ``replace_existing`` and ``ignore_existing`` set to ``False``
    :raises (~basyx.aas.model.base.AASConstraintViolation, KeyError, ValueError, TypeError): **Non-failsafe**:
        Errors during construction of the objects
    :raises TypeError: **Non-failsafe**: Encountered an element in the wrong list
                                         (e.g. an AssetAdministrationShell in ``submodels``)
    :return: A set of :class:`Identifiers <basyx.aas.model.base.Identifier>` that were added to object_store
    """
    ret: Set[model.Identifier] = set()
    decoder_ = _select_decoder(failsafe, stripped, decoder)

    # json.load() accepts TextIO and BinaryIO
    cm: ContextManager[IO]
    if isinstance(file, get_args(Path)):
        # 'file' is a path, needs to be opened first
        cm = open(file, "r", encoding="utf-8-sig")
    else:
        # 'file' is not a path, thus it must already be IO
        # mypy seems to have issues narrowing the type due to get_args()
        cm = contextlib.nullcontext(file)  # type: ignore[arg-type]

    # read, parse and convert JSON file
    with cm as fp:
        data = json.load(fp, cls=decoder_)

    for name, expected_type in (('assetAdministrationShells', model.AssetAdministrationShell),
                                ('submodels', model.Submodel),
                                ('conceptDescriptions', model.ConceptDescription),
                                ('assetAdministrationShellDescriptors', server_model.AssetAdministrationShellDescriptor),
                                ('submodelDescriptors', server_model.SubmodelDescriptor)):
        try:
            lst = _get_ts(data, name, list)
        except (KeyError, TypeError):
            continue

        for item in lst:
            error_message = "Expected a {} in list '{}', but found {}".format(
                expected_type.__name__, name, repr(item))
            if isinstance(item, model.Identifiable):
                if not isinstance(item, expected_type):
                    if decoder_.failsafe:
                        logger.warning("{} was in wrong list '{}'; nevertheless, we'll use it".format(item, name))
                    else:
                        raise TypeError(error_message)
                if item.id in ret:
                    error_message = f"{item} has a duplicate identifier already parsed in the document!"
                    if not decoder_.failsafe:
                        raise KeyError(error_message)
                    logger.error(error_message + " skipping it...")
                    continue
                existing_element = object_store.get(item.id)
                if existing_element is not None:
                    if not replace_existing:
                        error_message = f"object with identifier {item.id} already exists " \
                                        f"in the object store: {existing_element}!"
                        if not ignore_existing:
                            raise KeyError(error_message + f" failed to insert {item}!")
                        logger.info(error_message + f" skipping insertion of {item}...")
                        continue
                    object_store.discard(existing_element)
                object_store.add(item)
                ret.add(item.id)
            elif decoder_.failsafe:
                logger.error(error_message)
            else:
                raise TypeError(error_message)
    return ret


class ServerAASToJsonEncoder(AASToJsonEncoder):

    def default(self, obj: object) -> object:
        """
        The overwritten ``default`` method for :class:`json.JSONEncoder`

        :param obj: The object to serialize to json
        :return: The serialized object
        """
        mapping: Dict[Type, Callable] = {
            model.AdministrativeInformation: self._administrative_information_to_json,
            model.AnnotatedRelationshipElement: self._annotated_relationship_element_to_json,
            model.AssetAdministrationShell: self._asset_administration_shell_to_json,
            model.AssetInformation: self._asset_information_to_json,
            model.BasicEventElement: self._basic_event_element_to_json,
            model.Blob: self._blob_to_json,
            model.Capability: self._capability_to_json,
            model.ConceptDescription: self._concept_description_to_json,
            model.DataSpecificationIEC61360: self._data_specification_iec61360_to_json,
            model.Entity: self._entity_to_json,
            model.Extension: self._extension_to_json,
            model.File: self._file_to_json,
            model.Key: self._key_to_json,
            model.LangStringSet: self._lang_string_set_to_json,
            model.MultiLanguageProperty: self._multi_language_property_to_json,
            model.Operation: self._operation_to_json,
            model.Property: self._property_to_json,
            model.Qualifier: self._qualifier_to_json,
            model.Range: self._range_to_json,
            model.Reference: self._reference_to_json,
            model.ReferenceElement: self._reference_element_to_json,
            model.RelationshipElement: self._relationship_element_to_json,
            model.Resource: self._resource_to_json,
            model.SpecificAssetId: self._specific_asset_id_to_json,
            model.Submodel: self._submodel_to_json,
            model.SubmodelElementCollection: self._submodel_element_collection_to_json,
            model.SubmodelElementList: self._submodel_element_list_to_json,
            model.ValueReferencePair: self._value_reference_pair_to_json,
            server_model.AssetAdministrationShellDescriptor: self._asset_administration_shell_descriptor_to_json,
            server_model.SubmodelDescriptor: self._submodel_descriptor_to_json,
            server_model.Endpoint: self._endpoint_to_json,
            server_model.ProtocolInformation: self._protocol_information_to_json,
            server_model.AssetLink: self._asset_link_to_json
        }
        for typ in mapping:
            if isinstance(obj, typ):
                mapping_method = mapping[typ]
                return mapping_method(obj)
        return super().default(obj)

    @classmethod
    def _abstract_classes_to_json(cls, obj: object) -> Dict[str, object]:
        data: Dict[str, object] = super()._abstract_classes_to_json(obj)
        if isinstance(obj, server_model.Descriptor):
            if obj.description:
                data['description'] = obj.description
            if obj.display_name:
                data['displayName'] = obj.display_name
            if obj.extension:
                data['extensions'] = list(obj.extension)

        return data


    @classmethod
    def _asset_administration_shell_descriptor_to_json(cls, obj: server_model.AssetAdministrationShellDescriptor) -> Dict[str, object]:
        """
        serialization of an object from class AssetAdministrationShell to json

        :param obj: object of class AssetAdministrationShell
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data.update(cls._namespace_to_json(obj))
        data['id'] = obj.id
        if obj.administration:
            data['administration'] = obj.administration
        if obj.asset_kind:
            data['assetKind'] = _generic.ASSET_KIND[obj.asset_kind]
        if obj.asset_type:
            data['assetType'] = obj.asset_type
        if obj.global_asset_id:
            data['globalAssetId'] = obj.global_asset_id
        if obj.specific_asset_id:
            data['specificAssetIds'] = list(obj.specific_asset_id)
        if obj.endpoints:
            data['endpoints'] = list(obj.endpoints)
        if obj.id_short:
            data['idShort'] = obj.id_short
        if obj.submodel_descriptors:
            data['submodelDescriptors'] = list(obj.submodel_descriptors)
        return data

    @classmethod
    def _protocol_information_to_json(cls,
                                      obj: server_model.ProtocolInformation) -> \
            Dict[str, object]:
        data = cls._abstract_classes_to_json(obj)

        data['href'] = obj.href
        if obj.endpoint_protocol:
            data['endpointProtocol'] = obj.endpoint_protocol
        if obj.endpoint_protocol_version:
            data['endpointProtocolVersion'] = obj.endpoint_protocol_version
        if obj.subprotocol:
            data['subprotocol'] = obj.subprotocol
        if obj.subprotocol_body:
            data['subprotocolBody'] = obj.subprotocol_body
        if obj.subprotocol_body_encoding:
            data['subprotocolBodyEncoding'] = obj.subprotocol_body_encoding
        return data

    @classmethod
    def _endpoint_to_json(cls, obj: server_model.Endpoint) -> Dict[str, object]:
        data = cls._abstract_classes_to_json(obj)
        data['protocolInformation'] = cls._protocol_information_to_json(
                obj.protocol_information)
        data['interface'] = obj.interface
        return data

    @classmethod
    def _submodel_descriptor_to_json(cls, obj: server_model.SubmodelDescriptor) -> Dict[str, object]:
        """
        serialization of an object from class Submodel to json

        :param obj: object of class Submodel
        :return: dict with the serialized attributes of this object
        """
        data = cls._abstract_classes_to_json(obj)
        data['id'] = obj.id
        data['endpoints'] = [cls._endpoint_to_json(ep) for ep in
                             obj.endpoints]
        if obj.id_short:
            data['idShort'] = obj.id_short
        if obj.administration:
            data['administration'] = obj.administration
        if obj.semantic_id:
            data['semanticId'] = obj.semantic_id
        if obj.supplemental_semantic_id:
            data['supplementalSemanticIds'] = list(obj.supplemental_semantic_id)
        return data

    @classmethod
    def _asset_link_to_json(cls, obj: server_model.AssetLink) -> Dict[str, object]:
        data = cls._abstract_classes_to_json(obj)
        data['name'] = obj.name
        data['value'] = obj.value
        return data


def _create_dict(data: model.AbstractObjectStore) -> dict:
    # separate different kind of objects
    asset_administration_shells: List[model.AssetAdministrationShell] = []
    submodels: List[model.Submodel] = []
    concept_descriptions: List[model.ConceptDescription] = []
    asset_administration_shell_descriptors: List[server_model.AssetAdministrationShellDescriptor] = []
    submodel_descriptors: List[server_model.SubmodelDescriptor] = []
    assets_links: List[server_model.AssetLink] = []
    for obj in data:
        if isinstance(obj, model.AssetAdministrationShell):
            asset_administration_shells.append(obj)
        elif isinstance(obj, model.Submodel):
            submodels.append(obj)
        elif isinstance(obj, model.ConceptDescription):
            concept_descriptions.append(obj)
        elif isinstance(obj, server_model.AssetAdministrationShellDescriptor):
            asset_administration_shell_descriptors.append(obj)
        elif isinstance(obj, server_model.SubmodelDescriptor):
            submodel_descriptors.append(obj)
        elif isinstance(obj, server_model.AssetLink):
            assets_links.append(obj)
    dict_: Dict[str, List] = {}
    if asset_administration_shells:
        dict_['assetAdministrationShells'] = asset_administration_shells
    if submodels:
        dict_['submodels'] = submodels
    if concept_descriptions:
        dict_['conceptDescriptions'] = concept_descriptions
    if asset_administration_shell_descriptors:
        dict_['assetAdministrationShellDescriptors'] = asset_administration_shell_descriptors
    if submodel_descriptors:
        dict_['submodelDescriptors'] = submodel_descriptors
    if assets_links:
        dict_['assetLinks'] = assets_links
    return dict_
