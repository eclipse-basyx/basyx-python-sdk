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
This module contains the classes :class:`~.ConceptDescription` and :class:`~.ConceptDictionary` from the AAS meta model
as well as specialized :class:`ConceptDescriptions <.ConceptDescription>` like :class:`~.IEC61360ConceptDescription`.
"""
from enum import unique, Enum
from typing import Optional, Set, Type

from . import base, datatypes


class ConceptDescription(base.Identifiable):
    """
    The semantics of a property or other elements that may have a semantic description is defined by a concept
    description.

    The description of the concept should follow a standardized schema (realized as data specification template).

    *Note:* Compare :attr:`~.ConceptDescription.is_case_of` to is-case-of relationship in ISO 13584-32 & IEC EN 61360

    :ivar is_case_of: Unordered list of global :class:`References <aas.model.base.Reference>` to external definitions
                      the concept is compatible to or was derived from.

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
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration


class ConceptDictionary(base.Referable):
    """
    A dictionary containing :class:`ConceptDescriptions <.ConceptDescription>`.

    Typically a concept description dictionary of an AAS contains only
    :class:`ConceptDescriptions <.ConceptDescription>` of elements used within
    :class:`Submodels <aas.model.submodel.Submodel>` of the AAS.


    :param concept_description: Unordered list of :class:`References <aas.model.base.Reference>` to elements of class
                                :class:`~.ConceptDescription`
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
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.concept_description: Set[base.AASReference[ConceptDescription]] = \
            set() if concept_description is None else concept_description


# #############################################################################
# Helper types for
@unique
class IEC61360DataType(Enum):
    """
    Data types for data_type in :class:`DataSpecificationIEC61360 <.IEC61360ConceptDescription>`
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
    Level types for the level_type in :class:`DataSpecificationIEC61360 <.IEC61360ConceptDescription>`
    """
    MIN = 0
    MAX = 1
    NOM = 2
    TYP = 3


class IEC61360ConceptDescription(ConceptDescription):
    """
    A specialized :class:`~.ConceptDescription` to define concepts according to IEC61360
    """
    def __init__(self,
                 identification: base.Identifier,
                 preferred_name: base.LangStringSet,
                 data_type: Optional[IEC61360DataType] = None,
                 definition: Optional[base.LangStringSet] = None,
                 short_name: Optional[base.LangStringSet] = None,
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
                 value_format: base.DataTypeDef = None,
                 value_list: Optional[base.ValueList] = None,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 level_types: Set[IEC61360LevelType] = None,
                 ):
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
        self.preferred_name: base.LangStringSet = preferred_name
        self.short_name: Optional[base.LangStringSet] = short_name
        self.data_type: Optional[IEC61360DataType] = data_type
        self.definition: Optional[base.LangStringSet] = definition
        self.unit: Optional[str] = unit
        self.unit_id: Optional[base.Reference] = unit_id
        self.source_of_definition: Optional[str] = source_of_definition
        self.symbol: Optional[str] = symbol
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
