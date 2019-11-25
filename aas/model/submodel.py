import abc
from typing import List, Optional

from . import util


class SubmodelElement(util.HasDataSpecification, util.Referable, util.Qualifiable, util.HasSemantics, util.HasKind,
                      metaclass=abc.ABCMeta):
    """
    A submodel element is an element suitable for the description and differentiation of assets.

    NOTE: The concept of type and instance applies to submodel elements. Properties are special submodel elements.
    The property types are defined in dictionaries (like the IEC Common Data Dictionary or eCl@ss),
    they do not have a value. The property type (kind=Type) is also called data element type in some standards.
    The property instances (kind=Instance) typically have a value. A property instance is also called
    property-value pair in certain standards.
    """

    def __init__(self, id_short: str, has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__()
        self.has_data_specification: List[util.Reference] = has_data_specification
        self.semantic_id: Optional[util.Reference] = semantic_id
        self.id_short: str = id_short
        self.category: Optional[str] = category
        self.description: Optional[util.LangStringSet] = description
        self.parent: Optional[util.Reference] = parent
        self.qualifier: List[util.Constraint] = qualifier
        self.kind: util.ModelingKind = kind


class Submodel(util.HasDataSpecification, util.HasSemantics, util.Identifiable, util.Qualifiable, util.HasKind):
    """
    A Submodel defines a specific aspect of the asset represented by the AAS. A submodel is used to structure
    the virtual representation and technical functionality of an Administration Shell into distinguishable parts.
    Each submodel refers to a well-defined domain or subject matter. Submodels can become standardized
    and thus become submodels types. Submodels can have different life-cycles.

    :ivar submodel_element: A submodel consists of zero or more submodel elements.
    """

    def __init__(self, identification: util.Identifier, submodel_element: List[SubmodelElement] = [],
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 administration: Optional[util.AdministrativeInformation] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__()
        self.submodel_element: List[SubmodelElement] = submodel_element
        self.has_data_specification: List[util.Reference] = has_data_specification
        self.semantic_id: Optional[util.Reference] = semantic_id
        self.administration: Optional[util.AdministrativeInformation] = administration
        self.identification: util.Identifier = identification
        self.qualifier: List[util.Constraint] = qualifier
        self.kind: util.ModelingKind = kind


class DataElement(SubmodelElement, metaclass=abc.ABCMeta):
    """
    A data element is a submodel element that is not further composed out of other submodel elements.
    A data element is a submodel element that has a value. The type of value differs for different subtypes
    of data elements.

    << abstract >>
    """

    def __init__(self, id_short: str, has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)


class Property(DataElement):
    """
    A property is a data element that has a single value.

    :ivar value_type: Data type of the value
    :ivar value: The value of the property instance.
    :ivar value_id: Reference to the global unique id of a coded value.
    """

    def __init__(self, id_short: str, value_type: util.DataTypeDef, value: Optional[util.ValueDataType] = None, value_id: Optional[util.Reference] = None,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value_type: util.DataTypeDef = value_type
        self.value: Optional[util.ValueDataType] = value
        self.value_id: Optional[util.Reference] = value_id


class MultiLanguageProperty(DataElement):
    """
    A property is a data element that has a multi language value.

    :ivar value: The value of the property instance.
    :ivar value_id: Reference to the global unique id of a coded value.
    """

    def __init__(self, id_short: str, value: Optional[util.LangStringSet] = None, value_id: Optional[util.Reference] = None,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value: Optional[util.LangStringSet] = value
        self.value_id: Optional[util.Reference] = value_id


class Range(DataElement):
    """
    A property is a data element that has a multi language value.

    :ivar value_type: Data type of the min and max
    :ivar min_: The minimum value of the range. If the min value is missing then the value is assumed to be negative
                infinite.
    :ivar max_: The maximum of the range. If the max value is missing then the value is assumed to be positive infinite
    """

    def __init__(self, id_short: str, value_type: util.DataTypeDef, min_: Optional[util.ValueDataType] = None,
                 max_: Optional[util.ValueDataType] = None,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value_type: util.DataTypeDef = value_type
        self.min_: Optional[util.ValueDataType] = min_
        self.max_: Optional[util.ValueDataType] = max_


class Blob(DataElement):
    """
    A BLOB is a data element that represents a file that is contained with its source code in the value attribute.

    :ivar value: The value of the BLOB instance of a blob data element.
                 Note: In contrast to the file property the file content is stored directly as value in
                 the Blob data element.
    :ivar mime_type: Mime type of the content of the BLOB. The mime type states which file extension the file has.
                     Valid values are e.g. “application/json”, “application/xls”, ”image/jpg”. The allowed values
                     are defined as in RFC2046.
    """

    def __init__(self, id_short: str, mime_type: util.MimeType, value: Optional[util.BlobType] = None,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value: Optional[util.BlobType] = value
        self.mime_type: util.MimeType = mime_type


class File(DataElement):
    """
    A File is a data element that represents a file via its path description.

    :ivar value: Path and name of the referenced file (without file extension). The path can be absolute or relative.
                 Note: The file extension is defined by using a qualifier of type “MimeType”.
    :ivar mime_type: Mime type of the content of the File.
    """

    def __init__(self, id_short: str, mime_type: util.MimeType, value: Optional[util.PathType],
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value: Optional[util.PathType] = value
        self.mime_type: util.MimeType = mime_type


class ReferenceElement(DataElement):
    """
    A reference element is a data element that defines a reference to another element within the same or another AAS
    or a reference to an external object or entity.

    :ivar value: Reference to any other referable element of the same of any other AAS
                 or a reference to an external object or entity.
    """

    def __init__(self, id_short: str, value: Optional[util.Reference], has_data_specification: List[util.Reference] = [],
                 semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None, description: Optional[util.LangStringSet] = None,
                 parent: Optional[util.Reference] = None, qualifier: List[util.Constraint] = [],
                 kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value: Optional[util.Reference] = value


class SubmodelElementCollection(SubmodelElement):
    """
    A submodel element collection is a set or list of submodel elements.

    :ivar value: Submodel element contained in the collection.
    :ivar ordered: If ordered=false then the elements in the property collection are not ordered.
                   If ordered=true then the elements in the collection are ordered. Default = false
    :ivar allow_duplicates: If allow_duplicates=true then it is allowed that the collection contains the same element
                            several times. Default = false
    """

    def __init__(self, id_short: str, value: List[SubmodelElement] = [], ordered: Optional[bool] = False,
                 allow_duplicates: Optional[bool] = False, has_data_specification: List[util.Reference] = [],
                 semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None, description: Optional[util.LangStringSet] = None,
                 parent: Optional[util.Reference] = None, qualifier: List[util.Constraint] = [],
                 kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.value: List[SubmodelElement] = value
        self.ordered: Optional[bool] = ordered
        self.allow_duplicates: Optional[bool] = allow_duplicates


class RelationshipElement(SubmodelElement):
    """
    A relationship element is used to define a relationship between two referable elements.

    :ivar first: Reference to the first element in the relationship taking the role of the subject which have to be of
                 class Referable.

    :ivar second: Reference to the second element in the relationship taking the role of the object which have to be of
                 class Referable.
    """

    def __init__(self, id_short: str, first: util.Reference, second: util.Reference,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.first: util.Reference = first
        self.second: util.Reference = second


class AnnotatedRelationshipElement(SubmodelElement):
    """
    An annotated relationship element is a relationship element that can be annotated with additional data elements.

    :ivar annotation: Annotations that hold for the relationship between to elements
    """

    def __init__(self, id_short: str, annotation: List[util.Reference] = [],
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.annotation: List[util.Reference] = annotation


class OperationVariable(SubmodelElement):
    """
    An operation variable is a submodel element that is used as input or output variable of an operation.

    :ivar value: Describes the needed argument for an operation via a submodel element of kind=Type.
    """

    def __init__(self, id_short: str, value: SubmodelElement, has_data_specification: List[util.Reference] = [],
                 semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.TYPE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        # Constraint AASd-008: The submodel element shall be of kind=Type.
        if value.kind != util.ModelingKind.TYPE:
            raise ValueError("value must be of kind=Type")
        self.value: SubmodelElement = value


class Operation(SubmodelElement):
    """
    An operation is a submodel element with input and output variables.

    :ivar input_variable: Input parameter of the operation
    :ivar output_variable: Output parameter of the operation
    :ivar inoutput_variable: Parameter that is input and output of the operation
    """
    def __init__(self, id_short: str, input_variable: List[OperationVariable] = [], output_variable: List[OperationVariable] = [],
                 inoutput_variable: List[OperationVariable] = [],
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.input_variable: List[OperationVariable] = input_variable
        self.output_variable: List[OperationVariable] = output_variable
        self.inoutput_variable: List[OperationVariable] = inoutput_variable


class Capability(SubmodelElement):
    """
    A capability is the implementation-independent description of the potential of an asset to achieve a certain effect
    in the physical or virtual world

    """

    def __init__(self, id_short: str, has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)


class Entity(SubmodelElement):
    """
    An entity is a submodel element that is used to model entities

    :ivar entity_type: Describes whether the entity is a co-managed or a self-managed entity.
    :ivar statement: Describes statements applicable to the entity by a set of submodel elements, typically with a
                     qualified value.
    :ivar asset: Reference to the asset the entity is representing.
    """

    def __init__(self, id_short: str, entity_type: util.EntityType, statements: List[SubmodelElement] = [],
                 asset: Optional[util.Reference] = None,
                 has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.entity_type: util.EntityType = entity_type
        self.statements: List[SubmodelElement] = statements
        self.asset: Optional[util.Reference] = asset


class Event(SubmodelElement, metaclass=abc.ABCMeta):
    """
    An event
    """

    def __init__(self, id_short: str, has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)


class BasicEvent(Event):
    """
    An event

    :ivar observed: Reference to the data or other elements that are being observed
    """

    def __init__(self, id_short: str, observed: util.Reference, has_data_specification: List[util.Reference] = [], semantic_id: Optional[util.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None,
                 qualifier: List[util.Constraint] = [], kind: util.ModelingKind = util.ModelingKind.INSTANCE):
        super().__init__(id_short, has_data_specification, semantic_id, category, description, parent, qualifier, kind)
        self.observed: util.Reference = observed