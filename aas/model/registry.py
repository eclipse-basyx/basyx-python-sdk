import abc
from typing import MutableSet, Iterator, Generic, TypeVar, Dict, List

from .base import Identifier, Identifiable


class AbstractRegistry(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for registries and registry proxy objects, that allow to resolve global identifieres to
    Identifiable objects (resp. proxy objects for remote Identifiable objects).
    """
    @abc.abstractmethod
    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        """
        Find a Referable in this Namespaces by its id_short

        :param identifier:
        :return: The Identifiable object (or a proxy object for a remote Identifiable object)
        :raises KeyError: If no such Referable can be found
        """
        pass


T = TypeVar('T', bound=Identifiable)


class AbstractObjectStore(AbstractRegistry, MutableSet[T], Generic[T], metaclass=abc.ABCMeta):
    """
    Abstract baseclass of for local containers for storage of Identifiable objects, that can be used as Registry to
    retrieve the stored objects by Identifier.
    """
    pass


class DictObjectStore(AbstractObjectStore[T], Generic[T]):
    """
    A local in-memory object store for Identifiable Objects, backed by a dict, mapping Identifier → Identifiable
    """
    def __init__(self):
        self._backend: Dict[Identifier, T] = {}

    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        return self._backend[identifier]

    def add(self, x: T) -> None:
        if x.identification in self._backend and self._backend.get(x.identification) is not x:
            raise KeyError("Identifiable object with same identification {} is already stored in this store"
                           .format(x.identification))
        self._backend[x.identification] = x

    def discard(self, x: T) -> None:
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

    def __iter__(self) -> Iterator[T]:
        return iter(self._backend.values())


class RegistryMultiplexer(AbstractRegistry):
    """
    A multiplexer for Registries of Identifiable objects.

    This class combines multiple Registries of Identifiable objects into a single one to allow retrieving Identifiable
    objects from different sources. It implements the AbstractRegistry interface to be used as Registry itself.

    :ivar registries: A list of registries to query when looking up an object
    """
    def __init__(self):
        self.registries: List[AbstractRegistry] = []

    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        for registry in self.registries:
            try:
                return registry.get_identifiable(identifier)
            except KeyError:
                pass
        raise KeyError("Identifier could not be found in any of the {} consulted registries."
                       .format(len(self.registries)))
