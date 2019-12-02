import abc
import itertools
from abc import abstractmethod
from enum import Enum, unique
from typing import List, Optional, Set, TypeVar, MutableSet, Generic, Iterable, Dict, Iterator, Union, overload,\
    MutableSequence
import re

DataTypeDef = str  # any xsd simple type as string
BlobType = bytearray
MimeType = str  # any mimetype as in RFC2046
PathType = str
QualifierType = str
ValueDataType = str  # any xsd atomic type
LangString = str  # a string in a specified language
# A dict of language-Identifier (according to ISO 639-1 and ISO 3166-1) and string in this language.
# The meaning of the string in each language is the same.
# << Data Type >> Example ["en-US", "germany"]
LangStringSet = Dict[str, LangString]


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
    :cvar ANNOTATION_RELATIONSHIP_ELEMENT: annotated relationship element
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
    ANNOTATION_RELATIONSHIP_ELEMENT = 1001
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

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
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

    :ivar type_: Denote which kind of entity is referenced. In case type = GlobalReference then the element is a
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
        self.type_: KeyElements = type_
        self.local: bool = local
        self.value: str = value
        self.id_type: KeyType = id_type


class Reference:
    """
    Reference to either a model element of the same or another AAS or to an external entity.

    A reference is an ordered list of keys, each key referencing an element. The complete list of keys may for
    example be concatenated to a path that then gives unique access to an element or entity

    :ivar: key: Ordered list of unique reference in its name space, each key referencing an element. The complete
                list of keys may for example be concatenated to a path that then gives unique access to an element
                or entity.
    """

    def __init__(self,
                 key: List[Key]):
        """
        Initializer of Reference

        :param key: Ordered list of unique reference in its name space, each key referencing an element. The complete
                    list of keys may for example be concatenated to a path that then gives unique access to an element
                    or entity.

        TODO: Add instruction what to do after construction
        """
        self.key: List[Key] = key


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
        self.id: str = id_
        self.id_type: IdentifierType = id_type


class HasDataSpecification(metaclass=abc.ABCMeta):
    """
    Element that can have data specification templates. A template defines the additional attributes an element may or
    shall have.

    << abstract >>

    :ivar data_specification: Unordered list of global references to the data specification template used by the
                              element.
    """

    def __init__(self):
        self.data_specification: Set[Reference] = set()


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


    """

    def __init__(self):
        self.id_short: Optional[str] = ""
        self.category: Optional[str] = None
        self.description: Optional[LangStringSet] = None
        # We use a Python reference to the parent Namespace instead of a Reference Object, as specified. This allows
        # simpler and faster navigation/checks and it has no effect in the serialized data formats anyway.
        self.parent: Optional[Namespace] = None

    def _get_id_short(self):
        return self._id_short

    def _set_id_short(self, id_short: Optional[str]):
        """
        Check the input string

        Constraint AASd-001: In case of a referable element not being an identifiable element this id is mandatory and
        used for referring to the element in its name space.
        Constraint AASd-002: idShort shall only feature letters, digits, underscore ('_'); starting mandatory with a
        letter

        :param id_short: Identifying string of the element within its name space
        :raises: Exception if the constraint is not fulfilled
        """

        if id_short is None and not hasattr(self, 'identification'):
            raise ValueError("The id_short for not identifiable elements is mandatory")
        test_id_short: str = str(id_short)
        if not re.match("^[a-zA-Z0-9_]*$", test_id_short):
            raise ValueError("The id_short must contain only letters, digits and underscore")
        if not re.match("^([a-zA-Z].*|)$", test_id_short):
            raise ValueError("The id_short must start with a letter")
        self._id_short = id_short

    id_short = property(_get_id_short, _set_id_short)


class Identifiable(Referable, metaclass=abc.ABCMeta):
    """
    An element that has a globally unique identifier.

    << abstract >>

    :ivar administration: Administrative information of an identifiable element.
    :ivar identification: The globally unique identification of the element.
    """

    def __init__(self):
        super().__init__()
        self.administration: Optional[AdministrativeInformation] = None
        self.identification: Identifier = Identifier("", IdentifierType.IRDI)


class HasSemantics(metaclass=abc.ABCMeta):
    """
    Element that can have a semantic definition.

    << abstract >>

    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the element.
                       The semantic id may either reference an external global id or it may reference a referable model
                       element of kind=Type that defines the semantics of the element.
    """

    def __init__(self):
        self.semantic_id: Optional[Reference] = None


class HasKind(metaclass=abc.ABCMeta):
    """
    An element with a kind is an element that can either represent a type or an instance.
    Default for an element is that it is representing an instance.

    << abstract >>

    :ivar kind: Kind of the element: either type or instance. Default = Instance.
    """

    def __init__(self):
        self._kind: ModelingKind = ModelingKind.INSTANCE

    @property
    def kind(self):
        return self._kind


class Constraint(metaclass=abc.ABCMeta):
    """
    A constraint is used to further qualify an element.

    << abstract >>
    """

    def __init__(self):
        pass


class Qualifiable(metaclass=abc.ABCMeta):
    """
    The value of a qualifiable element may be further qualified by one or more qualifiers or complex formulas.

    << abstract >>

    :ivar qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
    """

    def __init__(self):
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
        self.depends_on: Optional[Set[Reference]] = set() if depends_on is None else depends_on


class Qualifier(Constraint, HasSemantics):
    """
    A qualifier is a type-value pair that makes additional statements w.r.t. the value of the element.

    :ivar type_: The type of the qualifier that is applied to the element.
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
        self.type_: QualifierType = type_
        self.value_type: DataTypeDef = value_type
        self.value: Optional[ValueDataType] = value
        self.value_id: Optional[Reference] = value_id
        self.semantic_id: Optional[Reference] = semantic_id


