"""
This module contains the classes `ConceptDescription` and `ConceptDictionary` from the AAS meta model as well as
specialized ConceptDescriptions like `IEC61360ConceptDescription`.
"""
from enum import unique, Enum
from typing import Optional, Set

from . import base


class ConceptDescription(base.Identifiable):
    """
    The semantics of a property or other elements that may have a semantic description is defined by a concept
    description.

    The description of the concept should follow a standardized schema (realized as data specification template).

    :ivar is_case_of: Unordered list of global references to external definitions the concept is compatible to or was
                      derived from.
                      Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
    """

    def __init__(self,
                 identification: base.Identifier,
                 is_case_of: Optional[Set[base.Reference]] = None,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None):
        """
        Initializer of ConceptDescription

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param is_case_of: Unordered list of global references to external definitions the concept is compatible to or
                           was derived from.
                           Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        """
        super().__init__()
        self.identification: base.Identifier = identification
        self.is_case_of: Set[base.Reference] = set() if is_case_of is None else is_case_of
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration


class ConceptDictionary(base.Referable):
    """
    A dictionary containing concept descriptions.

    Typically a concept description dictionary of an AAS contains only concept descriptions of elements used within
    submodels of the AAS.


    :param concept_description: Unordered list of references to elements of class ConceptDescription
    """
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 concept_description: Optional[Set[base.AASReference[ConceptDescription]]] = None):
        """
        Initializer of ConceptDictionary

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints. (from
                         base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param concept_description: Unordered list of references to elements of class ConceptDescription

        TODO: Add instruction what to do after construction
        """
        super().__init__()
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.concept_description: Set[base.AASReference[ConceptDescription]] = \
            set() if concept_description is None else concept_description


# #############################################################################
# Helper types for
@unique
class IEC61360DataType(Enum):
    """
    Data types for data_type in DataSpecificationIEC61360
    """
    DATE = 0
    STRING = 1
    STRING_TRANSLATABLE = 2
    REAL_MEASURE = 3
    REAL_COUNT = 4
    REAL_CURRENCY = 5
    BOOLEAN = 6
    URL = 7
    RATIONAL = 8
    RATIONAL_MEASURE = 9
    TIME = 10
    TIMESTAMP = 11


@unique
class IEC61360LevelType(Enum):
    """
    Level types for the level_type in DataSpecificationIEC61360
    """
    MIN = 0
    MAX = 1
    NOM = 2
    TYP = 3


class IEC61360ConceptDescription(ConceptDescription):
    """
    A specialized ConceptDescription to define concepts according to IEC61360
    """
    def __init__(self,
                 identification: base.Identifier,
                 preferred_name: str,
                 short_name: str,
                 data_type: IEC61360DataType,
                 definition: str,
                 code: str,
                 is_case_of: Optional[Set[base.Reference]] = None,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: base.AdministrativeInformation = None,
                 unit: Optional[str] = None,
                 unit_id: Optional[base.Reference] = None,
                 source_of_definition: Optional[str] = None,
                 symbol: Optional[str] = None,
                 value_format: Optional[str] = None,
                 value_list: Optional[base.ValueList] = None,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 level_types: Optional[Set[IEC61360LevelType]] = None,
                 ):
        """
        Initializer of IEC61360ConceptDescription

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param preferred_name: preferred of the data object
        :param short_name: short name of the data object
        :param data_type: data type of the data object
        :param definition: definition of the data object
        :param code: code
        :param is_case_of: Unordered list of global references to external definitions the concept is compatible to or
                           was derived from.
                           Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints. (from
                         base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param unit: unit of the data object (optional)
        :param unit_id: reference to a unit id (optional)
        :param source_of_definition: source of the definition (optional)
        :param symbol: unit symbol (optional)
        :param value_format: format of the values (optional)
        :param value_list: list of values (optional)
        :param value: value data type object (optional)
        :param value_id: Reference to the value (optional)
        :param level_types: Set of level types of the DataSpecificationContent (optional)
        """
        super().__init__(identification, is_case_of, id_short, category, description, parent, administration)
        self.preferred_name:  str = preferred_name
        self.short_name: str = short_name
        self.data_type: IEC61360DataType = data_type
        self.definition: str = definition
        self.code: str = code
        self.unit: Optional[str] = unit
        self.unit_id: Optional[base.Reference] = unit_id
        self.source_of_definition: Optional[str] = source_of_definition
        self.symbol: Optional[str] = symbol
        self.value_format: Optional[str] = value_format
        self.value_list: Optional[base.ValueList] = value_list
        self.value: Optional[base.ValueDataType] = value
        self.value_id: Optional[base.Reference] = value_id
        self.level_types: Optional[Set[IEC61360LevelType]] = level_types
