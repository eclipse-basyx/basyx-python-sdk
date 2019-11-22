import abc
from enum import Enum, unique
from typing import List, Optional


@unique
class IdentifierType(Enum):
    """
    Enumeration of different types of Identifiers for global identification

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
                properties and classifications.
    :cvar URI: Uniform Resource Identifier
    :cvar CUSTOM: Custom identifiers like GUIDs (globally unique Identifiers)
    """

    IRDI = 0
    URI = 1
    CUSTOM = 2


@unique
class Kind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.

    :cvar TYPE: hardware or software element which specifies the common attributes shared by all instances of the type
    :cvar INSTANCE: concrete, clearly identifiable component of a certain type
    """

    TYPE = 0
    INSTANCE = 1


@unique
class KeyElements(Enum):
    """
    Enumeration for denoting which kind of entity is referenced. They can be categorized in ReferableElements,
    IdentifiableElements and other KeyElements

    :cvar ASSET: IdentifiableElements
    :cvar ASSET_ADMINISTRATION_SHELL: IdentifiableElements
    :cvar CONCEPT_DESCRIPTION: IdentifiableElements
    :cvar SUBMODEL: IdentifiableElements
    :cvar ACCESS_PERMISSION_RULE: ReferableElements
    :cvar BLOB: ReferableElements
    :cvar CONCEPT_DICTIONARY: ReferableElements
    :cvar DATA_ELEMENT: ReferableElements
    :cvar FILE: ReferableElements
    :cvar EVENT: ReferableElements
    :cvar OPERATION: ReferableElements
    :cvar OPERATION_VARIABLE: ReferableElements
    :cvar PROPERTY: ReferableElements
    :cvar REFRENCE_ELEMENT: ReferableElements
    :cvar RELATIONSHIP_ELEMENT: ReferableElements
    :cvar SUBMODEL_ELEMENT: ReferableElements
    :cvar SUBMODEL_ELEMENT_COLLECTION: ReferableElements
    :cvar VIEW: ReferableElements
    :cvar GLOBAL_REFERENCE: KeyElement
    """

    # IdentifableElements starting from 0
    ASSET = 0
    ASSET_ADMINISTRATION_SHELL = 1
    CONCEPT_DESCRIPTION = 2
    SUBMODEL = 3

    # ReferableElements starting from 1000
    ACCESS_PERMISSION_RULE = 1000
    BLOB = 1001
    CONCEPT_DICTIONARY = 1002
    DATA_ELEMENT = 1003
    FILE = 1004
    EVENT = 1005
    OPERATION = 1006
    OPERATION_VARIABLE = 1007
    PROPERTY = 1008
    REFRENCE_ELEMENT = 1009
    RELATIONSHIP_ELEMENT = 1010
    SUBMODEL_ELEMENT = 1011
    SUBMODEL_ELEMENT_COLLECTION = 1012
    VIEW = 1013

    # KeyElements starting from 2000
    GLOBAL_REFERENCE = 2000


class KeyType(Enum):
    """
    Enumeration for denoting the type of the key value.

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
                properties and classifications.
    :cvar URI: Uniform Resource Identifier
    :cvar CUSTOM: Custom identifiers like GUIDs (globally unique Identifiers)
    :cvar IDSHORT: Identifying string of the element within its name space.
    """

    IRDI = 0
    URI = 1
    CUSTOM = 2
    IDSHORT = 3


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
    :ivar idType: Type of the key value. In case of idType = idShort local shall be true. In case type=GlobalReference
                  idType shall not be IdShort.
    """

    def __init__(self, type_: KeyElements, local: bool, value: str, idType: KeyType):
        self.type_: KeyElements = type_
        self.local: bool = local
        self.value: str = value
        self.idType: KeyType = idType


class Reference:
    """
    Reference to either a model element of the same or another AAs or to an external entity.

    A reference is an ordered list of keys, each key referencing an element. The complete list of keys may for
    example be concatenated to a path that then gives unique access to an element or entity

    :ivar: key: Unique reference in its name space.
    """

    def __init__(self, keys: Optional[List[Key]]):
        self.keys: Optional[List[Key]] = keys


class AdministrativeInformation:
    """
    Administrative meta-information for an element like version information.

    :ivar version: Version of the element.
    :ivar revision: Revision of the element.
    """

    def __init__(self, version: Optional[str], revision: Optional[str]):
        self.version: Optional[str] = version
        self.revision: Optional[str] = revision


class Identifier:
    """
    Used to uniquely identify an entity by using an identifier.

    :ivar id: Identifier of the element. Its type is defined in id_type.
    :ivar id_type: Type of the Identifier, e.g. URI, IRDI etc. The supported Identifier types are defined in
                   the enumeration "IdentifierType".
    """

    def __init__(self, id_: str, id_type: IdentifierType):
        self.id: str = id_
        self.id_type: IdentifierType = id_type


class HasDataSpecification(metaclass=abc.ABCMeta):
    """
    Element that can have data specification templates. A template defines the additional attributes an element may or
    shall have.

    << abstract >>

    :ivar has_data_specification: Global reference to the data specification template used by the element.
    """

    def __init__(self):
        self.has_data_specification: List[Reference] = []


class Referable(metaclass=abc.ABCMeta):
    """
    An element that is referable by its id_short. This id is not globally unique. This id is unique within
    the name space of the element.

    << abstract >>

    :ivar id_short: Identifying string of the element within its name space.
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
    :ivar description: Description or comments on the element.
    :ivar parent: Reference to the next referable parent element of the element.
    """

    def __init__(self):
        self.id_short: Optional[str] = None
        self.category: Optional[str] = None
        self.description: Optional[str] = None
        self.parent: Optional["Referable"] = None


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
        self.kind: Kind = Kind.Type


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

    :ivar qualifier: Additional qualification of a qualifiable element.
    """

    def __init__(self):
        self.qualifier: List[Constraint] = []


class Formula(Constraint):
    """
    A formula is used to describe constraints by a logical expression.

    :ivar depends_on: A formula may depend on referable or even external global elements - assumed that can be
                      referenced and their value may be evaluated - that are used in the logical expression.
    """

    def __init__(self, depends_on: List[Reference]):
        super().__init__()
        self.depends_on: List[Reference] = depends_on


class Qualifier(Constraint, HasSemantics):
    """
    A qualifier is a type-value pair that makes additional statements w.r.t. the value of the element.

    :ivar qualifier_type: The qualifier_type describes the type of the qualifier that is applied to the element.
    :ivar qualifier_value: The qualifier_value is the value of the qualifier.
    :ivar qualifier_value_id: Reference to the global unique id of a coded value.
    :ivar semantic_id: The semantic_id defined in the HasSemantics class.
    """

    def __init__(self, qualifier_type: str, qualifier_value: Optional[str], qualifier_value_id: Optional[Reference],
                 semantic_id: Optional[Reference]):
        super().__init__()
        self.qualifier_type: str = qualifier_type
        self.qualifier_value: Optional[str] = qualifier_value
        self.qualifier_value_id: Optional[Reference] = qualifier_value_id
        self.semantic_id: Optional[Reference] = semantic_id
