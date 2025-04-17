import enum
from typing import Optional, Type, Callable, Any, List, Dict
from lxml import etree

from basyx.aas.adapter._generic import PathOrIO
from basyx.aas.adapter.xml import XMLConstructables, AASFromXmlDecoder
from basyx.aas.adapter.xml.xml_deserialization import _parse_xml_document, _failsafe_construct, \
    _child_text_mandatory, NS_AAS, read_aas_xml_element
import server.app.server_model as server_model


class ServerAASFromXmlDecoder(AASFromXmlDecoder):

    @classmethod
    def construct_asset_administration_shell_descriptor(cls, element: etree._Element,
                                                        object_class=server_model.AssetAdministrationShellDescriptor,
                                                        **_kwargs: Any) -> server_model.AssetAdministrationShellDescriptor:
        id_value = _child_text_mandatory(element, NS_AAS + "id")
        id_short = _child_text_mandatory(element, NS_AAS + "idShort")
        endpoints_elem = element.find(NS_AAS + "endpoints")
        endpoints: List[str] = []
        if endpoints_elem is not None:
            endpoints = [child.text.strip() for child in endpoints_elem.findall(NS_AAS + "endpoint") if child.text]

        asset_kind = _child_text_mandatory(element, NS_AAS + "assetKind")

        specific_asset_ids_elem = element.find(NS_AAS + "specificAssetIds")
        specific_asset_ids: List[Dict[str, Any]] = []
        if specific_asset_ids_elem is not None:
            for sid_elem in specific_asset_ids_elem.findall(NS_AAS + "specificAssetId"):
                name = sid_elem.findtext(NS_AAS + "name")
                value = sid_elem.findtext(NS_AAS + "value")
                if name is not None and value is not None:
                    specific_asset_ids.append({"name": name.strip(), "value": value.strip()})

        descriptor = object_class(
            id_=id_value,
            id_short=id_short,
            endpoints=endpoints,
            asset_kind=asset_kind,
            specific_asset_id=specific_asset_ids
        )

        cls._amend_abstract_attributes(descriptor, element)
        return descriptor

    @classmethod
    def construct_submodel_descriptor(cls, element: etree._Element, object_class=server_model.SubmodelDescriptor,
                                      **_kwargs: Any) -> server_model.SubmodelDescriptor:
        submodel_id = _child_text_mandatory(element, NS_AAS + "id")
        id_short = _child_text_mandatory(element, NS_AAS + "idShort")

        endpoints_elem = element.find(NS_AAS + "endpoints")
        endpoints: List[str] = []
        if endpoints_elem is not None:
            endpoints = [child.text.strip() for child in endpoints_elem.findall(NS_AAS + "endpoint") if child.text]

        # Hier können weitere optionale Felder verarbeitet werden, z.B. semanticId, etc.

        submodel_descriptor = object_class(
            id_=submodel_id,
            id_short=id_short,
            endpoints=endpoints
        )

        cls._amend_abstract_attributes(submodel_descriptor, element)
        return submodel_descriptor


class ServerStrictAASFromXmlDecoder(ServerAASFromXmlDecoder):
    """
    Non-failsafe XML decoder. Encountered errors won't be caught and abort parsing.
    """
    failsafe = False


class ServerStrippedAASFromXmlDecoder(ServerAASFromXmlDecoder):
    """
    Decoder for stripped XML elements. Used in the HTTP adapter.
    """
    stripped = True


class ServerStrictStrippedAASFromXmlDecoder(ServerStrictAASFromXmlDecoder, ServerStrippedAASFromXmlDecoder):
    """
    Non-failsafe decoder for stripped XML elements.
    """
    pass


@enum.unique
class ServerXMLConstructables(enum.Enum):
    ASSET_ADMINISTRATION_SHELL_DESCRIPTOR = enum.auto()
    SUBMODEL_DESCRIPTOR = enum.auto()
    ASSET_LINK = enum.auto()


def _select_server_decoder(failsafe: bool, stripped: bool, decoder: Optional[Type[ServerAASFromXmlDecoder]]) \
        -> Type[ServerAASFromXmlDecoder]:
    """
    Returns the correct decoder based on the parameters failsafe and stripped. If a decoder class is given, failsafe
    and stripped are ignored.

    :param failsafe: If true, a failsafe decoder is selected. Ignored if a decoder class is specified.
    :param stripped: If true, a decoder for parsing stripped XML elements is selected. Ignored if a decoder class is
                     specified.
    :param decoder: Is returned, if specified.
    :return: A AASFromXmlDecoder (sub)class.
    """
    if decoder is not None:
        return decoder
    if failsafe:
        if stripped:
            return ServerStrippedAASFromXmlDecoder
        return ServerAASFromXmlDecoder
    else:
        if stripped:
            return ServerStrictStrippedAASFromXmlDecoder
        return ServerStrictAASFromXmlDecoder


def read_server_aas_xml_element(file: PathOrIO, construct: XMLConstructables, failsafe: bool = True,
                                stripped: bool = False,
                                decoder: Optional[Type[AASFromXmlDecoder]] = None, **constructor_kwargs) -> Optional[
    object]:
    """
    Construct a single object from an XML string. The namespaces have to be declared on the object itself, since there
    is no surrounding environment element.

    :param file: A filename or file-like object to read the XML-serialized data from
    :param construct: A member of the enum :class:`~.XMLConstructables`, specifying which type to construct.
    :param failsafe: If true, the document is parsed in a failsafe way: missing attributes and elements are logged
                     instead of causing exceptions. Defect objects are skipped.
                     This parameter is ignored if a decoder class is specified.
    :param stripped: If true, stripped XML elements are parsed.
                     See https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/91
                     This parameter is ignored if a decoder class is specified.
    :param decoder: The decoder class used to decode the XML elements
    :param constructor_kwargs: Keyword arguments passed to the constructor function
    :raises ~lxml.etree.XMLSyntaxError: **Non-failsafe**: If the given file(-handle) has invalid XML
    :raises KeyError: **Non-failsafe**: If a required namespace has not been declared on the XML document
    :raises (~basyx.aas.model.base.AASConstraintViolation, KeyError, ValueError): **Non-failsafe**: Errors during
                                                                                  construction of the objects
    :return: The constructed object or None, if an error occurred in failsafe mode.
    """

    try:
        return read_aas_xml_element(file, construct, failsafe=failsafe, stripped=stripped, decoder=decoder,
                                    **constructor_kwargs)
    except ValueError:
        decoder_ = _select_server_decoder(failsafe, stripped, decoder)
        constructor: Callable[..., object]

        if construct == ServerXMLConstructables.ASSET_ADMINISTRATION_SHELL_DESCRIPTOR:
            constructor = decoder_.construct_asset_administration_shell_descriptor
        elif construct == ServerXMLConstructables.SUBMODEL_DESCRIPTOR:
            constructor = decoder_.construct_submodel_descriptor
        else:
            raise ValueError(f"{construct.name} cannot be constructed!")

        element = _parse_xml_document(file, failsafe=decoder_.failsafe)
        return _failsafe_construct(element, constructor, decoder_.failsafe, **constructor_kwargs)
