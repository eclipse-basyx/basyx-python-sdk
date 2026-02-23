# Copyright (c) 2026 the Eclipse BaSyx Authors
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


_KEY = TypeVar('_KEY')  # Generic key type
_VALUE = TypeVar('_VALUE')  # Generic value type


class AbstractObjectProvider(Generic[_KEY, _VALUE], metaclass=abc.ABCMeta):
    """
    Abstract base class for all objects that allow retrieving values by a key.

    This includes local object stores, database clients and AAS API clients.
    """

    @abc.abstractmethod
    def get_item(self, key: _KEY) -> _VALUE:
        """Retrieve the item or raise a KeyError."""
        pass

    def get(self, key: _KEY, default: Optional[_VALUE] = None) -> Optional[_VALUE]:
        """Retrieve the item or return a default value."""
        try:
            return self.get_item(key)
        except KeyError:
            return default


class AbstractObjectStore(AbstractObjectProvider[_KEY, _VALUE], MutableSet[_VALUE]):
    """
    Abstract base class for container-like objects for storage of values.

    ObjectStores are special ObjectProviders that, in addition to retrieving values by a key, allow adding and deleting
    values (i.e. behave like a Python set). This includes local IdentifiableStores (like
    :class:`~.DictIdentifiableStore`) and specific IdentifiableStores (like
    :class:`~basyx.aas.backend.couchdb.CouchDBIdentifiableStore` and
    :class:`~basyx.aas.backend.local_file.LocalFileIdentifiableStore`).

    The AbstractObjectStore inherits from the :class:`~collections.abc.MutableSet` abstract collections class and
    therefore implements all the functions of this class.
    """

    @abc.abstractmethod
    def __init__(self):
        pass

    def update(self, other: Iterable[_VALUE]) -> None:
        for x in other:
            self.add(x)

    def sync(self, other: Iterable[_VALUE], overwrite: bool) -> Tuple[int, int, int]:
        """
        Merge values from an :class:`~collections.abc.Iterable` into this
        :class:`~basyx.aas.model.provider.AbstractObjectStore`.

        :param other: :class:`~collections.abc.Iterable` to sync with
        :param overwrite: Flag to overwrite existing values in this
            :class:`~basyx.aas.model.provider.AbstractObjectStore` with updated versions from ``other``,
            values unique to this :class:`~basyx.aas.model.provider.AbstractObjectStore` are always preserved
        :return: Counts of processed values as``(added, overwritten, skipped)``
        """
        added, overwritten, skipped = 0, 0, 0
        for value in other:
            if value in self:
                if overwrite:
                    self.discard(value)
                    self.add(value)
                    overwritten += 1
                else:
                    skipped += 1
            else:
                self.add(value)
                added += 1
        return added, overwritten, skipped


class ObjectProviderMultiplexer(AbstractObjectProvider[_KEY, _VALUE]):
    """
    A multiplexer for :class:`AbstractObjectProviders <.AbstractObjectProvider>`.

    This class combines multiple :class:`AbstractObjectProviders <.AbstractObjectProvider>` into a single one to allow
    retrieving values from different sources. It implements the :class:`~.AbstractObjectProvider` interface to be used
    as registry itself.

    :param registries: A list of :class:`AbstractObjectProviders <.AbstractObjectProvider>` to query when looking up a
        key
    """

    def __init__(self, registries: Optional[List[AbstractObjectProvider[_KEY, _VALUE]]] = None) -> None:
        self.providers: List[AbstractObjectProvider[_KEY, _VALUE]] = registries if registries is not None else []

    def get_item(self, key: _KEY) -> _VALUE:
        for provider in self.providers:
            try:
                return provider.get_item(key)
            except KeyError:
                pass
        raise KeyError("Key could not be found in any of the {} consulted registries."
                       .format(len(self.providers)))


_IDENTIFIABLE = TypeVar('_IDENTIFIABLE', bound=Identifiable)


