import abc
from typing import MutableSet, Iterator, Generic, TypeVar, Dict, List, Optional

from .base import Identifier, Identifiable


class AbstractRegistry(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for registries and registry proxy objects, that allow to resolve global identifiers to
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


_IT = TypeVar('_IT', bound=Identifiable)


class AbstractObjectStore(AbstractRegistry, MutableSet[_IT], Generic[_IT], metaclass=abc.ABCMeta):
    """
    Abstract baseclass of for local containers for storage of Identifiable objects, that can be used as Registry to
    retrieve the stored objects by Identifier.
    """
    pass


class DictObjectStore(AbstractObjectStore[_IT], Generic[_IT]):
    """
    A local in-memory object store for Identifiable Objects, backed by a dict, mapping Identifier → Identifiable
    """
    def __init__(self):
        self._backend: Dict[Identifier, _IT] = {}

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


class RegistryMultiplexer(AbstractRegistry):
    """
    A multiplexer for Registries of Identifiable objects.

    This class combines multiple Registries of Identifiable objects into a single one to allow retrieving Identifiable
    objects from different sources. It implements the AbstractRegistry interface to be used as Registry itself.

    :ivar registries: A list of registries to query when looking up an object
    """
    def __init__(self, registries: Optional[List[AbstractRegistry]] = None):
        self.registries: List[AbstractRegistry] = registries if registries is not None else []

    def get_identifiable(self, identifier: Identifier) -> Identifiable:
        for registry in self.registries:
            try:
                return registry.get_identifiable(identifier)
            except KeyError:
                pass
        raise KeyError("Identifier could not be found in any of the {} consulted registries."
                       .format(len(self.registries)))
