from __future__ import absolute_import

import re
from enum import Enum
from typing import Optional, List

from basyx.aas.model import base


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
