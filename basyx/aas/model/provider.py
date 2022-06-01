# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements Registries for the AAS, in order to enable resolving global
:class:`Identifiers <aas.model.base.Identifier>`; and mapping :class:`Identifiers <aas.model.base.Identifier>` to
:class:`~aas.model.base.Identifiable` objects.
"""

import abc
from typing import MutableSet, Iterator, Generic, TypeVar, Dict, List, Optional, Iterable

from .base import Identifier, Identifiable


class AbstractObjectProvider(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for all objects, that allow to retrieve :class:`~aas.model.base.Identifiable` objects
    (resp. proxy objects for remote :class:`~aas.model.base.Identifiable` objects) by their
    :class:`~aas.model.base.Identifier`.

    This includes local object stores, database clients and AAS API clients.
    """
    @abc.abstractmethod
    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        """
        Find an :class:`~aas.model.base.Identifiable` by its :class:`~aas.model.base.Identifier`

        This may include looking up the object's endpoint in a registry and fetching it from an HTTP server or a
        database.

        :param identifier: :class:`~aas.model.base.Identifier` of the object to return
        :return: The :class:`~aas.model.base.Identifiable` object (or a proxy object for a remote
                 :class:`~aas.model.base.Identifiable` object)
        :raises KeyError: If no such :class:`~.aas.model.base.Identifiable` can be found
        """
        pass

    def get(self, identifier: Identifier, default: Optional[Identifiable] = None) -> Optional[Identifiable]:
        """
        Find an object in this set by its :class:`identification <aas.model.base.Identifier>`, with fallback parameter

        :param identifier: :class:`~aas.model.base.Identifier` of the object to return
        :param default: An object to be returned, if no object with the given
                        :class:`identification <aas.model.base.Identifier>` is found
        :return: The :class:`~aas.model.base.Identifiable` object with the given
                 :class:`identification <aas.model.base.Identifier>` in the provider. Otherwise the `default` object
                 or None, if none is given.
        """
        try:
            return self.get_identifiable(identifier)
        except KeyError:
            return default


_IT = TypeVar('_IT', bound=Identifiable)


class AbstractObjectStore(AbstractObjectProvider, MutableSet[_IT], Generic[_IT], metaclass=abc.ABCMeta):
    """
    Abstract baseclass of for container-like objects for storage of :class:`~aas.model.base.Identifiable` objects.

    ObjectStores are special ObjectProvides that – in addition to retrieving objects by
    :class:`~aas.model.base.Identifier` – allow to add and delete objects (i.e. behave like a Python set).
    This includes local object stores (like :class:`~.DictObjectStore`) and database
    :class:`Backends <aas.backend.backends.Backend>`.

    The AbstractObjectStore inherits from the `MutableSet` abstract collections class and therefore implements all the
    functions of this class.
    """
    @abc.abstractmethod
    def __init__(self):
        pass

    def update(self, other: Iterable[_IT]) -> None:
        for x in other:
            self.add(x)


class DictObjectStore(AbstractObjectStore[_IT], Generic[_IT]):
    """
    A local in-memory object store for :class:`~aas.model.base.Identifiable` objects, backed by a dict, mapping
    :class:`~aas.model.base.Identifier` → :class:`~aas.model.base.Identifiable`
    """
    def __init__(self, objects: Iterable[_IT] = ()) -> None:
        super().__init__()
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
    A multiplexer for Providers of :class:`~aas.model.base.Identifiable` objects.

    This class combines multiple registries of :class:`~aas.model.base.Identifiable` objects into a single one to allow
    retrieving :class:`~aas.model.base.Identifiable` objects from different sources.
    It implements the :class:`~.AbstractObjectProvider` interface to be used as registry itself.

    :ivar registries: A list of :class:`AbstractObjectProviders <.AbstractObjectProvider>` to query when looking up an
                      object
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
