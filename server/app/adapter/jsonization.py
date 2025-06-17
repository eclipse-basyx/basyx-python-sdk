from typing import Dict, Set, Optional, Type

import server.app.model as server_model
from basyx.aas import model
from basyx.aas.adapter import _generic
from basyx.aas.adapter._generic import ASSET_KIND_INVERSE, PathOrIO
from basyx.aas.adapter.json import AASToJsonEncoder
from basyx.aas.adapter.json.json_deserialization import _get_ts, AASFromJsonDecoder, JSON_AAS_TOP_LEVEL_KEYS_TO_TYPES, \
    read_aas_json_file_into

import logging
from typing import Callable

logger = logging.getLogger(__name__)

JSON_SERVER_AAS_TOP_LEVEL_KEYS_TO_TYPES = JSON_AAS_TOP_LEVEL_KEYS_TO_TYPES + (
    ('assetAdministrationShellDescriptors', server_model.AssetAdministrationShellDescriptor),
    ('submodelDescriptors', server_model.SubmodelDescriptor)
)


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
        if 'assetKind' in dct:
            ret.asset_kind = ASSET_KIND_INVERSE[_get_ts(dct, 'assetKind', str)]
        if 'assetType' in dct:
            ret.asset_type = _get_ts(dct, 'assetType', str)
        global_asset_id = None
        if 'globalAssetId' in dct:
            ret.global_asset_id = _get_ts(dct, 'globalAssetId', str)
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
            cls, dct: Dict[str, object],
            object_class=server_model.SubmodelDescriptor) -> server_model.SubmodelDescriptor:
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


def read_server_aas_json_file_into(object_store: model.AbstractObjectStore, file: PathOrIO,
                                   replace_existing: bool = False,
                                   ignore_existing: bool = False, failsafe: bool = True, stripped: bool = False,
                                   decoder: Optional[Type[AASFromJsonDecoder]] = None) -> Set[model.Identifier]:
    return read_aas_json_file_into(object_store=object_store, file=file, replace_existing=replace_existing,
                                   ignore_existing=ignore_existing, failsafe=failsafe, stripped=stripped,
                                   decoder=decoder, keys_to_types=JSON_SERVER_AAS_TOP_LEVEL_KEYS_TO_TYPES)


class ServerAASToJsonEncoder(AASToJsonEncoder):

    @classmethod
    def _get_aas_class_serializers(cls) -> Dict[Type, Callable]:
        serializers = super()._get_aas_class_serializers()
        serializers.update({
            server_model.AssetAdministrationShellDescriptor: cls._asset_administration_shell_descriptor_to_json,
            server_model.SubmodelDescriptor: cls._submodel_descriptor_to_json,
            server_model.Endpoint: cls._endpoint_to_json,
            server_model.ProtocolInformation: cls._protocol_information_to_json,
            server_model.AssetLink: cls._asset_link_to_json
        })
        return serializers

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
    def _asset_administration_shell_descriptor_to_json(cls, obj: server_model.AssetAdministrationShellDescriptor) -> \
            Dict[str, object]:
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
