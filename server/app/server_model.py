from __future__ import absolute_import

import abc
import re
from enum import Enum

from typing import Optional, List, Iterable

import server.app
from basyx.aas.model import base, NamespaceSet


class AssetLink:
    def __init__(self, name: base.LabelType, value: base.Identifier):
        if not name:
            raise ValueError("AssetLink 'name' must be a non-empty string.")
        if not value:
            raise ValueError("AssetLink 'value' must be a non-empty string.")
        self.name = name
        self.value = value


class SecurityTypeEnum(Enum):
    NONE = "NONE"
    RFC_TLSA = "RFC_TLSA"
    W3C_DID = "W3C_DID"


class SecurityAttributeObject:
    def __init__(self, type_: SecurityTypeEnum, key: str, value: str):

        if not isinstance(type_, SecurityTypeEnum):
            raise ValueError(f"Invalid security type: {type_}. Must be one of {list(SecurityTypeEnum)}")
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string.")
        if not value or not isinstance(value, str):
            raise ValueError("Value must be a non-empty string.")
        self.type = type_
        self.key = key
        self.value = value


class ProtocolInformation:

    def __init__(
            self,
            href: str,
            endpoint_protocol: Optional[str] = None,
            endpoint_protocol_version: Optional[List[str]] = None,
            subprotocol: Optional[str] = None,
            subprotocol_body: Optional[str] = None,
            subprotocol_body_encoding: Optional[str] = None,
            security_attributes: Optional[List[SecurityAttributeObject]] = None
    ):
        if not href or not isinstance(href, str):
            raise ValueError("href must be a non-empty string representing a valid URL.")

        self.href = href
        self.endpoint_protocol = endpoint_protocol
        self.endpoint_protocol_version = endpoint_protocol_version or []
        self.subprotocol = subprotocol
        self.subprotocol_body = subprotocol_body
        self.subprotocol_body_encoding = subprotocol_body_encoding
        self.security_attributes = security_attributes or []


class Endpoint:
    INTERFACE_SHORTNAMES = {
        "AAS", "SUBMODEL", "SERIALIZE", "AASX-FILE", "AAS-REGISTRY",
        "SUBMODEL-REGISTRY", "AAS-REPOSITORY", "SUBMODEL-REPOSITORY",
        "CD-REPOSITORY", "AAS-DISCOVERY"
    }
    VERSION_PATTERN = re.compile(r"^\d+(\.\d+)*$")

    def __init__(self, interface: base.NameType, protocol_information: ProtocolInformation):  # noqa: E501

        self.interface = interface
        self.protocol_information = protocol_information

    @property
    def interface(self) -> str:
        return self._interface

    @interface.setter
    def interface(self, interface: base.NameType):
        if interface is None:
            raise ValueError("Invalid value for `interface`, must not be `None`")
        if not self.is_valid_interface(interface):
            raise ValueError(f"Invalid interface format: {interface}. Expected format: '<SHORTNAME>-<VERSION>', ")

        self._interface = interface

    @classmethod
    def is_valid_interface(cls, interface: base.NameType) -> bool:
        parts = interface.split("-", 1)
        if len(parts) != 2:
            return False
        short_name, version = parts
        return short_name in cls.INTERFACE_SHORTNAMES and cls.VERSION_PATTERN.match(version)

    @property
    def protocol_information(self) -> ProtocolInformation:
        return self._protocol_information

    @protocol_information.setter
    def protocol_information(self, protocol_information: ProtocolInformation):
        if protocol_information is None:
            raise ValueError("Invalid value for `protocol_information`, must not be `None`")  # noqa: E501

        self._protocol_information = protocol_information


class Descriptor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, description: Optional[base.MultiLanguageTextType] = None,
                 display_name: Optional[base.MultiLanguageNameType] = None, extension: Iterable[base.Extension] = ()):
        super().__init__()
        self.namespace_element_sets: List[NamespaceSet] = []
        self.description: Optional[base.MultiLanguageTextType] = description
        self.display_name: Optional[base.MultiLanguageNameType] = display_name
        self.extension = base.NamespaceSet(self, [("name", True)], extension)

    @property
    def description(self) -> Optional[base.MultiLanguageTextType]:
        return self._description

    @description.setter
    def description(self, value: Optional[base.MultiLanguageTextType]):
        self._description = value

    @property
    def display_name(self) -> Optional[base.MultiLanguageNameType]:
        return self._display_name

    @display_name.setter
    def display_name(self, value: Optional[base.MultiLanguageNameType]):
        self._display_name = value

    def commit(self):
        pass

    def update(self):
        pass

    def update_from(self, other: "Descriptor", update_source: bool = False):
        """
        Updates the descriptor's attributes from another descriptor.

        :param other: The descriptor to update from.
        :param update_source: Placeholder for compatibility; not used in this context.
        """
        for attr in vars(other):
            if attr == "id":
                continue  # Skip updating the unique identifier of the AAS
            setattr(self, attr, getattr(other, attr))


