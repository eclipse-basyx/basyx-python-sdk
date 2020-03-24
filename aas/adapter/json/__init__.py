"""
This package contains functionality for serialization and deserialization of PyI40AAS objects into/from JSON.

json_serialization:
    The module offers a function to write an ObjectStore to a given file and therefore defines the custom JSONEncoder
    `AASToJsonEncoder` which handles encoding of all PyI40AAS objects and their attributes by converting them into
    standard python objects.

json_deserialization.py
    The module implements custom JSONDecoder classes `AASFromJsonDecoder` and `StrictAASFromJsonDecoder`, that — when
    used with Python's `json` module — detect AAS objects in the parsed JSON and convert them into the corresponding
    PyI40AAS object. A function `read_json_aas_file()` is provided to read all AAS objects within a JSON file and return
    them as PyI40AAS ObjectStore.
"""
