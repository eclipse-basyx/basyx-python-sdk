from typing import Iterable, Dict, TypeVar, Iterator

from basyx.aas import model
from basyx.aas.model import provider as sdk_provider

from app.model.descriptor import Descriptor

_DESCRIPTOR_TYPE = TypeVar("_DESCRIPTOR_TYPE", bound=Descriptor)

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
            raise KeyError("Descriptor object with same id {} is already stored in this store"
                           .format(x.id))
        self._backend[x.id] = x

    def discard(self, x: _DESCRIPTOR_TYPE) -> None:
        if self._backend.get(x.id) is x:
            del self._backend[x.id]

    def __contains__(self, x: object) -> bool:
        if isinstance(x, model.Identifier):
            return x in self._backend
        if not isinstance(x, Descriptor):
            return False
        return self._backend.get(x.id) is x

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_DESCRIPTOR_TYPE]:
        return iter(self._backend.values())
