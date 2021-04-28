# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
This module implements the basic structures of the AAS metamodel, including the abstract classes and enums needed for
the higher level classes to inherit from.
"""

import abc
import inspect
import itertools
from enum import Enum, unique
from typing import List, Optional, Set, TypeVar, MutableSet, Generic, Iterable, Dict, Iterator, Union, overload, \
    MutableSequence, Type, Any, TYPE_CHECKING, Tuple
import re

from . import datatypes
from ..backend import backends

if TYPE_CHECKING:
    from . import provider

DataTypeDef = Type[datatypes.AnyXSDType]
ValueDataType = datatypes.AnyXSDType  # any xsd atomic type (from .datatypes)
BlobType = bytes
MimeType = str  # any mimetype as in RFC2046
PathType = str
QualifierType = str
# A dict of language-Identifier (according to ISO 639-1 and ISO 3166-1) and string in this language.
# The meaning of the string in each language is the same.
# << Data Type >> Example ["en-US", "germany"]
LangStringSet = Dict[str, str]


@unique
class IdentifierType(Enum):
    """
    Enumeration of different types of Identifiers for global identification

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifier scheme for
                properties and classifications.
    :cvar IRI: IRI according to Rfc 3987. Every URI is an IRI
    :cvar CUSTOM: Custom identifiers like GUIDs (globally unique Identifiers)
    """

    IRDI = 0
    IRI = 1
    CUSTOM = 2


@unique
class KeyElements(Enum):
    """
    Enumeration for denoting which kind of entity is referenced. They can be categorized in ReferableElements,
    IdentifiableElements and other KeyElements

    # IdentifiableElements starting from 0
    :cvar ASSET: asset
    :cvar ASSET_ADMINISTRATION_SHELL: asset administration shell
    :cvar CONCEPT_DESCRIPTION: concept description
    :cvar SUBMODEL: submodel

    # ReferableElements starting from 1000
    :cvar ACCESS_PERMISSION_RULE: access permission rule
    :cvar ANNOTATED_RELATIONSHIP_ELEMENT: annotated relationship element
    :cvar BASIC_EVENT: basic event
    :cvar BLOB: blob
    :cvar CAPABILITY: capability
    :cvar CONCEPT_DICTIONARY: concept dictionary
    :cvar DATA_ELEMENT: data element,
                        Note: Date Element is abstract, i. e. if a key uses "DATA_ELEMENT" the reference may be
                              Property, File etc.
    :cvar ENTITY: entity
    :cvar EVENT: event, Note: Event is abstract
    :cvar FILE: file
    :cvar MULTI_LANGUAGE_PROPERTY: property with a value that can be provided in multiple languages
    :cvar OPERATION: operation
    :cvar PROPERTY: property
    :cvar RANGE: range with min and max
    :cvar REFERENCE_ELEMENT: reference
    :cvar RELATIONSHIP_ELEMENT: relationship
    :cvar SUBMODEL_ELEMENT: submodel element,
                            Note: Submodel Element is abstract, i.e. if a key uses “SUBMODEL_ELEMENT” the reference may
                                  be a Property, a SubmodelElementCollection, an Operation etc.
    :cvar SUBMODEL_ELEMENT_COLLECTION: collection of submodel elements
    :cvar VIEW: view

    # KeyElements starting from 2000
    :cvar GLOBAL_REFERENCE: reference to an element not belonging to an asset administration shel
    :cvar FRAGMENT_REFERENCE: unique reference to an element within a file. The file itself is assumed to be part of an
                             asset administration shell.
    """

    # IdentifiableElements starting from 0
    ASSET = 0
    ASSET_ADMINISTRATION_SHELL = 1
    CONCEPT_DESCRIPTION = 2
    SUBMODEL = 3

    # ReferableElements starting from 1000
    ACCESS_PERMISSION_RULE = 1000
    ANNOTATED_RELATIONSHIP_ELEMENT = 1001
    BASIC_EVENT = 1002
    BLOB = 1003
    CAPABILITY = 1004
    CONCEPT_DICTIONARY = 1005
    DATA_ELEMENT = 1006
    ENTITY = 1007
    EVENT = 1008
    FILE = 1009
    MULTI_LANGUAGE_PROPERTY = 1010
    OPERATION = 1011
    PROPERTY = 1012
    RANGE = 1013
    REFERENCE_ELEMENT = 1014
    RELATIONSHIP_ELEMENT = 1015
    SUBMODEL_ELEMENT = 1016
    SUBMODEL_ELEMENT_COLLECTION = 1017
    VIEW = 1018

    # KeyElements starting from 2000
    GLOBAL_REFERENCE = 2000
    FRAGMENT_REFERENCE = 2001


@unique
class KeyType(Enum):
    """
    Enumeration for denoting the type of the key value.

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifier scheme for
                properties and classifications.
    :cvar IRI: IRI according to Rfc 3987. Every URI is an IRI
    :cvar CUSTOM: Custom identifiers like GUIDs (globally unique Identifiers)
    :cvar IDSHORT: id_short of a referable element
    :cvar FRAGMENT_ID: identifier of a fragment within a file
    """

    IRDI = 0
    IRI = 1
    CUSTOM = 2
    IDSHORT = 3
    FRAGMENT_ID = 4

    @property
    def is_local_key_type(self) -> bool:
        return self in (KeyType.IDSHORT, KeyType.FRAGMENT_ID)


@unique
class EntityType(Enum):
    """
    Enumeration for denoting whether an entity is a self-managed or a co-managed entity

    :cvar CO_MANAGED_ENTITY: For co-managed entities there is no separate AAS. Co-managed entities need to be part of a
                             self-managed entity
    :cvar SELF_MANAGED_ENTITY: Self-managed entities have their own AAS but can be part of the bill of material of a
                               composite self-managed entity. The asset of an I4.0-component is a self-managed entity
                               per definition.
    """

    CO_MANAGED_ENTITY = 0
    SELF_MANAGED_ENTITY = 1


@unique
class ModelingKind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.

    :cvar TEMPLATE: Software element which specifies the common attributes shared by all instances of the template
    :cvar INSTANCE: concrete, clearly identifiable component of a certain template,
                    Note: It becomes an individual entity of a template, for example a device model, by defining
                          specific property values.
                    Note: In an object oriented view, an instance denotes an object of a template (class).
    """

    TEMPLATE = 0
    INSTANCE = 1


