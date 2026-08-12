# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import json
from pathlib import Path
from typing import IO, Dict, Iterable, Iterator, Union

from basyx.aas import model
from basyx.aas.model import provider as sdk_provider

from app import adapter
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
    Load AAS/Submodel descriptor JSON files from a directory into a :class:`DictDescriptorStore`.

    :param directory: Path to the directory containing JSON descriptor files
    :return: Populated :class:`DictDescriptorStore`
    """
    store = DictDescriptorStore()
    directory = Path(directory)

    for file in directory.iterdir():
        if not file.is_file() or file.suffix.lower() != ".json":
            continue
        with open(file) as f:
            data = json.load(f, cls=adapter.ServerAASFromJsonDecoder)
        for item in data.get("assetAdministrationShellDescriptors", []):
            if isinstance(item, descriptor.AssetAdministrationShellDescriptor):
                try:
                    store.add(item)
                except KeyError:
                    pass
        for item in data.get("submodelDescriptors", []):
            if isinstance(item, descriptor.SubmodelDescriptor):
                try:
                    store.add(item)
                except KeyError:
                    pass

    return store
