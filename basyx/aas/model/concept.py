# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module contains the class :class:`~.ConceptDescription` from the AAS meta model
as well as specialized :class:`ConceptDescriptions <.ConceptDescription>` like :class:`~.IEC61360ConceptDescription`.
"""
from enum import unique, Enum
from typing import Optional, Set, Type, Iterable

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
    "QUALIFIER"
}


class ConceptDescription(base.Identifiable):
    """
    The semantics of a :class:`~.Property` or other elements that may have a semantic description is defined by a
    concept description.

    The description of the concept should follow a standardized schema (realized as data specification template).

    *Note:* Compare :attr:`~.ConceptDescription.is_case_of` to is-case-of relationship in ISO 13584-32 & IEC EN 61360

    :ivar ~.identification: The globally unique identification of the element. (inherited from
                            :class:`~aas.model.base.Identifiable`)
    :ivar is_case_of: Unordered list of global :class:`References <aas.model.base.Reference>` to external definitions
                      the concept is compatible to or was derived from.
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
                    (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an identifiable element. (inherited from
                          :class:`~aas.model.base.Identifiable`)
    :ivar extension: An extension of the element. (from
                     :class:`~aas.model.base.HasExtension`)
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
                 extension: Iterable[base.Extension] = ()):

        super().__init__()
        self.identification: base.Identifier = identification
        self.is_case_of: Set[base.Reference] = set() if is_case_of is None else is_case_of
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.extension = base.NamespaceSet(self, [("name", True)], extension)

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
    Data types for data_type in :class:`DataSpecificationIEC61360 <.IEC61360ConceptDescription>`
    The data types are:

    :cvar DATE:
    :cvar STRING:
    :cvar STRING_TRANSLATABLE:
    :cvar REAL_MEASURE:
    :cvar REAL_COUNT:
    :cvar REAL_CURRENCY:
    :cvar BOOLEAN:
    :cvar URL:
    :cvar RATIONAL:
    :cvar RATIONAL_MEASURE:
    :cvar TIME:
    :cvar TIMESTAMP:
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
    The level types are:

    :cvar MIN:
    :cvar MAX:
    :cvar NOM:
    :cvar TYP:
    """
    MIN = 0
    MAX = 1
    NOM = 2
    TYP = 3


class IEC61360ConceptDescription(ConceptDescription):
    """
    A specialized :class:`~.ConceptDescription` to define concepts according to IEC61360

    :ivar preferred_name: Preferred name of the data object
    :ivar short_name: Short name of the data object
    :ivar data_type: Data type of the data object
    :ivar definition: Definition of the data object
    :ivar ~.identification: The globally unique identification of the element. (inherited from
                            :class:`~aas.model.base.Identifiable`)
    :ivar is_case_of: Unordered list of global :class:`References <aas.model.base.Reference>` to external definitions
                      the concept is compatible to or was derived from.
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
                    (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an identifiable element. (inherited from
                          :class:`~aas.model.base.Identifiable`)
    :ivar unit: Optional unit of the data object
    :ivar unit_id: Optional reference to a unit id
    :ivar source_of_definition: Optional source of the definition
    :ivar symbol: Optional unit symbol
    :ivar value_format: Optional format of the values
    :ivar value_list: Optional list of values
    :ivar value: Optional value data type object
    :ivar value_id: Optional reference to the value
    :ivar level_types: Optional set of level types of the DataSpecificationContent
    :ivar extension: An extension of the element. (from
                     :class:`~aas.model.base.HasExtension`)
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
                 extension: Iterable[base.Extension] = ()):

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
