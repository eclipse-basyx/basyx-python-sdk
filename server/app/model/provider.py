from pathlib import Path
from typing import IO, Dict, Iterable, Iterator, Union

from basyx.aas import model
from basyx.aas.model import provider as sdk_provider

import app.adapter as adapter
from app.model import descriptor

PathOrIO = Union[Path, IO]


_DESCRIPTOR_TYPE = Union[descriptor.AssetAdministrationShellDescriptor, descriptor.SubmodelDescriptor]
_DESCRIPTOR_CLASSES = (descriptor.AssetAdministrationShellDescriptor, descriptor.SubmodelDescriptor)


class DictDescriptorStore(sdk_provider.AbstractObjectStore[model.Identifier, _DESCRIPTOR_TYPE]):
    """
    A local in-memory object store for :class:`~app.model.descriptor.Descriptor` objects, backed by a dict, mapping
    :class:`~basyx.aas.model.base.Identifier` → :class:`~app.model.descriptor.Descriptor`
    """

    def __init__(self, descriptors: Iterable[_DESCRIPTOR_TYPE] = ()) -> None:
        self._backend: Dict[model.Identifier, _DESCRIPTOR_TYPE] = {}
        for x in descriptors:
            self.add(x)

    def get_item(self, identifier: model.Identifier) -> _DESCRIPTOR_TYPE:
        return self._backend[identifier]

    def add(self, x: _DESCRIPTOR_TYPE) -> None:
        if x.id in self._backend and self._backend.get(x.id) is not x:
            raise KeyError("Descriptor object with same id {} is already stored in this store".format(x.id))
        self._backend[x.id] = x

    def discard(self, x: _DESCRIPTOR_TYPE) -> None:
        if self._backend.get(x.id) is x:
            del self._backend[x.id]

    def __contains__(self, x: object) -> bool:
        if isinstance(x, model.Identifier):
            return x in self._backend
        if not isinstance(x, _DESCRIPTOR_CLASSES):
            return False
        return self._backend.get(x.id) is x

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_DESCRIPTOR_TYPE]:
        return iter(self._backend.values())


def load_directory(directory: Union[Path, str]) -> DictDescriptorStore:
    """
    Create a new :class:`~basyx.aas.model.provider.DictIdentifiableStore` and use it to load Asset Administration Shell
    and Submodel files in ``AASX``, ``JSON`` and ``XML`` format from a given directory into memory. Additionally, load
    all embedded supplementary files into a new :class:`~basyx.aas.adapter.aasx.DictSupplementaryFileContainer`.

    :param directory: :class:`~pathlib.Path` or ``str`` pointing to the directory containing all Asset Administration
        Shell and Submodel files to load
    :return: Tuple consisting of a :class:`~basyx.aas.model.provider.DictIdentifiableStore` and a
        :class:`~basyx.aas.adapter.aasx.DictSupplementaryFileContainer` containing all loaded data
    """

    dict_descriptor_store: DictDescriptorStore = DictDescriptorStore()

    directory = Path(directory)

    for file in directory.iterdir():
        if not file.is_file():
            continue

        suffix = file.suffix.lower()
        if suffix == ".json":
            with open(file) as f:
                adapter.read_server_aas_json_file_into(dict_descriptor_store, f)

    return dict_descriptor_store
