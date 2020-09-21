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
TODO
"""
import abc
import re
from typing import List, Dict, Type


class Backend(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def commit_object(cls,
                      committed_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:
        """
        TODO
        :param committed_object:
        :param store_object:
        :param relative_path:
        """
        pass

    @classmethod
    @abc.abstractmethod
    def update_object(cls,
                      updated_object: "Referable",  # type: ignore
                      store_object: "Referable",  # type: ignore
                      relative_path: List[str]) -> None:
        """
        TODO
        :param updated_object:
        :param store_object:
        :param relative_path:
        """
        pass


# Global registry for backends by URI scheme
# TODO allow multiple backends per scheme with priority
_backends_map: Dict[str, Type[Backend]] = {}


def register_backend(scheme: str, backend_class: Type[Backend]) -> None:
    """
    TODO
    :param scheme:
    :param backend_class:
    """
    # TODO handle multiple backends per scheme
    _backends_map[scheme] = backend_class


RE_URI_SCHEME = re.compile(r"^([a-zA-Z][a-zA-Z+\-\.]*):")


def get_backend(url: str) -> Type[Backend]:
    """
    TODO
    :param url:
    :return:
    """
    # TODO handle multiple backends per scheme
    scheme_match = RE_URI_SCHEME.match(url)
    if not scheme_match:
        raise ValueError("{} is not a valid URL with URI scheme.".format(url))
    scheme = scheme_match[1]
    try:
        return _backends_map[scheme]
    except KeyError as e:
        raise UnknownBackendException("Could not find Backend for source '{}'".format(url)) from e


# #################################################################################################
# Custom Exception classes for reporting errors during interaction with Backends
class BackendError(Exception):
    """Base class of all exceptions raised by the backends module"""
    pass


class UnknownBackendException(BackendError):
    """Raised, if the backend is not found in the registry"""
    pass


class BackendNotAvailableException(BackendError):
    """Raised, if the backend does exist in the registry, but is not available for some reason"""
    pass