@unique
class AssetKind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.

    :cvar TYPE: hardware or software element which specifies the common attributes shared by all instances of the type
    :cvar INSTANCE: concrete, clearly identifiable component of a certain type,
                    Note: It becomes an individual entity of a type, for example a device, by defining specific
                          property values.
                    Note: In an object oriented view, an instance denotes an object of a class (of a type)
    """

    TYPE = 0
    INSTANCE = 1


class Key:
    """
    A key is a reference to an element by its id.

    :ivar type: Denote which kind of entity is referenced. In case type = GlobalReference then the element is a
                global unique id. In all other cases the key references a model element of the same or of another AAS.
                The name of the model element is explicitly listed.
    :ivar local: Denotes if the key references a model element of the same AAS (=true) or not (=false). In case of
                 local = false the key may reference a model element of another AAS or an entity outside any AAS that
                 has a global unique id.
    :ivar value: The key value, for example an IRDI if the idType=IRDI
    :ivar id_type: Type of the key value. In case of idType = idShort local shall be true. In case type=GlobalReference
                   idType shall not be IdShort.
    """

    def __init__(self,
                 type_: KeyElements,
                 local: bool,
                 value: str,
                 id_type: KeyType):
        """
        Initializer of Key

        :param type_: Denote which kind of entity is referenced. In case type = GlobalReference then the element is a
                      global unique id. In all other cases the key references a model element of the same or of another
                      AAS. The name of the model element is explicitly listed.
        :param local: Denotes if the key references a model element of the same AAS (=true) or not (=false). In case of
                      local = false the key may reference a model element of another AAS or an entity outside any AAS
                      that has a global unique id.
        :param value: The key value, for example an IRDI if the idType=IRDI
        :param id_type: Type of the key value. In case of idType = idShort local shall be true. In case
                        type=GlobalReference idType shall not be IdShort.

        TODO: Add instruction what to do after construction
        """
        self.type: KeyElements
        self.local: bool
        self.value: str
        self.id_type: KeyType
        super().__setattr__('type', type_)
        super().__setattr__('local', local)
        super().__setattr__('value', value)
        super().__setattr__('id_type', id_type)

    def __setattr__(self, key, value):
        """Prevent modification of attributes."""
        raise AttributeError('Reference is immutable')

    def __repr__(self) -> str:
        return "Key(local={}, id_type={}, value={})".format(self.local, self.id_type.name, self.value)

    def __str__(self) -> str:
        return "{}={}".format(self.id_type.name, self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Key):
            return NotImplemented
        return (self.id_type is other.id_type
                and self.value == other.value
                and self.local == other.local
                and self.type == other.type)

    def __hash__(self):
        return hash((self.id_type, self.value, self.local, self.type))

    def get_identifier(self) -> Optional["Identifier"]:
        """
        Get an identifier object corresponding to this key, if it is a global key.

        :return: None if this is no global key, otherwise a corresponding identifier object
        """
        if self.id_type.is_local_key_type:
            return None
        return Identifier(self.value, IdentifierType(self.id_type.value))

    @staticmethod
    def from_referable(referable: "Referable") -> "Key":
        """
        Construct a key for a given Referable (or Identifiable) object
        """
        # Get the `type` by finding the first class from the base classes list (via inspect.getmro), that is contained
        # in KEY_ELEMENTS_CLASSES
        from . import KEY_ELEMENTS_CLASSES
        try:
            key_type = next(iter(KEY_ELEMENTS_CLASSES[t]
                                 for t in inspect.getmro(type(referable))
                                 if t in KEY_ELEMENTS_CLASSES))
        except StopIteration:
            key_type = KeyElements.PROPERTY

        local = True  # TODO
        if isinstance(referable, Identifiable):
            return Key(key_type, local, referable.identification.id,
                       KeyType(referable.identification.id_type.value))
        else:
            return Key(key_type, local, referable.id_short, KeyType.IDSHORT)


class AdministrativeInformation:
    """
    Administrative meta-information for an element like version information.

    :ivar version: Version of the element.
    :ivar revision: Revision of the element.
    Constraint AASd-005: A revision requires a version. This means, if there is no version there is no revision
                         neither.
    """

    def __init__(self,
                 version: Optional[str] = None,
                 revision: Optional[str] = None):
        """
        Initializer of AdministrativeInformation

        :param version: Version of the element.
        :param revision: Revision of the element.

        Constraint AASd-005: A revision requires a version. This means, if there is no version there is no revision
                             neither.
        :raises ValueError: If version is None and revision is not None

        TODO: Add instruction what to do after construction
        """
        if version is None and revision is not None:
            raise ValueError("A revision requires a version. This means, if there is no version there is no revision "
                             "neither.")
        self.version: Optional[str] = version
        self._revision: Optional[str] = revision

    def _get_revision(self):
        return self._revision

    def _set_revision(self, revision: str):
        if self.version is None:
            raise ValueError("A revision requires a version. This means, if there is no version there is no revision "
                             "neither. Please set version first.")
        else:
            self._revision = revision

    def __eq__(self, other) -> bool:
        return self.version == other.version and self._revision == other._revision

    def __repr__(self) -> str:
        return "AdministrativeInformation(version={}, revision={})".format(self.version, self.revision)

    revision = property(_get_revision, _set_revision)


class Identifier:
    """
    Used to uniquely identify an entity by using an identifier.

    :ivar id: Identifier of the element. Its type is defined in id_type.
    :ivar id_type: Type of the Identifier, e.g. URI, IRDI etc. The supported Identifier types are defined in
                   the enumeration "IdentifierType".
    """

    def __init__(self,
                 id_: str,
                 id_type: IdentifierType):
        """
        Initializer of Identifier

        :param id_: Identifier of the element. Its type is defined in id_type.
        :param id_type: Type of the Identifier, e.g. URI, IRDI etc. The supported Identifier types are defined in the
                        enumeration "IdentifierType".

        TODO: Add instruction what to do after construction
        """
        self.id: str
        self.id_type: IdentifierType
        super().__setattr__('id', id_)
        super().__setattr__('id_type', id_type)

    def __setattr__(self, key, value):
        """Prevent modification of attributes."""
        raise AttributeError('Identifier are immutable')

    def __hash__(self):
        return hash((self.id_type, self.id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identifier):
            return NotImplemented
        return self.id_type == other.id_type and self.id == other.id

    def __repr__(self) -> str:
        return "Identifier({}={})".format(self.id_type.name, self.id)


class Referable(metaclass=abc.ABCMeta):
    """
    An element that is referable by its id_short. This id is not globally unique. This id is unique within
    the name space of the element.

    << abstract >>

    :ivar id_short: Identifying string of the element within its name space.
                    Constraint AASd-001: In case of a referable element not being an identifiable element this id is
                                         mandatory and used for referring to the element in its name space.
                    Constraint AASd-002: idShort shall only feature letters, digits, underscore ("_"); starting
                                         mandatory with a letter.
                    Constraint AASd-003: idShort shall be matched case insensitive.
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
    :ivar description: Description or comments on the element.
    :ivar parent: Reference to the next referable parent element of the element.
                  Constraint AASd-004: Add parent in case of non identifiable elements.
    :ivar source: Source of the object, an URI, that defines where this object's data originates from.
                  This is used to specify where the Referable should be updated from and committed to.
                  Default is an empty string, making it use the source of its ancestor, if possible.
    """
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self._id_short: Optional[str] = ""
        self.category: Optional[str] = ""
        self.description: Optional[LangStringSet] = set()
        # We use a Python reference to the parent Namespace instead of a Reference Object, as specified. This allows
        # simpler and faster navigation/checks and it has no effect in the serialized data formats anyway.
        self.parent: Optional[Namespace] = None
        self.source: str = ""

    def __repr__(self) -> str:
        reversed_path = []
        item = self  # type: Any
        while item is not None:
            if isinstance(item, Identifiable):
                reversed_path.append(str(item.identification))
                break
            elif isinstance(item, Referable):
                reversed_path.append(item.id_short)
                item = item.parent
            else:
                raise AttributeError('Referable must have an identifiable as root object and only parents that are '
                                     'referable')

        return "{}[{}]".format(self.__class__.__name__, " / ".join(reversed(reversed_path)))

    def _get_id_short(self):
        return self._id_short

    def _set_id_short(self, id_short: Optional[str]):
        """
        Check the input string

        Constraint AASd-001: In case of a referable element not being an identifiable element this id is mandatory and
        used for referring to the element in its name space.
        Constraint AASd-002: idShort shall only feature letters, digits, underscore ('_'); starting mandatory with a
        letter

        Additionally check that the idShort is not already present in the same parent Namespace (if this object is
        already contained in a parent Namespace).

        :param id_short: Identifying string of the element within its name space
        :raises ValueError: if the constraint is not fulfilled
        :raises KeyError: if the new idShort causes a name collision in the parent Namespace
        """

        if id_short is None and not hasattr(self, 'identification'):
            raise ValueError("The id_short for not identifiable elements is mandatory")
        test_id_short: str = str(id_short)
        if not re.fullmatch("[a-zA-Z0-9_]*", test_id_short):
            raise ValueError("The id_short must contain only letters, digits and underscore")
        if len(test_id_short) > 0 and not test_id_short[0].isalpha():
            raise ValueError("The id_short must start with a letter")

        if self.parent is not None and id_short != self.id_short:
            for set_ in self.parent.namespace_element_sets:
                if id_short in set_:
                    raise KeyError("Referable with id_short '{}' is already present in the parent Namespace"
                                   .format(id_short))
            for set_ in self.parent.namespace_element_sets:
                if self in set_:
                    set_.discard(self)
                    self._id_short = id_short
                    set_.add(self)
                    break
        # Redundant to the line above. However this way, we make sure that we really update the _id_short
        self._id_short = id_short

    def update(self,
               max_age: float = 0,
               recursive: bool = True,
               _indirect_source: bool = True) -> None:
        """
        Update the local Referable object from any underlying external data source, using an appropriate backend

        If there is no source given, it will find its next ancestor with a source and update from this source.
        If there is no source in any ancestor, this function will do nothing

        :param max_age: Maximum age of the local data in seconds. This method may return early, if the previous update
            of the object has been performed less than `max_age` seconds ago.
        :param recursive: Also call update on all children of this object. Default is True
        :param _indirect_source: Internal parameter to avoid duplicate updating.
        :raises backends.BackendError: If no appropriate backend or the data source is not available
        """
        # TODO consider max_age
        if not _indirect_source:
            # Update was already called on an ancestor of this Referable. Only update it, if it has its own source
            if self.source != "":
                backends.get_backend(self.source).update_object(updated_object=self,
                                                                store_object=self,
                                                                relative_path=[])

        else:
            # Try to find a valid source for this Referable
            if self.source != "":
                backends.get_backend(self.source).update_object(updated_object=self,
                                                                store_object=self,
                                                                relative_path=[])
            else:
                store_object, relative_path = self.find_source()
                if store_object and relative_path is not None:
                    backends.get_backend(store_object.source).update_object(updated_object=self,
                                                                            store_object=store_object,
                                                                            relative_path=list(relative_path))

        if recursive:
            # update all the children who have their own source
            if isinstance(self, Namespace):
                for namespace_set in self.namespace_element_sets:
                    for referable in namespace_set:
                        referable.update(max_age, recursive=True, _indirect_source=False)

    def find_source(self) -> Tuple[Optional["Referable"], Optional[List[str]]]:  # type: ignore
        """
        Finds the closest source in this objects ancestors. If there is no source, returns None

        :return: (The closest ancestor with a defined source, the relative path of id_shorts to that ancestor)
        """
        referable: Referable = self
        relative_path: List[str] = [self.id_short]
        while referable is not None:
            if referable.source != "":
                relative_path.reverse()
                return referable, relative_path
            if referable.parent:
                assert(isinstance(referable.parent, Referable))
                referable = referable.parent
                relative_path.append(referable.id_short)
                continue
            break
        return None, None

    def update_from(self, other: "Referable", update_source: bool = False):
        """
        Internal function to updates the object's attributes from another object of a similar type.

        This function should not be used directly. It is typically used by backend implementations (database adapters,
        protocol clients, etc.) to update the object's data, after `update()` has been called.

        :param other: The object to update from
        :param update_source: Update the source attribute with the other's source attribute. This is not propagated
                              recursively
        """
        for name, var in vars(other).items():
            # do not update the parent, namespace_element_sets or source (depending on update_source parameter)
            if name in ("parent", "namespace_element_sets") or name == "source" and not update_source:
                continue
            if isinstance(var, NamespaceSet):
                # update the elements of the NameSpaceSet
                vars(self)[name].update_nss_from(var)
            else:
                vars(self)[name] = var  # that variable is not a NameSpaceSet, so it isn't Referable

    def commit(self) -> None:
        """
        Transfer local changes on this object to all underlying external data sources.

        This function commits the current state of this object to its own and each external data source of its
        ancestors. If there is no source, this function will do nothing.
        """
        current_ancestor = self.parent
        relative_path: List[str] = [self.id_short]
        # Commit to all ancestors with sources
        while current_ancestor:
            assert(isinstance(current_ancestor, Referable))
            if current_ancestor.source != "":
                backends.get_backend(current_ancestor.source).commit_object(committed_object=self,
                                                                            store_object=current_ancestor,
                                                                            relative_path=list(relative_path))
            relative_path.insert(0, current_ancestor.id_short)
            current_ancestor = current_ancestor.parent
        # Commit to own source and check if there are children with sources to commit to
        self._direct_source_commit()

    def _direct_source_commit(self):
        """
        Commits children of an ancestor recursively, if they have a specific source given
        """
        if self.source != "":
            backends.get_backend(self.source).commit_object(committed_object=self,
                                                            store_object=self,
                                                            relative_path=[])

        if isinstance(self, Namespace):
            for namespace_set in self.namespace_element_sets:
                for referable in namespace_set:
                    referable._direct_source_commit()

    id_short = property(_get_id_short, _set_id_short)


_RT = TypeVar('_RT', bound=Referable)


class UnexpectedTypeError(TypeError):
    """
    Exception to be raised by Reference.resolve() if the retrieved object has not the expected type.

    :ivar value: The object of unexpected type
    """
    def __init__(self, value: Referable, *args):
        super().__init__(*args)
        self.value = value


class Reference:
    """
    Reference to either a model element of the same or another AAs or to an external entity.

    A reference is an ordered list of keys, each key referencing an element. The complete list of keys may for
    example be concatenated to a path that then gives unique access to an element or entity

    :ivar: key: Ordered list of unique reference in its name space, each key referencing an element. The complete
                list of keys may for example be concatenated to a path that then gives unique access to an element
                or entity.
    :ivar: type: The type of the referenced object (additional attribute, not from the AAS Metamodel)
    """

    def __init__(self,
                 key: Tuple[Key, ...]):
        """
        Initializer of Reference

        :param key: Ordered list of unique reference in its name space, each key referencing an element. The complete
                    list of keys may for example be concatenated to a path that then gives unique access to an element
                    or entity.

        TODO: Add instruction what to do after construction
        """
        self.key: Tuple[Key, ...]
        super().__setattr__('key', key)

    def __setattr__(self, key, value):
        """Prevent modification of attributes."""
        raise AttributeError('Reference is immutable')

    def __repr__(self) -> str:
        return "Reference(key={})".format(self.key)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Reference):
            return NotImplemented
        if len(self.key) != len(other.key):
            return False
        return all(k1 == k2 for k1, k2 in zip(self.key, other.key))


class AASReference(Reference, Generic[_RT]):
    """
    Typed Reference to any referable Asset Administration Shell object.

    This is a special construct of the implementation to allow typed references and dereferencing.
    """
    def __init__(self,
                 key: Tuple[Key, ...],
                 target_type: Type[_RT]):
        """
        Initializer of AASReference

        :param key: Ordered list of unique reference in its name space, each key referencing an element. The complete
                    list of keys may for example be concatenated to a path that then gives unique access to an element
                    or entity.
        :param: type_: The type of the referenced object (additional parameter, not from the AAS Metamodel)

        TODO: Add instruction what to do after construction
        """
        # TODO check keys for validity. GlobalReference and Fragment-Type keys are not allowed here
        super().__init__(key)
        self.type: Type[_RT]
        object.__setattr__(self, 'type', target_type)

    def resolve(self, provider_: "provider.AbstractObjectProvider") -> _RT:
        """
        Follow the reference and retrieve the Referable object it points to

        :return: The referenced object (or a proxy object for it)
        :raises IndexError: If the list of keys is empty
        :raises TypeError: If one of the intermediate objects on the path is not a Namespace
        :raises UnexpectedTypeError: If the retrieved object is not of the expected type (or one of its subclasses). The
                                     object is stored in the `value` attribute of the exception
        :raises KeyError: If the reference could not be resolved
        """
        if len(self.key) == 0:
            raise IndexError("List of keys is empty")
        # Find key index last (global) identifier-key in key list (from https://stackoverflow.com/a/6890255/10315508)
        try:
            last_identifier_index = next(i
                                         for i in reversed(range(len(self.key)))
                                         if self.key[i].get_identifier())
        except StopIteration:
            # If no identifier-key is contained in the list, we could try to resolve the path locally.
            # TODO implement local resolution
            raise NotImplementedError("We currently don't support local-only references without global identifier keys")

        resolved_keys: List[str] = []  # for more helpful error messages

        # First, resolve the identifier-key via the provider
        identifier: Identifier = self.key[last_identifier_index].get_identifier()  # type: ignore
        try:
            item: Referable = provider_.get_identifiable(identifier)
        except KeyError as e:
            raise KeyError("Could not resolve global reference key {}".format(identifier)) from e
        resolved_keys.append(str(identifier))

        # Now, follow path, given by remaining keys, recursively
        for key in self.key[last_identifier_index+1:]:
            if not isinstance(item, Namespace):
                raise TypeError("Object retrieved at {} is not a Namespace".format(" / ".join(resolved_keys)))
            try:
                item = item.get_referable(key.value)
            except KeyError as e:
                raise KeyError("Could not resolve id_short {} at {}".format(key.value, " / ".join(resolved_keys)))\
                    from e

        # Check type
        if not isinstance(item, self.type):
            raise UnexpectedTypeError(item, "Retrieved object {} is not an instance of referenced type {}"
                                            .format(item, self.type.__name__))
        return item

    def get_identifier(self) -> Identifier:
        """
        Retrieve the Identifier of the Identifiable object, which is referenced or in which the referenced Referable is
        contained.

        :raises ValueError: If this Reference does not include a Key with global KeyType (IRDI, IRI, CUSTOM)
        """
        try:
            last_identifier = next(key.get_identifier()
                                   for key in reversed(self.key)
                                   if key.get_identifier())
            return last_identifier  # type: ignore  # MyPy doesn't get the generator expression above
        except StopIteration:
            raise ValueError("Reference cannot be represented as an Identifier, since it does not contain a Key with "
                             "global KeyType (IRDI, IRI, CUSTOM)")

    def __repr__(self) -> str:
        return "AASReference(type={}, key={})".format(self.type.__name__, self.key)

    @staticmethod
    def from_referable(referable: Referable) -> "AASReference":
        """
        Construct a Reference to a given Referable AAS object

        This requires that the Referable object is Identifiable itself or is a child-, grand-child-, etc. object of an
        Identifiable object. Additionally, the object must be an instance of a known Referable type.

        :raises ValueError: If no Identifiable object is found while traversing the object's ancestors
        """
        # Get the first class from the base classes list (via inspect.getmro), that is contained in KEY_ELEMENTS_CLASSES
        from . import KEY_ELEMENTS_CLASSES
        try:
            ref_type = next(iter(t for t in inspect.getmro(type(referable)) if t in KEY_ELEMENTS_CLASSES))
        except StopIteration:
            ref_type = Referable

        ref: Referable = referable
        keys: List[Key] = []
        while True:
            keys.append(Key.from_referable(ref))
            if isinstance(ref, Identifiable):
                keys.reverse()
                return AASReference(tuple(keys), ref_type)
            if ref.parent is None or not isinstance(ref.parent, Referable):
                raise ValueError("The given Referable object is not embedded within an Identifiable object")
            ref = ref.parent


class Identifiable(Referable, metaclass=abc.ABCMeta):
    """
    An element that has a globally unique identifier.

    << abstract >>

    :ivar administration: Administrative information of an identifiable element.
    :ivar identification: The globally unique identification of the element.
    """
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self.administration: Optional[AdministrativeInformation] = None
        self.identification: Identifier = Identifier("", IdentifierType.IRDI)

    def __repr__(self) -> str:
        return "{}[{}]".format(self.__class__.__name__, self.identification)


class HasSemantics(metaclass=abc.ABCMeta):
    """
    Element that can have a semantic definition.

    << abstract >>

    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the element.
                       The semantic id may either reference an external global id or it may reference a referable model
                       element of kind=Type that defines the semantics of the element.
    """
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self.semantic_id: Optional[Reference] = None


class HasKind(metaclass=abc.ABCMeta):
    """
    An element with a kind is an element that can either represent a type or an instance.
    Default for an element is that it is representing an instance.

    << abstract >>

    :ivar kind: Kind of the element: either type or instance. Default = Instance.
    """
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self._kind: ModelingKind = ModelingKind.INSTANCE

    @property
    def kind(self):
        return self._kind


class Constraint(metaclass=abc.ABCMeta):
    """
    A constraint is used to further qualify an element.

    << abstract >>
    """
    @abc.abstractmethod
    def __init__(self):
        pass


class Qualifiable(metaclass=abc.ABCMeta):
    """
    The value of a qualifiable element may be further qualified by one or more qualifiers or complex formulas.

    << abstract >>

    :ivar qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
    """
    @abc.abstractmethod
    def __init__(self):
        super().__init__()
        self.qualifier: Set[Constraint] = set()


class Formula(Constraint):
    """
    A formula is used to describe constraints by a logical expression.

    :ivar depends_on: Unordered list of references to referable or even external global elements that are used in the
                      logical expression. The value of the referenced elements needs to be accessible so that
                      it can be evaluated in the formula to true or false in the corresponding logical expression
                      it is used in.
    """

    def __init__(self,
                 depends_on: Optional[Set[Reference]] = None):
        """
        Initializer of Formula

        :param depends_on: Unordered of references to referable or even external global elements that are used in the
                           logical expression. The value of the referenced elements needs to be accessible so that
                           it can be evaluated in the formula to true or false in the corresponding logical expression
                           it is used in.

        TODO: Add instruction what to do after construction
        """
        super().__init__()
        self.depends_on: Set[Reference] = set() if depends_on is None else depends_on


class Qualifier(Constraint, HasSemantics):
    """
    A qualifier is a type-value pair that makes additional statements w.r.t. the value of the element.

    :ivar type: The type of the qualifier that is applied to the element.
    :ivar value_type: Data type of the qualifier value
    :ivar value: The value of the qualifier.
                 Constraint AASd-006: if both, the value and the valueId are present then the value needs to be
                                      identical to the value of the referenced coded value in Qualifier/valueId.
    :ivar value_id: Reference to the global unique id of a coded value.
    :ivar semantic_id: The semantic_id defined in the HasSemantics class.
    """

    def __init__(self,
                 type_: QualifierType,
                 value_type: DataTypeDef,
                 value: Optional[ValueDataType] = None,
                 value_id: Optional[Reference] = None,
                 semantic_id: Optional[Reference] = None):
        """
        Initializer of Qualifier

        :param type_: The type of the qualifier that is applied to the element.
        :param value_type: Data type of the qualifier value
        :param value: The value of the qualifier.
        :param value_id: Reference to the global unique id of a coded value.
        :param semantic_id: The semantic_id defined in the HasSemantics class.

        TODO: Add instruction what to do after construction
        """
        super().__init__()
        self.type: QualifierType = type_
        self.value_type: Type[datatypes.AnyXSDType] = value_type
        self._value: Optional[ValueDataType] = datatypes.trivial_cast(value, value_type) if value is not None else None
        self.value_id: Optional[Reference] = value_id
        self.semantic_id: Optional[Reference] = semantic_id

    def __repr__(self) -> str:
        return "Qualifier(type={})".format(self.type)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value) -> None:
        if value is None:
            self._value = None
        else:
            self._value = datatypes.trivial_cast(value, self.value_type)


class ValueReferencePair:
    """
    A value reference pair within a value list. Each value has a global unique id defining its semantic.

    << Data Type >>

    :ivar value: The value of the referenced concept definition of the value in value_id
    :ivar value_id: Global unique id of the value.
    """

    def __init__(self,
                 value_type: DataTypeDef,
                 value: ValueDataType,
                 value_id: Reference):
        """
        Initializer of ValueReferencePair

        :param value: The value of the referenced concept definition of the value in value_id
        :param value_id: Global unique id of the value.
        :param value_type: XSD datatype of the value (this is not compliant to the DotAAS meta model)

        TODO: Add instruction what to do after construction
        """
        self.value_type: Type[datatypes.AnyXSDType] = value_type
        self.value_id: Reference = value_id
        self._value: ValueDataType = datatypes.trivial_cast(value, value_type)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value) -> None:
        if value is None:
            raise AttributeError('Value can not be None')
        else:
            self._value = datatypes.trivial_cast(value, self.value_type)

    def __repr__(self) -> str:
        return "ValueReferencePair(value_type={}, value={}, value_id={})".format(self.value_type,
                                                                                 self.value,
                                                                                 self.value_id)


ValueList = Set[ValueReferencePair]


class Namespace(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for all objects which form a Namespace to hold Referable objects and resolve them by their
    id_short.

    A Namespace can contain multiple NamespaceSets, which contain Referable objects of different types. However, the
    id_short of each object must be unique across all NamespaceSets of one Namespace.

    :ivar namespace_element_sets: A list of all NamespaceSets of this Namespace
    """
    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.namespace_element_sets: List[NamespaceSet] = []

    def get_referable(self, id_short: str) -> Referable:
        """
        Find a Referable in this Namespaces by its id_short

        :raises KeyError: If no such Referable can be found
        """
        for dict_ in self.namespace_element_sets:
            if id_short in dict_:
                return dict_.get_referable(id_short)
        raise KeyError("Referable with id_short {} not found in this namespace".format(id_short))

    def remove_referable(self, id_short: str) -> None:
        """
        Remove a Referable from this Namespace by its id_short

        :raises KeyError: If no such Referable can be found
        """
        for dict_ in self.namespace_element_sets:
            if id_short in dict_:
                return dict_.remove(id_short)
        raise KeyError("Referable with id_short {} not found in this namespace".format(id_short))

    def __iter__(self) -> Iterator[_RT]:
        return itertools.chain.from_iterable(self.namespace_element_sets)


