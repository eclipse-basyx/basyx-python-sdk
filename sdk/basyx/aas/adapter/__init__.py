"""
This package contains different kinds of adapters.

* :ref:`json <adapter.json.__init__>`: This package offers an adapter for serialization and deserialization of BaSyx
  Python SDK objects to/from JSON.
* :ref:`xml <adapter.xml.__init__>`: This package offers an adapter for serialization and deserialization of BaSyx
  Python SDK objects to/from XML.
* :ref:`aasx <adapter.aasx>`: This package offers functions for reading and writing AASX-files.
"""

from basyx.aas.adapter.aasx import AASXReader, DictSupplementaryFileContainer
from basyx.aas.adapter.json import read_aas_json_file_into
from basyx.aas.adapter.xml import read_aas_xml_file_into
from basyx.aas.model.provider import DictObjectStore
from pathlib import Path
from typing import Union


def load_directory(directory: Union[Path, str]) -> tuple[DictObjectStore, DictSupplementaryFileContainer]:
    """
    Create a new :class:`~basyx.aas.model.provider.DictObjectStore` and use it to load Asset Administration Shell and
    Submodel files in ``AASX``, ``JSON`` and ``XML`` format from a given directory into memory. Additionally, load all
    embedded supplementary files into a new :class:`~basyx.aas.adapter.aasx.DictSupplementaryFileContainer`.

    :param directory: :class:`~pathlib.Path` or ``str`` pointing to the directory containing all Asset Administration
        Shell and Submodel files to load
    :return: Tuple consisting of a :class:`~basyx.aas.model.provider.DictObjectStore` and a
        :class:`~basyx.aas.adapter.aasx.DictSupplementaryFileContainer` containing all loaded data
    """

    dict_object_store: DictObjectStore = DictObjectStore()
    file_container: DictSupplementaryFileContainer = DictSupplementaryFileContainer()

    directory = Path(directory)

    for file in directory.iterdir():
        if not file.is_file():
            continue

        suffix = file.suffix.lower()
        if suffix == ".json":
            with open(file) as f:
                read_aas_json_file_into(dict_object_store, f)
        elif suffix == ".xml":
            with open(file) as f:
                read_aas_xml_file_into(dict_object_store, f)
        elif suffix == ".aasx":
            with AASXReader(file) as reader:
                reader.read_into(object_store=dict_object_store, file_store=file_container)

    return dict_object_store, file_container