class ValueReferencePair:
    """
    A value reference pair within a value list. Each value has a global unique id defining its semantic.

    << Data Type >>

    :ivar value: The value of the referenced concept definition of the value in value_id
    :ivar value_id: Global unique id of the value.
    """

    def __init__(self,
                 value: ValueDataType,
                 value_id: Reference):
        """
        Initializer of ValueReferencePair

        :param value: The value of the referenced concept definition of the value in value_id
        :param value_id: Global unique id of the value.

        TODO: Add instruction what to do after construction
        """
        self.value: ValueDataType = value
        self.value_id: Reference = value_id


class ValueList:
    """
    A set of value reference pairs.

    << Data Type >>

    :ivar value_reference_pair_type: Unordered list of pairs of a value together with its global unique id.
    """

    def __init__(self,
                 value_reference_pair_type: Set[ValueReferencePair]):
        """
        Initializer of ValueList

        :param value_reference_pair_type: Unordered list of pairs of a value together with its global unique id.

        TODO: Add instruction what to do after construction
        """
        self.value_reference_pair_type: Set[ValueReferencePair] = value_reference_pair_type


T = TypeVar('T', bound=Referable)


class Namespace(metaclass=abc.ABCMeta):
    """
    Abstract baseclass for all objects which form a Namespace to hold Referable objects and resolve them by their
    id_short.

    A Namespace can contain multiple NamespaceSets, which contain Referable objects of different types. However, the
    id_short of each object must be unique across all NamespaceSets of one Namespace.

    :ivar namespace_element_sets: A list of all NamespaceSets of this Namespace
    """
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


class NamespaceSet(MutableSet[T], Generic[T]):
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
    def __init__(self, parent: Namespace, items: Iterable[T] = ()) -> None:
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
        self._backend: Dict[str, T] = {}
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

    def __iter__(self) -> Iterator[T]:
        return iter(self._backend.values())

    def add(self, value: T):
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

    def remove(self, item: Union[str, T]):
        if isinstance(item, str):
            del self._backend[item]
        else:
            item_in_dict = self._backend[item.id_short]
            if item_in_dict is not item:
                raise KeyError("Item not found in NamespaceDict (other item with same id_short exists)")
            item.parent = None
            del self._backend[item.id_short]

    def discard(self, x: T) -> None:
        if x not in self:
            return
        self.remove(x)

    def pop(self) -> T:
        _, value = self._backend.popitem()
        value.parent = None
        return value

    def clear(self) -> None:
        for value in self._backend.values():
            value.parent = None
        self._backend.clear()

    def get_referable(self, key) -> T:
        """
        Find an object in this set by its id_short

        :raises KeyError: If no such object can be found
        """
        return self._backend[key]

    def get(self, key, default: Optional[T] = None) -> Optional[T]:
        """
        Find an object in this set by its id_short, with fallback parameter

        :param default: An object to be returned, if no object with the given id_short is found
        :return: The Referable object with the given id_short in the set. Otherwise the `default` object or None, if
                 none is given.
        """
        return self._backend.get(key, default)


class OrderedNamespaceSet(NamespaceSet[T], MutableSequence[T], Generic[T]):
    """
    A specialized version of NamespaceSet, that keeps track of the order of the stored Referable objects.

    Additionally to the MutableSet interface of NamespaceSet, this class provides a set-like interface (actually it
    is derived from MutableSequence). However, we don't permit duplicate entries in the ordered list of objects.
    """
    def __init__(self, parent: Namespace, items: Iterable[T] = ()) -> None:
        """
        Initialize a new OrderedNamespaceSet.

        This initializer automatically takes care of adding this set to the `namespace_element_sets` list of the
        Namespace.

        :param parent: The Namespace this set belongs to
        :param items: A given list of Referable items to be added to the set
        :raises KeyError: When `items` contains multiple objects with same id_short
        """
        self._order: List[T] = []
        super().__init__(parent, items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._order)

    def add(self, value: T):
        super().add(value)
        self._order.append(value)

    def remove(self, item: Union[str, T]):
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

    def insert(self, index: int, object_: T) -> None:
        super().add(object_)
        self._order.insert(index, object_)

    @overload
    @abstractmethod
    def __getitem__(self, i: int) -> T: ...

    @overload
    @abstractmethod
    def __getitem__(self, s: slice) -> MutableSequence[T]: ...

    def __getitem__(self, s: Union[int, slice]) -> Union[T, MutableSequence[T]]:
        return self._order[s]

    @overload
    @abstractmethod
    def __setitem__(self, i: int, o: T) -> None: ...

    @overload
    @abstractmethod
    def __setitem__(self, s: slice, o: Iterable[T]) -> None: ...

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
    @abstractmethod
    def __delitem__(self, i: int) -> None: ...

    @overload
    @abstractmethod
    def __delitem__(self, i: slice) -> None: ...

    def __delitem__(self, i: Union[int, slice]) -> None:
        if isinstance(i, int):
            i = slice(i, i+1)
        for o in self._order[i]:
            super().remove(o)
        del self._order[i]
