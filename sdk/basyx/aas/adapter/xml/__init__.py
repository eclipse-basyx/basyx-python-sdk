"""
.. _adapter.xml.__init__:

This package contains functionality for serialization and deserialization of BaSyx Python SDK objects into/from XML.

:ref:`xml_serialization <adapter.xml.xml_serialization>`: The module offers a function to write an
:class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` to a given file.

:ref:`xml_deserialization <adapter.xml.xml_deserialization>`: The module offers a function to create an
:class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` from a given xml document.
"""

from .xml_serialization import (
    object_store_to_xml_element,
    write_aas_xml_file,
    object_to_xml_element,
    write_aas_xml_element,
)
from .xml_deserialization import (
    AASFromXmlDecoder,
    StrictAASFromXmlDecoder,
    StrippedAASFromXmlDecoder,
    StrictStrippedAASFromXmlDecoder,
    XMLConstructables,
    read_aas_xml_file,
    read_aas_xml_file_into,
    read_aas_xml_element,
)
