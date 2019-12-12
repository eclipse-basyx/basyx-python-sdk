from typing import Optional, List

from . import base


class DataSpecificationIEC61360(base.DataSpecification):
    """
    Data Specification of a data object following IEC61360.
    """
    def __init__(self,
                 preferred_name: str,
                 short_name: str,
                 data_type: str,
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
                 value_list: Optional[List[str]] = None,
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
        """
        self.preferred_name:  str = preferred_name
        self.short_name: str = short_name
        self.data_type: str = data_type
        self.definition: str = definition
        self.code: str = code
        self.administration: base.AdministrativeInformation = administration
        self.identification: base.Identifier = identification
        self.id_short: str = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.unit: Optional[str] = unit
        self.unit_id: Optional[base.Reference] = unit_id
        self.source_of_definition: Optional[str] = source_of_definition
        self.symbol: Optional[str] = symbol
        self.value_format: Optional[str] = value_format
        self.value_list: Optional[List[str]] = value_list