class NamespaceSet(MutableSet[_RT], Generic[_RT]):
    """
    Helper class for storing Referable objects of a given type in a Namespace and find them by their id_short.

    This class behaves much like a set of Referable objects of a defined type, but uses a dict internally to rapidly
    find those objects by their id_short. Additionally, it manages the `parent` attribute of the stored Referables and
    ensures the uniqueness of their id_short within the Namespace.

    Use `add()`, `remove()`, `pop()`, `discard()`, `clear()`, `len()`, `x in` checks and iteration  just like on a
    normal set of Referables. To get a referable by its id_short, use `get_referable()` or `get()` (the latter one
    allows a default argument and returns None instead of raising a KeyError). As a bonus, the `x in` check supports
    checking for existence of id_short *or* a concrete Referable object.
    """
    def __init__(self, parent: Namespace, items: Iterable[_RT] = ()) -> None:
        """
        Initialize a new NamespaceSet.

        This initializer automatically takes care of adding this set to the `namespace_element_sets` list of the
        Namespace.

        :param parent: The Namespace this set belongs to
        :param items: A given list of Referable items to be added to the set
        :raises KeyError: When `items` contains multiple objects with same id_short
        """
        self.parent = parent
        parent.namespace_element_sets.append(self)
        self._backend: Dict[str, _RT] = {}
        try:
            for i in items:
                self.add(i)
        except Exception:
            # Do a rollback, when an exception occurs while adding items
            self.clear()
            raise

    def __contains__(self, x: object) -> bool:
        if isinstance(x, str):
            return x in self._backend
        elif isinstance(x, Referable):
            return self._backend.get(x.id_short) is x
        else:
            return False

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[_RT]:
        return iter(self._backend.values())

    def add(self, value: _RT):
        for set_ in self.parent.namespace_element_sets:
            if value.id_short in set_:
                raise KeyError("Referable with id_short '{}' is already present in {}"
                               .format(value.id_short,
                                       "this set of objects"
                                       if set_ is self else "another set in the same namespace"))
        if value.parent is not None and value.parent is not self.parent:
            raise ValueError("Object has already a parent, but it must not be part of two namespaces.")
            # TODO remove from current parent instead (allow moving)?
        value.parent = self.parent
        self._backend[value.id_short] = value

    def remove(self, item: Union[str, _RT]):
        if isinstance(item, str):
            del self._backend[item]
        else:
            item_in_dict = self._backend[item.id_short]
            if item_in_dict is not item:
                raise KeyError("Item not found in NamespaceDict (other item with same id_short exists)")
            item.parent = None
            del self._backend[item.id_short]

    def discard(self, x: _RT) -> None:
        if x not in self:
            return
        self.remove(x)

    def pop(self) -> _RT:
        _, value = self._backend.popitem()
        value.parent = None
        return value

    def clear(self) -> None:
        for value in self._backend.values():
            value.parent = None
        self._backend.clear()

    def get_referable(self, key) -> _RT:
        """
        Find an object in this set by its id_short

        :raises KeyError: If no such object can be found
        """
        return self._backend[key]

    def get(self, key, default: Optional[_RT] = None) -> Optional[_RT]:
        """
        Find an object in this set by its id_short, with fallback parameter

        :param default: An object to be returned, if no object with the given id_short is found
        :return: The Referable object with the given id_short in the set. Otherwise the `default` object or None, if
                 none is given.
        """
        return self._backend.get(key, default)

    def update_nss_from(self, other: "NamespaceSet"):
        """
        Update a NamespaceSet from a given NamespaceSet.

        WARNING: By updating, the "other" NamespaceSet gets destroyed.

        :param other: The NamespaceSet to update from
        """
        referables_to_add: List[Referable] = []  # objects from the other nss to add to self
        referables_to_remove: List[Referable] = []  # objects to remove from self
        for other_referable in other:
            try:
                referable = self._backend[other_referable.id_short]
                if type(referable) is type(other_referable):
                    # referable is the same as other referable
                    referable.update_from(other_referable, update_source=True)
            except KeyError:
                # other referable is not in NamespaceSet
                referables_to_add.append(other_referable)
        for id_short, referable in self._backend.items():
            if not other.get(id_short):
                # referable does not exist in the other NamespaceSet
                referables_to_remove.append(referable)
        for referable_to_add in referables_to_add:
            other.remove(referable_to_add)
            self.add(referable_to_add)  # type: ignore
        for referable_to_remove in referables_to_remove:
            self.remove(referable_to_remove)  # type: ignore


