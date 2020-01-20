# Copyright 2019 PyI40AAS Contributors
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
In this module, you can find data specification templates.
Current Data specification templates:
    DataSpecification61360
"""

from typing import Optional, Set
from enum import Enum, unique

from aas.model import base


@unique
class DataTypeIEC61360(Enum):
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
class LevelType(Enum):
    """
    Level types for the level_type in DataSpecificationIEC61360
    """
    MIN = 0
    MAX = 1
    NOM = 2
    TYP = 3


class DataSpecificationIEC61360(base.DataSpecification):
    """
    Data Specification of a data object following IEC61360.
    """
    def __init__(self,
                 preferred_name: str,
                 short_name: str,
                 data_type: DataTypeIEC61360,
                 definition: str,
                 code: str,
                 administration: base.AdministrativeInformation,
                 identification: base.Identifier,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 unit: Optional[str] = None,
                 unit_id: Optional[base.Reference] = None,
                 source_of_definition: Optional[str] = None,
                 symbol: Optional[str] = None,
                 value_format: Optional[str] = None,
                 value_list: Optional[base.ValueList] = None,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 level_types: Optional[Set[LevelType]] = None,
                 ):
        """
        Initializer of DataSpecificationIEC61360

        :param preferred_name: preferred of the data object
        :param short_name: short name of the data object
        :param data_type: data type of the data object
        :param definition: definition of the data object
        :param code: code
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints. (from
                         base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
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
        super().__init__(administration, identification, id_short, category, description, parent)
        self.preferred_name:  str = preferred_name
        self.short_name: str = short_name
        self.data_type: DataTypeIEC61360 = data_type
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
        self.level_types: Optional[Set[LevelType]] = level_types
