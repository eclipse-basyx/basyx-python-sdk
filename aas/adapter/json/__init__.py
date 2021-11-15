"""
.. _adapter.json.__init__:

This package contains functionality for serialization and deserialization of PyI40AAS objects into/from JSON.

:ref:`json_serialization <adapter.json.json_serialization>`: The module offers a function to write an ObjectStore to a
given file and therefore defines the custom JSONEncoder :class:`~.aas.adapter.json.json_serialization.AASToJsonEncoder`
which handles encoding of all PyI40AAS objects and their attributes by converting them into standard python objects.

:ref:`json_deserialization <adapter.json.json_deserialization>`: The module implements custom JSONDecoder classes
:class:`~aas.adapter.json.json_deserialization.AASFromJsonDecoder` and
:class:`~aas.adapter.json.json_deserialization.StrictAASFromJsonDecoder`, that — when used with Python's `json`
module — detect AAS objects in the parsed JSON and convert them into the corresponding PyI40AAS object.
A function :meth:`~aas.adapter.json.json_deserialization.read_aas_json_file` is provided to read all AAS objects
within a JSON file and return them as PyI40AAS ObjectStore.
"""
import os.path

from .json_serialization import AASToJsonEncoder, StrippedAASToJsonEncoder, write_aas_json_file, object_store_to_json
from .json_deserialization import AASFromJsonDecoder, StrictAASFromJsonDecoder, StrippedAASFromJsonDecoder, \
    StrictStrippedAASFromJsonDecoder, read_aas_json_file, read_aas_json_file_into

JSON_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'aasJSONSchema.json')