class DictIdentifiableStore(AbstractObjectStore[Identifier, _IDENTIFIABLE]):
    """
    A local in-memory object store for :class:`~basyx.aas.model.base.Identifiable` objects, backed by a dict, mapping
    :class:`~basyx.aas.model.base.Identifier` → :class:`~basyx.aas.model.base.Identifiable`

    .. note::
        The `DictIdentifiableStore` provides efficient retrieval of objects by their
        :class:`~basyx.aas.model.base.Identifier`. However, since object stores are not referenced via the parent
        attribute, the mapping is not updated if the :class:`~basyx.aas.model.base.Identifier` of an
        :class:`~basyx.aas.model.base.Identifiable` changes. For more details, see
        [issue #216](https://github.com/eclipse-basyx/basyx-python-sdk/issues/216). As a result, the
        `DictIdentifiableStore` is unsuitable for storing objects whose :class:`~basyx.aas.model.base.Identifier` may
        change. In such cases, consider using a :class:`~.SetIdentifiableStore` instead.
    """

    def __init__(self, identifiables: Iterable[_IDENTIFIABLE] = ()) -> None:
        self._backend: Dict[Identifier, _IDENTIFIABLE] = {}
        for x in identifiables:
            self.add(x)

    def get_item(self, identifier: Identifier) -> _IDENTIFIABLE:
        return self._backend[identifier]

    def add(self, x: _IDENTIFIABLE) -> None:
        if x.id in self._backend and self._backend.get(x.id) is not x:
            raise KeyError("Identifiable object with same id {} is already stored in this store"
                           .format(x.id))
        self._backend[x.id] = x

    def discard(self, x: _IDENTIFIABLE) -> None:
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

    def __iter__(self) -> Iterator[_IDENTIFIABLE]:
        return iter(self._backend.values())


class DictObjectStore(DictIdentifiableStore[_IDENTIFIABLE]):
    """
    `DictObjectStore` has been renamed to :class:`~.DictIdentifiableStore` and will be removed in a future release.
    Please migrate to :class:`~.DictIdentifiableStore`.
    """

    def __init__(self, identifiables: Iterable[_IDENTIFIABLE] = ()) -> None:
        warnings.warn(
            "`DictObjectStore` is deprecated and will be removed in a future release. Use "
            "`DictIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(identifiables)

    def get_identifiable(self, identifier: Identifier) -> _IDENTIFIABLE:
        warnings.warn(
            "`get_identifiable()` is deprecated. Use `get_item()` from `DictIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().get_item(identifier)


class SetIdentifiableStore(AbstractObjectStore[Identifier, _IDENTIFIABLE]):
    """
    A local in-memory object store for :class:`~basyx.aas.model.base.Identifiable` objects, backed by a set

    .. note::
        The `SetIdentifiableStore` is slower than the `DictIdentifiableStore` for retrieval of objects, because it has
        to iterate over all objects to find the one with the correct :class:`~basyx.aas.model.base.Identifier`.
        On the other hand, the `SetIdentifiableStore` is more secure, because it is less affected by changes in the
        :class:`~basyx.aas.model.base.Identifier` of an :class:`~basyx.aas.model.base.Identifiable` object.
        Therefore, the `SetIdentifiableStore` is suitable for storing objects whose
        :class:`~basyx.aas.model.base.Identifier` may change.
    """

    def __init__(self, objects: Iterable[_IDENTIFIABLE] = ()) -> None:
        self._backend: Set[_IDENTIFIABLE] = set()
        for x in objects:
            self.add(x)

    def get_item(self, identifier: Identifier) -> _IDENTIFIABLE:
        for x in self._backend:
            if x.id == identifier:
                return x
        raise KeyError(identifier)

    def add(self, x: _IDENTIFIABLE) -> None:
        if x in self:
            # Object is already in store
            return
        try:
            self.get_item(x.id)
        except KeyError:
            self._backend.add(x)
        else:
            raise KeyError(f"Identifiable object with same id {x.id} is already stored in this store")

    def discard(self, x: _IDENTIFIABLE) -> None:
        self._backend.discard(x)

    def remove(self, x: _IDENTIFIABLE) -> None:
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

    def __iter__(self) -> Iterator[_IDENTIFIABLE]:
        return iter(self._backend)


class SetObjectStore(SetIdentifiableStore[_IDENTIFIABLE]):
    """
    `SetObjectStore` has been renamed to :class:`~.SetIdentifiableStore` and will be removed in a future release.
    Please migrate to :class:`~.SetIdentifiableStore`.
    """

    def __init__(self, objects: Iterable[_IDENTIFIABLE] = ()) -> None:
        warnings.warn(
            "`SetObjectStore` is deprecated and will be removed in a future release. Use `SetIdentifiableStore`"
            "instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(objects)

    def get_identifiable(self, identifier: Identifier) -> _IDENTIFIABLE:
        warnings.warn(
            "`get_identifiable()` is deprecated. Use `get_item()` from `SetIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().get_item(identifier)
