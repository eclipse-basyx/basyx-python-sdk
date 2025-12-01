# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module implements Registries for the AAS, in order to enable resolving global
:class:`Identifiers <basyx.aas.model.base.Identifier>`; and mapping
:class:`Identifiers <basyx.aas.model.base.Identifier>` to :class:`~basyx.aas.model.base.Identifiable` objects.
"""

import abc
import warnings
from typing import MutableSet, Iterator, Generic, TypeVar, Dict, List, Optional, Iterable, Set, Tuple

from .base import Identifier, Identifiable


_K = TypeVar('_K')
_V = TypeVar('_V')


class AbstractObjectProvider(Generic[_K, _V], metaclass=abc.ABCMeta):
    """
    Documentation when we agree on this solution.
    """

    @abc.abstractmethod
    def get_item(self, key: _K) -> _V:
        """Retrieve the item or raise a KeyError."""
        pass

    def get(self, key: _K, default: Optional[_V] = None) -> Optional[_V]:
        """Retrieve the item or return a default value."""
        try:
            return self.get_item(key)
        except KeyError:
            return default


class AbstractObjectStore(AbstractObjectProvider[_K, _V], MutableSet[_V]):
    """
    Abstract baseclass of for container-like objects for storage of :class:`~basyx.aas.model.base.Identifiable` objects.

    ObjectStores are special ObjectProvides that – in addition to retrieving objects by
    :class:`~basyx.aas.model.base.Identifier` – allow to add and delete objects (i.e. behave like a Python set).
    This includes local object stores (like :class:`~.DictObjectStore`) and specific object stores
    (like :class:`~basyx.aas.backend.couchdb.CouchDBObjectStore` and
    :class:`~basyx.aas.backend.local_file.LocalFileObjectStore`).

    The AbstractObjectStore inherits from the :class:`~collections.abc.MutableSet` abstract collections class and
    therefore implements all the functions of this class.
    """

    @abc.abstractmethod
    def __init__(self):
        pass

    def update(self, other: Iterable[_V]) -> None:
        for x in other:
            self.add(x)

    def sync(self, other: Iterable[_V], overwrite: bool) -> Tuple[int, int, int]:
        """
        Merge :class:`Identifiables <basyx.aas.model.base.Identifiable>` from an
        :class:`~collections.abc.Iterable` into this :class:`~basyx.aas.model.provider.AbstractObjectStore`.

        :param other: :class:`~collections.abc.Iterable` to sync with
        :param overwrite: Flag to overwrite existing :class:`Identifiables <basyx.aas.model.base.Identifiable>` in this
            :class:`~basyx.aas.model.provider.AbstractObjectStore` with updated versions from ``other``,
            :class:`Identifiables <basyx.aas.model.base.Identifiable>` unique to this
            :class:`~basyx.aas.model.provider.AbstractObjectStore` are always preserved
        :return: Counts of processed :class:`Identifiables <basyx.aas.model.base.Identifiable>` as
            ``(added, overwritten, skipped)``
        """
        added, overwritten, skipped = 0, 0, 0
        for value in other:
            if value in self:
                if overwrite:

                    # TODO: This is a quick fix. Yes it works. The underlying problem with the subclass
                    # `LocalFileIdentifiableStore` will be solved in a separate issue
                    # (https://github.com/eclipse-basyx/basyx-python-sdk/issues/438).
                    # Think of this as pythonic duct tape.
                    #
                    # The problem is that the `_object_cache` isn't initialised together with the
                    # `LocalFileIdentifiableStore`, leading to an error when `discard()` is called on the empty cache.
                    # The for-loop calls `__iter__` calls `get_identifiable_by_hash()` calls
                    # `self._object_cache[obj.id] = obj`, adding all identifiables to the cache and therefore avoiding
                    # the error.
                    for element in self:
                        pass

                    self.discard(value)
                    self.add(value)
                    overwritten += 1
                else:
                    skipped += 1
            else:
                self.add(value)
                added += 1
        return added, overwritten, skipped


_IT = TypeVar('_IT', bound=Identifiable)


class DictIdentifiableStore(AbstractObjectStore[Identifier, _IT]):
    """
    A local in-memory object store for :class:`~basyx.aas.model.base.Identifiable` objects, backed by a dict, mapping
    :class:`~basyx.aas.model.base.Identifier` → :class:`~basyx.aas.model.base.Identifiable`

    .. note::
        The `DictObjectStore` provides efficient retrieval of objects by their :class:`~basyx.aas.model.base.Identifier`
        However, since object stores are not referenced via the parent attribute, the mapping is not updated
        if the :class:`~basyx.aas.model.base.Identifier` of an :class:`~basyx.aas.model.base.Identifiable` changes.
        For more details, see [issue #216](https://github.com/eclipse-basyx/basyx-python-sdk/issues/216).
        As a result, the `DictObjectStore` is unsuitable for storing objects whose
        :class:`~basyx.aas.model.base.Identifier` may change.
        In such cases, consider using a :class:`~.SetObjectStore` instead.
    """

    def __init__(self, iterables: Iterable[_IT] = ()) -> None:
        self._backend: Dict[Identifier, _IT] = {}
        for x in iterables:
            self.add(x)

    def get_item(self, identifier: Identifier) -> _IT:
        return self._backend[identifier]

    def add(self, x: _IT) -> None:
        if x.id in self._backend and self._backend.get(x.id) is not x:
            raise KeyError("Identifiable object with same id {} is already stored in this store"
                           .format(x.id))
        self._backend[x.id] = x

    def discard(self, x: _IT) -> None:
        if self._backend.get(x.id) is x:
            del self._backend[x.id]

    def __contains__(self, x: object) -> bool:
        if isinstance(x, Identifier):
            return x in self._backend
        if not isinstance(x, Identifiable):
            return False
        return self._backend.get(x.id) is x

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_IT]:
        return iter(self._backend.values())


class DictObjectStore(DictIdentifiableStore):
    """
    `DictObjectStore` has been renamed to :class:`~.DictIdentifiableStore` and will be removed in a future release.
    Please migrate to :class:`~.DictIdentifiableStore`.
    """
    def __init__(self, iterables: Iterable[_IT] = ()) -> None:
        warnings.warn(
            "`DictObjectStore` is deprecated and will be removed in a future release. Use "
            "`DictIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(iterables)


class SetIdentifiableStore(AbstractObjectStore[Identifier, _IT]):
    """
    A local in-memory object store for :class:`~basyx.aas.model.base.Identifiable` objects, backed by a set

    .. note::
        The `SetObjectStore` is slower than the `DictObjectStore` for retrieval of objects, because it has to iterate
        over all objects to find the one with the correct :class:`~basyx.aas.model.base.Identifier`.
        On the other hand, the `SetObjectStore` is more secure, because it is less affected by changes in the
        :class:`~basyx.aas.model.base.Identifier` of an :class:`~basyx.aas.model.base.Identifiable` object.
        Therefore, the `SetObjectStore` is suitable for storing objects whose :class:`~basyx.aas.model.base.Identifier`
        may change.
    """

    def __init__(self, objects: Iterable[_IT] = ()) -> None:
        self._backend: Set[_IT] = set()
        for x in objects:
            self.add(x)

    def get_item(self, identifier: Identifier) -> _IT:
        for x in self._backend:
            if x.id == identifier:
                return x
        raise KeyError(identifier)

    def add(self, x: _IT) -> None:
        if x in self:
            # Object is already in store
            return
        try:
            self.get_item(x.id)
        except KeyError:
            self._backend.add(x)
        else:
            raise KeyError(f"Identifiable object with same id {x.id} is already stored in this store")

    def discard(self, x: _IT) -> None:
        self._backend.discard(x)

    def remove(self, x: _IT) -> None:
        self._backend.remove(x)

    def __contains__(self, x: object) -> bool:
        if isinstance(x, Identifier):
            try:
                self.get_item(x)
                return True
            except KeyError:
                return False
        if not isinstance(x, Identifiable):
            return False
        return x in self._backend

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_IT]:
        return iter(self._backend)


class SetObjectStore(SetIdentifiableStore):
    """
    `SetObjectStore` has been renamed to :class:`~.SetIdentifiableStore` and will be removed in a future release.
    Please migrate to :class:`~.SetIdentifiableStore`.
    """
    def __init__(self, objects: Iterable[_IT] = ()) -> None:
        warnings.warn(
            "`SetObjectStore` is deprecated and will be removed in a future release. Use `SetIdentifiableStore`"
            "instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(objects)


class ObjectProviderMultiplexer(AbstractObjectProvider[_K, _V]):
    """
    A multiplexer for Providers of :class:`~basyx.aas.model.base.Identifiable` objects.

    This class combines multiple registries of :class:`~basyx.aas.model.base.Identifiable` objects into a single one
    to allow retrieving :class:`~basyx.aas.model.base.Identifiable` objects from different sources.
    It implements the :class:`~.AbstractObjectProvider` interface to be used as registry itself.

    :param registries: A list of :class:`AbstractObjectProviders <.AbstractObjectProvider>` to query when looking up an
                      object
    """

    def __init__(self, registries: Optional[List[AbstractObjectProvider[ _K, _V]]] = None) -> None:
        self.providers: List[AbstractObjectProvider[_K, _V]] = registries if registries is not None else []

    def get_item(self, key: _K) -> _V:
        for provider in self.providers:
            try:
                return provider.get_item(key)
            except KeyError:
                pass
        raise KeyError("Key could not be found in any of the {} consulted registries."
                       .format(len(self.providers)))
