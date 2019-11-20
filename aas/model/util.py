# TODO: check for constraints. what to do with them?

from abc import ABC, abstractmethod
from enum import Enum, unique, auto


@unique
class IdentifierType(Enum):
    """
    Enumeration of different types of Identifiers for global identification

    :var IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
                properties and classifications.
    :var URI: Uniform Resource Identifier
    :var Custom: Custom identifiers like GUIDs (globally unique Identifiers)
    """

    IRDI = auto()
    URI = auto()
    Custom = auto()


@unique
class Kind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.

    :var Type: hardware or software element which specifies the common attributes shared by all instances of the type
    :var Instance: concrete, clearly identifiable component of a certain type
    """

    Type = auto()
    Instance = auto()


class AdministrativeInformation:
    """
    Administrative meta-information for an element like version information.

    :var version: Version of the element.
    :var revision: Revision of the element.
    """

    def __init__(self, version: str or None, revision: str or None):
        self.version: str or None = version
        self.revision: str or None = revision


class Identifier:
    """
    Used to uniquely identify an entity by using an identifier.

    :var id: Identifier of the element. Its type is defined in id_type.
    :var id_type: Type of the Identifier, e.g. URI, IRDI etc. The supported Identifier types are defined in
                   the enumeration "IdentifierType".
    """

    def __init__(self, id_: str, id_type: IdentifierType):
        self.id: str = id_
        self.id_type: IdentifierType = id_type


class HasDataSpecification(ABC):
    """
    Element that can have data specification templates. A template defines the additional attributes an element may or
    shall have.

    :var has_data_specification: Global reference to the data specification template used by the element.
    """

    @property
    @abstractmethod
    def has_data_specification(self) -> [str]:
        pass


class Referable(ABC):
    """
    An element that is referable by its id_short. This id is not globally unique. This id is unique within
    the name space of the element.

    :var id_short: Identifying string of the element within its name space.
    :var category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
    :var description: Description or comments on the element.
    :var parent: Reference to the next referable parent element of the element.
    """

    @property
    @abstractmethod
    def id_short(self) -> str or None:
        pass

    @property
    @abstractmethod
    def category(self) -> str or None:
        pass

    @property
    @abstractmethod
    def description(self) -> str or None:
        pass

    @property
    @abstractmethod
    def parent(self) -> 'Referable' or None:
        pass


class Identifiable(Referable):
    """
    An element that has a globally unique identifier.

    :var administration: Administrative information of an identifiable element.
    :var identification: The globally unique identification of the element.
    """

    @property
    @abstractmethod
    def administration(self) -> AdministrativeInformation or None:
        pass

    @property
    @abstractmethod
    def identification(self) -> 'Identifier':
        pass


class HasSemantics(ABC):
    """
    Element that can have a semantic definition.

    :var semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the element.
                       The semantic id may either reference an external global id or it may reference a referable model
                       element of kind=Type that defines the semantics of the element.
    """

    @property
    @abstractmethod
    def semantic_id(self) -> str or None:
        pass


class HasKind(ABC):
    """
    An element with a kind is an element that can either represent a type or an instance.
    Default for an element is that it is representing an instance.

    :var kind: Kind of the element: either type or instance. Default = Instance.
    """

    @property
    @abstractmethod
    def kind(self) -> Kind:
        pass


class Constraint(ABC):
    """
    A constraint is used to further qualify an element.
    """

    pass


class Qualifiable(ABC):
    """
    The value of a qualifiable element may be further qualified by one or more qualifiers or complex formulas.

    :var qualifier: Additional qualification of a qualifiable element.
    """

    @property
    @abstractmethod
    def qualifier(self) -> Constraint:
        pass


class Formula(Constraint):
    """
    A formula is used to describe constraints by a logical expression.

    :var depends_on: A formula may depend on referable or even external global elements - assumed that can be
                        referenced and their value may be evaluated - that are used in the logical expression.
    """

    def __init__(self, depends_on: [str]):
        self.depends_on: [str] = depends_on


class Qualifier(Constraint, HasSemantics):
    """
    A qualifier is a type-value pair that makes additional statements w.r.t. the value of the element.

    :var qualifier_type: The qualifier_type describes the type of the qualifier that is applied to the element.
    :var qualifier_value: The qualifier_value is the value of the qualifier.
    :var qualifier_value_id: Reference to the global unqiue id of a coded value.
    :var semantic_id: The semantic_id defined in the HasSemantics class.
    """

    def __init__(self, qualifier_type: str, qualifier_value: str or None, qualifier_value_id: str or None,
                 semantic_id: str or None):
        self.qualifier_type: str = qualifier_type
        self.qualifier_value: str or None = qualifier_value
        self.qualifier_value_id: str or None = qualifier_value_id
        self.semantic_id: str or None = semantic_id
