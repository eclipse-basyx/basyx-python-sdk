"""
This package contains functionality for serialization and deserialization of PyI40AAS objects into/from XML.

xml_serialization:
    The module offers a function to write an ObjectStore to a given file.

xml_deserialization.py
    The module offers a function to create an ObjectStore from a given xml document.
"""

from .xml_serialization import write_aas_xml_file
from .xml_deserialization import read_aas_xml_file
