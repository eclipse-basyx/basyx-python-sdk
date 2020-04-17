# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
This module implements Registries for the AAS, in order to enable resolving global identifiers; and
mapping identifiers to identifiable objects.
"""

import abc
from typing import MutableSet, Iterator, Generic, TypeVar, Dict, List, Optional, Iterable

from .base import Identifier, Identifiable


class AbstractObjectProvider(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for all objects, that allow to retrieve Identifiable objects (resp. proxy objects for remote
    Identifiable objects) by their Identifier.

    This includes local object stores, database clients and AAS API clients.
    """
    @abc.abstractmethod
    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        """
        Find an Identifiable by its id_short

        This may include looking up the object's endpoint in a registry and fetching it from an HTTP server or a
        database.

        :param identifier:
        :return: The Identifiable object (or a proxy object for a remote Identifiable object)
        :raises KeyError: If no such Referable can be found
        """
        pass

    def get(self, identifier: Identifier, default: Optional[Identifiable] = None) -> Optional[Identifiable]:
        """
        Find an object in this set by its identification, with fallback parameter

        :param default: An object to be returned, if no object with the given identification is found
        :return: The Identifiable object with the given identification in the provider. Otherwise the `default` object
                 or None, if none is given.
        """
        try:
            return self.get_identifiable(identifier)
        except KeyError:
            return default


_IT = TypeVar('_IT', bound=Identifiable)


class AbstractObjectStore(AbstractObjectProvider, MutableSet[_IT], Generic[_IT], metaclass=abc.ABCMeta):
    """
    Abstract baseclass of for container-like objects for storage of Identifiable objects.

    ObjectStores are special ObjectProvides that – in addition to retrieving objects by Identifier – allow to add and
    delete objects (i.e. behave like a Python set). This includes local object stores (like `DictObjectStore`) and
    database clients.
    """
    pass

    def update(self, other: Iterable[_IT]) -> None:
        for x in other:
            self.add(x)


class DictObjectStore(AbstractObjectStore[_IT], Generic[_IT]):
    """
    A local in-memory object store for Identifiable Objects, backed by a dict, mapping Identifier → Identifiable
    """
    def __init__(self, objects: Iterable[_IT] = ()) -> None:
        self._backend: Dict[Identifier, _IT] = {}
        for x in objects:
            self.add(x)

    def get_identifiable(self, identifier: Identifier) -> _IT:
        return self._backend[identifier]

    def add(self, x: _IT) -> None:
        if x.identification in self._backend and self._backend.get(x.identification) is not x:
            raise KeyError("Identifiable object with same identification {} is already stored in this store"
                           .format(x.identification))
        self._backend[x.identification] = x

    def discard(self, x: _IT) -> None:
        if self._backend.get(x.identification) is x:
            del self._backend[x.identification]

    def __contains__(self, x: object) -> bool:
        if isinstance(x, Identifier):
            return x in self._backend
        if not isinstance(x, Identifiable):
            return False
        return self._backend.get(x.identification) is x

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_IT]:
        return iter(self._backend.values())


class ObjectProviderMultiplexer(AbstractObjectProvider):
    """
    A multiplexer for Providers of Identifiable objects.

    This class combines multiple Registries of Identifiable objects into a single one to allow retrieving Identifiable
    objects from different sources. It implements the AbstractObjectProvider interface to be used as Registry itself.

    :ivar registries: A list of registries to query when looking up an object
    """
    def __init__(self, registries: Optional[List[AbstractObjectProvider]] = None):
        self.providers: List[AbstractObjectProvider] = registries if registries is not None else []

    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        for provider in self.providers:
            try:
                return provider.get_identifiable(identifier)
            except KeyError:
                pass
        raise KeyError("Identifier could not be found in any of the {} consulted registries."
                       .format(len(self.providers)))