class OrderedNamespaceSet(NamespaceSet[_RT], MutableSequence[_RT], Generic[_RT]):
    """
    A specialized version of NamespaceSet, that keeps track of the order of the stored Referable objects.

    Additionally to the MutableSet interface of NamespaceSet, this class provides a set-like interface (actually it
    is derived from MutableSequence). However, we don't permit duplicate entries in the ordered list of objects.
    """
    def __init__(self, parent: Namespace, items: Iterable[_RT] = ()) -> None:
        """
        Initialize a new OrderedNamespaceSet.

        This initializer automatically takes care of adding this set to the `namespace_element_sets` list of the
        Namespace.

        :param parent: The Namespace this set belongs to
        :param items: A given list of Referable items to be added to the set
        :raises KeyError: When `items` contains multiple objects with same id_short
        """
        self._order: List[_RT] = []
        super().__init__(parent, items)

    def __iter__(self) -> Iterator[_RT]:
        return iter(self._order)

    def add(self, value: _RT):
        super().add(value)
        self._order.append(value)

    def remove(self, item: Union[str, _RT]):
        if isinstance(item, str):
            item = self.get_referable(item)
        super().remove(item)
        self._order.remove(item)

    def pop(self, i: Optional[int] = None):
        if i is None:
            value = super().pop()
            self._order.remove(value)
        else:
            value = self._order.pop(i)
            super().remove(value)
        return value

    def clear(self) -> None:
        super().clear()
        self._order.clear()

    def insert(self, index: int, object_: _RT) -> None:
        super().add(object_)
        self._order.insert(index, object_)

    @overload
    def __getitem__(self, i: int) -> _RT: ...

    @overload
    def __getitem__(self, s: slice) -> MutableSequence[_RT]: ...

    def __getitem__(self, s: Union[int, slice]) -> Union[_RT, MutableSequence[_RT]]:
        return self._order[s]

    @overload
    def __setitem__(self, i: int, o: _RT) -> None: ...

    @overload
    def __setitem__(self, s: slice, o: Iterable[_RT]) -> None: ...

    def __setitem__(self, s, o) -> None:
        if isinstance(s, int):
            deleted_items = [self._order[s]]
            super().add(o)
            self._order[s] = o
        else:
            deleted_items = self._order[s]
            new_items = itertools.islice(o, len(deleted_items))
            successful_new_items = []
            try:
                for i in new_items:
                    super().add(i)
                    successful_new_items.append(i)
            except Exception:
                # Do a rollback, when an exception occurs while adding items
                for i in successful_new_items:
                    super().remove(i)
                raise
            self._order[s] = new_items
        for i in deleted_items:
            super().remove(i)

    @overload
    def __delitem__(self, i: int) -> None: ...

    @overload
    def __delitem__(self, i: slice) -> None: ...

    def __delitem__(self, i: Union[int, slice]) -> None:
        if isinstance(i, int):
            i = slice(i, i+1)
        for o in self._order[i]:
            super().remove(o)
        del self._order[i]
