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
This module contains the classes `ConceptDescription` and `ConceptDictionary` from the AAS meta model as well as
specialized ConceptDescriptions like `IEC61360ConceptDescription`.
"""
from enum import unique, Enum
from typing import Optional, Set, Type

from . import base, datatypes


ALLOWED_CONCEPT_DESCRIPTION_CATEGORIES: Set[str] = {
    "VALUE",
    "PROPERTY",
    "REFERENCE",
    "DOCUMENT",
    "CAPABILITY",
    "RELATIONSHIP",
    "COLLECTION",
    "FUNCTION",
    "EVENT",
    "ENTITY",
    "APPLICATION_CLASS",
    "QUALIFIER",
    "VIEW"
}


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
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 extension: Optional[Set[base.Extension]] = None):
        """
        Initializer of ConceptDescription

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param is_case_of: Unordered list of global references to external definitions the concept is compatible to or
                           was derived from.
                           Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param display_name: Can be provided in several languages. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param extension: An extension of the element. (from base.HasExtension)
        """
        super().__init__()
        self.identification: base.Identifier = identification
        self.is_case_of: Set[base.Reference] = set() if is_case_of is None else is_case_of
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.extension: Set[base.Extension] = set() if extension is None else extension

    def _set_category(self, category: Optional[str]):
        if category is None:
            self._category = "PROPERTY"
        else:
            if category not in ALLOWED_CONCEPT_DESCRIPTION_CATEGORIES:
                raise base.AASConstraintViolation(
                    51,
                    "ConceptDescription must have one of the following "
                    "categories: " + str(ALLOWED_CONCEPT_DESCRIPTION_CATEGORIES)
                )
            self._category = category


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
                 preferred_name: base.LangStringSet,
                 data_type: Optional[IEC61360DataType] = None,
                 definition: Optional[base.LangStringSet] = None,
                 short_name: Optional[base.LangStringSet] = None,
                 is_case_of: Optional[Set[base.Reference]] = None,
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 administration: base.AdministrativeInformation = None,
                 unit: Optional[str] = None,
                 unit_id: Optional[base.Reference] = None,
                 source_of_definition: Optional[str] = None,
                 symbol: Optional[str] = None,
                 value_format: base.DataTypeDef = None,
                 value_list: Optional[base.ValueList] = None,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 level_types: Set[IEC61360LevelType] = None,
                 extension: Optional[Set[base.Extension]] = None):
        """
        Initializer of IEC61360ConceptDescription

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param preferred_name: preferred of the data object
        :param short_name: short name of the data object
        :param data_type: data type of the data object
        :param definition: definition of the data object
        :param is_case_of: Unordered list of global references to external definitions the concept is compatible to or
                           was derived from.
                           Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param display_name: Can be provided in several languages. (from base.Referable)
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
        :param extension: An extension of the element. (from base.HasExtension)
        """
        super().__init__(identification, is_case_of, id_short, display_name, category, description, parent,
                         administration, extension)
        self.preferred_name: base.LangStringSet = preferred_name
        self.short_name: Optional[base.LangStringSet] = short_name
        self.data_type: Optional[IEC61360DataType] = data_type
        self.definition: Optional[base.LangStringSet] = definition
        self._unit: Optional[str] = unit
        self.unit_id: Optional[base.Reference] = unit_id
        self._source_of_definition: Optional[str] = source_of_definition
        self._symbol: Optional[str] = symbol
        self.value_list: Optional[base.ValueList] = value_list
        self.value_id: Optional[base.Reference] = value_id
        self.level_types: Set[IEC61360LevelType] = level_types if level_types else set()
        self.value_format: Optional[Type[datatypes.AnyXSDType]] = value_format
        self._value: Optional[base.ValueDataType] = (datatypes.trivial_cast(value, self.value_format)
                                                     if (value is not None and self.value_format is not None) else None)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value) -> None:
        if value is None or self.value_format is None:
            self._value = None
        else:
            self._value = datatypes.trivial_cast(value, self.value_format)

    def _set_unit(self, unit: Optional[str]):
        """
        Check the input string

        Constraint AASd-100: An attribute with data type "string" is not allowed to be empty

        :param unit: unit of the data object (optional)
        :raises ValueError: if the constraint is not fulfilled
        """
        if unit == "":
            raise ValueError("unit is not allowed to be an empty string")
        self._unit = unit

    def _get_unit(self):
        return self._unit

    unit = property(_get_unit, _set_unit)

    def _set_source_of_definition(self, source_of_definition: Optional[str]):
        """
        Check the input string

        Constraint AASd-100: An attribute with data type "string" is not allowed to be empty

        :param source_of_definition: source of the definition (optional)
        :raises ValueError: if the constraint is not fulfilled
        """
        if source_of_definition == "":
            raise ValueError("source_of_definition is not allowed to be an empty string")
        self._source_of_definition = source_of_definition

    def _get_source_of_definition(self):
        return self._source_of_definition

    source_of_definition = property(_get_source_of_definition, _set_source_of_definition)

    def _set_symbol(self, symbol: Optional[str]):
        """
        Check the input string

        Constraint AASd-100: An attribute with data type "string" is not allowed to be empty

        :param symbol: unit symbol (optional)
        :raises ValueError: if the constraint is not fulfilled
        """
        if symbol == "":
            raise ValueError("symbol is not allowed to be an empty string")
        self._symbol = symbol

    def _get_symbol(self):
        return self._symbol

    symbol = property(_get_symbol, _set_symbol)