class SubmodelDescriptor(Descriptor):

    def __init__(self, id_: base.Identifier, endpoints: List[Endpoint],
                 administration: Optional[base.AdministrativeInformation] = None,
                 id_short: Optional[base.NameType] = None, semantic_id: Optional[base.Reference] = None,
                 supplemental_semantic_id: Iterable[base.Reference] = ()):
        super().__init__()
        self.id: base.Identifier = id_
        self.endpoints: List[Endpoint] = endpoints
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.id_short: Optional[base.NameType] = id_short
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.supplemental_semantic_id: base.ConstrainedList[base.Reference] = \
            base.ConstrainedList(supplemental_semantic_id)


class AssetAdministrationShellDescriptor(Descriptor):

    def __init__(self,
                 id_: base.Identifier,
                 administration: Optional[base.AdministrativeInformation] = None,
                 asset_kind: Optional[base.AssetKind] = None,
                 asset_type: Optional[base.Identifier] = None,
                 endpoints: Optional[List[Endpoint]] = None,
                 global_asset_id: Optional[base.Identifier] = None,
                 id_short: Optional[base.NameType] = None,
                 specific_asset_id: Iterable[base.SpecificAssetId] = (),
                 submodel_descriptors: Optional[List[SubmodelDescriptor]] = None,
                 description: Optional[base.MultiLanguageTextType] = None,
                 display_name: Optional[base.MultiLanguageNameType] = None,
                 extension: Iterable[base.Extension] = ()):
        """AssetAdministrationShellDescriptor -

        Nur das 'id'-Feld (id_) ist zwingend erforderlich. Alle anderen Felder erhalten Defaultwerte.
        """
        super().__init__()
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.asset_kind: Optional[base.AssetKind] = asset_kind
        self.asset_type: Optional[base.Identifier] = asset_type
        self.endpoints: Optional[
            List[Endpoint]] = endpoints if endpoints is not None else []  # leere Liste, falls nicht gesetzt
        self.global_asset_id: Optional[base.Identifier] = global_asset_id
        self.id_short: Optional[base.NameType] = id_short
        self.id: base.Identifier = id_
        self._specific_asset_id: base.ConstrainedList[base.SpecificAssetId] = base.ConstrainedList(
            specific_asset_id,
            item_set_hook=self._check_constraint_set_spec_asset_id,
            item_del_hook=self._check_constraint_del_spec_asset_id
        )
        self.submodel_descriptors = submodel_descriptors if submodel_descriptors is not None else []
        self.description: Optional[base.MultiLanguageTextType] = description
        self.display_name: Optional[base.MultiLanguageNameType] = display_name
        self.extension = base.NamespaceSet(self, [("name", True)], extension)

    @property
    def specific_asset_id(self) -> base.ConstrainedList[base.SpecificAssetId]:
        return self._specific_asset_id

    @specific_asset_id.setter
    def specific_asset_id(self, specific_asset_id: Iterable[base.SpecificAssetId]) -> None:
        # constraints are checked via _check_constraint_set_spec_asset_id() in this case
        self._specific_asset_id[:] = specific_asset_id

    def _check_constraint_set_spec_asset_id(self, items_to_replace: List[base.SpecificAssetId],
                                            new_items: List[base.SpecificAssetId],
                                            old_list: List[base.SpecificAssetId]) -> None:
        self._validate_aasd_131(self.global_asset_id,
                                len(old_list) - len(items_to_replace) + len(new_items) > 0)

    def _check_constraint_del_spec_asset_id(self, _item_to_del: base.SpecificAssetId,
                                            old_list: List[base.SpecificAssetId]) -> None:
        self._validate_aasd_131(self.global_asset_id, len(old_list) > 1)
