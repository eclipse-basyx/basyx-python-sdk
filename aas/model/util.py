import abc
from enum import Enum, unique
from typing import List, Optional


DataTypeDef = str
BlobType = bytearray
MimeType = str
PathType = str
QualifierType = str
ValueDataType = str
langString = str


@unique
class IdentifierType(Enum):
    """
    Enumeration of different types of Identifiers for global identification

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
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
    ANNOTATION_RELATIONSHIP_ELEMENT = 1001
    BASIC = 1002
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
    REFRENCE_ELEMENT = 1014
    RELATIONSHIP_ELEMENT = 1015
    SUBMODEL_ELEMENT = 1016
    SUBMODEL_ELEMENT_COLLECTION = 1017
    VIEW = 1018

    # KeyElements starting from 2000
    GLOBAL_REFERENCE = 2000
    FRAGMENT_REFERNCE = 2001


class KeyType(Enum):
    """
    Enumeration for denoting the type of the key value.

    :cvar IRDI: IRDI (International Registration Data Identifier) according to ISO29002-5 as an Identifierscheme for
                properties and classifications.
    :cvar IRI: IRI according to Rfc 3987. Every URI is an IRI
    :cvar CUSTOM: Custom identifiers like GUIDs (globally unique Identifiers)
    :cvar IDSHORT: Identifying string of the element within its name space.
    :cvar FRAGMENT_ID: Identifier of a fragment within a file
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

    :cvar CO_MANAGED_ENTITY: For co-managed entities there is no separat AAS. Co-managed entities need to be part of a
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
    :cvar INSTANCE: concrete, clearly identifiable component of a certain template
    """

    TYPE = 0
    INSTANCE = 1


@unique
class AssetKind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.

    :cvar TYPE: hardware or software element which specifies the common attributes shared by all instances of the type
    :cvar INSTANCE: concrete, clearly identifiable component of a certain type
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

    def __init__(self, type_: KeyElements, local: bool, value: str, id_type: KeyType):
        self.type_: KeyElements = type_
        self.local: bool = local
        self.value: str = value
        self.id_type: KeyType = id_type


class Reference:
    """
    Reference to either a model element of the same or another AAs or to an external entity.

    A reference is an ordered list of keys, each key referencing an element. The complete list of keys may for
    example be concatenated to a path that then gives unique access to an element or entity

    :ivar: key: Unique reference in its name space.
    """

    def __init__(self, keys: List[Key]):
        self.keys: List[Key] = keys


class AdministrativeInformation:
    """
    Administrative meta-information for an element like version information.

    :ivar version: Version of the element.
    :ivar revision: Revision of the element.
    """

    def __init__(self, version: Optional[str] = None, revision: Optional[str] = None):
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

    :ivar data_specification: Global reference to the data specification template used by the element.
    """

    def __init__(self):
        self.data_specification: List[Reference] = []


class Referable(metaclass=abc.ABCMeta):
    """
    An element that is referable by its id_short. This id is not globally unique. This id is unique within
    the name space of the element.

    << abstract >>

    :ivar id_short: Identifying string of the element within its name space.
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
    :ivar description: Description or comments on the element.
    :ivar parent: Reference to the next referable parent element of the element. TODO how to check?
    """

    def __init__(self):
        self.id_short: str = ""
        self.category: Optional[str] = None
        self.description: Optional[LangStringSet] = None
        self.parent: Optional[Reference] = None


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
        self.kind: ModelingKind = ModelingKind.INSTANCE


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

    def __init__(self, depends_on: List[Reference] = []):
        super().__init__()
        self.depends_on: List[Reference] = depends_on


class Qualifier(Constraint, HasSemantics):
    """
    A qualifier is a type-value pair that makes additional statements w.r.t. the value of the element.

    :ivar type_: The type of the qualifier that is applied to the element.
    :ivar value_type: Data type of the qualifier value
    :ivar value: The value of the qualifier.
    :ivar value_id: Reference to the global unique id of a coded value.
    :ivar semantic_id: The semantic_id defined in the HasSemantics class.
    """

    def __init__(self, type_: QualifierType, value_type: DataTypeDef, value: Optional[ValueDataType] = None, value_id: Optional[Reference] = None,
                 semantic_id: Optional[Reference] = None):
        super().__init__()
        self.type_: QualifierType = type_
        self.value_type: DataTypeDef = value_type
        self.value: Optional[ValueDataType] = value
        self.value_id: Optional[Reference] = value_id
        self.semantic_id: Optional[Reference] = semantic_id


class LangStringSet:
    """
    A set of strings, each annotated by the language of the string. The meaning of the string in each language shall be
    the same.

    :ivar lang_string: A string in a specified language
    """

    def __init__(self, lang_string: List[langString]):
        self.lang_string: List[langString] = lang_string


class ValueReferencePair:
    """
    A value reference pair within a value list. Each value has a global unique id defining its semantic.

    :ivar value: The value of the referenced concept definition of the value in value_id
    :ivar value_id: Global unique id of the value.
    """

    def __init__(self, value: ValueDataType, value_id: Reference):
        self.value: ValueDataType = value
        self.value_id: Reference = value_id


class ValueList:
    """
    A set of value reference pairs.

    :ivar value_reference_pair_type: A pair of a value together with its global unique id.
    """

    def __init__(self, value_reference_pair_type: List[ValueReferencePair]):
        self.value_reference_pair_type: List[ValueReferencePair] = value_reference_pair_type
