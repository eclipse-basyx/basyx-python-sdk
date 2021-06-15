# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
This module contains the classes :class:`~.ConceptDescription` and :class:`~.ConceptDictionary` from the AAS meta model
as well as specialized ConceptDescriptions like :class:`~.IEC61360ConceptDescription`.
"""
from enum import unique, Enum
from typing import Optional, Set, Type

from . import base, datatypes


class ConceptDescription(base.Identifiable):
    """
    The semantics of a :class:`~.Property` or other elements that may have a semantic description is defined by a
    concept description.

    The description of the concept should follow a standardized schema (realized as data specification template).

    :ivar ~.identification: The globally unique identification of the element.
            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar is_case_of: Unordered list of global :class:`References <aas.model.base.Reference>` to external definitions
        the concept is compatible to or was derived from.
        *Note:* Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
    :ivar id_short: Identifying string of the element within its name space.
        (inherted from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an :class:`~aas.model.base.Identifiable` element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    """

    def __init__(self,
                 identification: base.Identifier,
                 is_case_of: Optional[Set[base.Reference]] = None,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None):
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

    Typically a concept description dictionary of an AAS contains only concept descriptions of elements used within
    submodels of the AAS.

    :ivar id_short: Identifying string of the element within its name space.
        (inherted from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar concept_description: Unordered list of :class:`References <aas.model.base.AASReference>` to elements of class
        :class:`~.ConceptDescription`
    """
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 concept_description: Optional[Set[base.AASReference[ConceptDescription]]] = None):
        """
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
    A specialized :class:`~.ConceptDescription` to define concepts according to IEC61360

    :ivar ~.identification: The globally unique identification of the element.
            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar preferred_name: Preferred of the data object
    :ivar data_type: Data type of the data object
    :ivar definition: Definition of the data object
    :ivar short_name: Short name of the data object
    :ivar is_case_of: Unordered list of global :class:`References <aas.model.base.Reference>` to external definitions
        the concept is compatible to or was derived from.
        *Note:* Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
    :ivar id_short: Identifying string of the element within its name space.
        (inherted from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an :class:`~aas.model.base.Identifiable` element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar unit_id: Reference to a unit id (optional)
    :ivar source_of_definition: Source of the definition (optional)
    :ivar symbol: Unit symbol (optional)
    :ivar value_format: Format of the values (optional)
    :ivar value_list: List of values (optional)
    :ivar value: Value data type object (optional)
    :ivar value_id: :class:`~aas.model.base.Reference` to the value (optional)
    :ivar level_types: Set of level types of the DataSpecificationContent (optional)
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
