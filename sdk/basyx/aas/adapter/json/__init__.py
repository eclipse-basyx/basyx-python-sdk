"""
.. _adapter.json.__init__:

This package contains functionality for serialization and deserialization of BaSyx Python SDK objects into/from JSON.

:ref:`json_serialization <adapter.json.json_serialization>`: The module offers a function to write an ObjectStore to a
given file and therefore defines the custom JSONEncoder
:class:`~basyx.aas.adapter.json.json_serialization.AASToJsonEncoder` which handles encoding of all BaSyx Python SDK
objects and their attributes by converting them into standard python objects.

:ref:`json_deserialization <adapter.json.json_deserialization>`: The module implements custom JSONDecoder classes
:class:`~basyx.aas.adapter.json.json_deserialization.AASFromJsonDecoder` and
:class:`~basyx.aas.adapter.json.json_deserialization.StrictAASFromJsonDecoder`, that — when used with Python's
:mod:`json` module — detect AAS objects in the parsed JSON and convert them into the corresponding BaSyx Python SDK
object. A function :meth:`~basyx.aas.adapter.json.json_deserialization.read_aas_json_file` is provided to read all
AAS objects within a JSON file and return them as BaSyx Python SDK
:class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>`.
"""

from .json_deserialization import (
    AASFromJsonDecoder,
    StrictAASFromJsonDecoder,
    StrictStrippedAASFromJsonDecoder,
    StrippedAASFromJsonDecoder,
    read_aas_json_file,
    read_aas_json_file_into,
)
from .json_serialization import (
    AASToJsonEncoder,
    StrippedAASToJsonEncoder,
    object_store_to_json,
    write_aas_json_file,
)
