"""
.. _adapter.xml.__init__:

This package contains functionality for serialization and deserialization of PyI40AAS objects into/from XML.

:ref:`xml_serialization <adapter.xml.xml_serialization>`: The module offers a function to write an
:class:`ObjectStore <aas.model.provider.AbstractObjectStore>` to a given file.

:ref:`xml_deserialization <adapter.xml.xml_deserialization>`: The module offers a function to create an
:class:`ObjectStore <aas.model.provider.AbstractObjectStore>` from a given xml document.
"""
import os.path

from .xml_serialization import write_aas_xml_file
from .xml_deserialization import AASFromXmlDecoder, StrictAASFromXmlDecoder, StrippedAASFromXmlDecoder, \
    StrictStrippedAASFromXmlDecoder, XMLConstructables, read_aas_xml_file, read_aas_xml_file_into, read_aas_xml_element

XML_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'AAS.xsd')
