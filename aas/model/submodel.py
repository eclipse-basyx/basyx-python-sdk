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
This module contains everything needed to model Submodels and define Events according to the AAS metamodel.
"""

import abc
from typing import Optional, Set, Iterable, TYPE_CHECKING

from . import base
if TYPE_CHECKING:
    from . import aas


class SubmodelElement(base.Referable, base.HasDataSpecification, base.Qualifiable, base.HasSemantics, base.HasKind,
                      metaclass=abc.ABCMeta):
    """
    A submodel element is an element suitable for the description and differentiation of assets.

    NOTE: The concept of type and instance applies to submodel elements. Properties are special submodel elements.
    The property types are defined in dictionaries (like the IEC Common Data Dictionary or eCl@ss),
    they do not have a value. The property type (kind=Type) is also called data element type in some standards.
    The property instances (kind=Instance) typically have a value. A property instance is also called
    property-value pair in certain standards.
    """

    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of SubmodelElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__()
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.data_specification: Set[base.Reference] = set() \
            if data_specification is None else data_specification
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.qualifier: Set[base.Constraint] = set() if qualifier is None else qualifier
        self._kind: base.ModelingKind = kind


class Submodel(base.Identifiable, base.HasDataSpecification, base.HasSemantics, base.HasKind, base.Qualifiable,
               base.Namespace):
    """
    A Submodel defines a specific aspect of the asset represented by the AAS.

    A submodel is used to structure the virtual representation and technical functionality of an Administration Shell
    into distinguishable parts. Each submodel refers to a well-defined domain or subject matter. Submodels can become
    standardized and thus become submodels types. Submodels can have different life-cycles.

    :ivar submodel_element: Unordered list of submodel elements
    """

    def __init__(self,
                 identification: base.Identifier,
                 submodel_element: Iterable[SubmodelElement] = (),
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Submodel

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param submodel_element: Unordered list of submodel elements
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        """

        super().__init__()
        self.identification: base.Identifier = identification
        self.submodel_element = base.NamespaceSet(self, submodel_element)
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.data_specification: Set[base.Reference] = set() \
            if data_specification is None else data_specification
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.qualifier: Set[base.Constraint] = set() if qualifier is None else qualifier
        self._kind: base.ModelingKind = kind


class DataElement(SubmodelElement, metaclass=abc.ABCMeta):
    """
    A data element is a submodel element that is not further composed out of other submodel elements.
    A data element is a submodel element that has a value. The type of value differs for different subtypes
    of data elements.

    << abstract >>
    """

    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of DataElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)


class Property(DataElement):
    """
    A property is a data element that has a single value.

    :ivar value_type: Data type of the value
    :ivar value: The value of the property instance.
    :ivar value_id: Reference to the global unique id of a coded value.
                    Constraint AASd-007: if both, the value and the valueId are present then the value needs to be
                                         identical to the value of the referenced coded value in valueId
    """

    def __init__(self,
                 id_short: str,
                 value_type: base.DataTypeDef,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Property

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value_type: Data type of the value
        :param value: The value of the property instance.
        :param value_id: Reference to the global unique id of a coded value.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value_type: base.DataTypeDef = value_type
        self.value: Optional[base.ValueDataType] = value
        self.value_id: Optional[base.Reference] = value_id


class MultiLanguageProperty(DataElement):
    """
    A property is a data element that has a multi language value.

    :ivar value: The value of the property instance.
    :ivar value_id: Reference to the global unique id of a coded value.
                    Constraint AASd-012: if both, the value and the valueId are present then for each string in a
                                         specific language the meaning must be the same as specified in valueId.
    """

    def __init__(self,
                 id_short: str,
                 value: Optional[base.LangStringSet] = None,
                 value_id: Optional[base.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of MultiLanguageProperty

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: The value of the property instance.
        :param value_id: Reference to the global unique id of a coded value.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                           (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value: Optional[base.LangStringSet] = value
        self.value_id: Optional[base.Reference] = value_id


class Range(DataElement):
    """
    A property is a data element that has a multi language value.

    :ivar value_type: Data type of the min and max
    :ivar min_: The minimum value of the range. If the min value is missing then the value is assumed to be negative
                infinite.
                Constraint AASd-013: In case of a range with kind=Instance either the min or the max value or both need
                                     to be defined
    :ivar max_: The maximum of the range. If the max value is missing then the value is assumed to be positive infinite
    """

    def __init__(self,
                 id_short: str,
                 value_type: base.DataTypeDef,
                 min_: Optional[base.ValueDataType] = None,
                 max_: Optional[base.ValueDataType] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Range

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value_type: Data type of the min and max
        :param min_: The minimum value of the range. If the min value is missing then the value is assumed to be
                     negative infinite.
        :param max_: The maximum of the range. If the max value is missing then the value is assumed to be positive
                     infinite
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value_type: base.DataTypeDef = value_type
        self.min_: Optional[base.ValueDataType] = min_
        self.max_: Optional[base.ValueDataType] = max_


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

    def __init__(self,
                 id_short: str,
                 mime_type: base.MimeType,
                 value: Optional[base.BlobType] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Blob

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: The value of the BLOB instance of a blob data element.
                      Note: In contrast to the file property the file content is stored directly as value in the Blob
                            data element.
        :param mime_type: Mime type of the content of the BLOB. The mime type states which file extension the file has.
                          Valid values are e.g. “application/json”, “application/xls”, ”image/jpg”. The allowed values
                          are defined as in RFC2046.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value: Optional[base.BlobType] = value
        self.mime_type: base.MimeType = mime_type


class File(DataElement):
    """
    A File is a data element that represents a file via its path description.

    :ivar value: Path and name of the referenced file (without file extension). The path can be absolute or relative.
                 Note: The file extension is defined by using a qualifier of type “MimeType”.
    :ivar mime_type: Mime type of the content of the File.
    """

    def __init__(self,
                 id_short: str,
                 mime_type: base.MimeType,
                 value: Optional[base.PathType] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of File

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param mime_type: Mime type of the content of the File.
        :param value: Path and name of the referenced file (without file extension). The path can be absolute or
                      relative.
                      Note: The file extension is defined by using a qualifier of type “MimeType”.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value: Optional[base.PathType] = value
        self.mime_type: base.MimeType = mime_type


class ReferenceElement(DataElement):
    """
    A reference element is a data element that defines a reference to another element within the same or another AAS
    or a reference to an external object or entity.

    :ivar value: Reference to any other referable element of the same of any other AAS
                 or a reference to an external object or entity.
    """

    def __init__(self,
                 id_short: str,
                 value: Optional[base.AASReference] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of ReferenceElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: Reference to any other referable element of the same of any other AAS or a reference to an
                      external object or entity.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value: Optional[base.AASReference] = value


class SubmodelElementCollection(SubmodelElement, base.Namespace, metaclass=abc.ABCMeta):
    """
    A submodel element collection is a set or list of submodel elements.

    << abstract >>

    :ivar value: Ordered or unordered list of submodel elements
    :ivar ordered: If ordered=false then the elements in the property collection are not ordered. If ordered=true then
                   the elements in the collection are ordered.
                   `ordered` shall not be set directly, instead one of the subclasses
                   `SubmodelElementCollectionOrdered` or `SubmodelElementCollectionUnordered` shall be used.
    """

    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of SubmodelElementCollection

        This class is abstract and should not used for instances; instead one of the subclasses
        `SubmodelElementCollectionOrdered` or `SubmodelElementCollectionUnordered` shall be used.

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value: base.NamespaceSet[SubmodelElement] = None  # type: ignore

    @property
    @abc.abstractmethod
    def ordered(self):
        pass


class SubmodelElementCollectionOrdered(SubmodelElementCollection):
    """
    A SubmodelElementCollectionOrdered is an ordered list of submodel elements.
    """

    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of SubmodelElementCollection

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: Ordered list of submodel elements.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value = base.OrderedNamespaceSet(self, value)

    @property
    def ordered(self):
        return True


class SubmodelElementCollectionUnordered(SubmodelElementCollection):
    """
    A SubmodelElementCollectionOrdered is an unordered list of submodel elements.
    """

    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of SubmodelElementCollection

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: Unordered list of submodel elements.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.value = base.NamespaceSet(self, value)

    @property
    def ordered(self):
        return False


class RelationshipElement(SubmodelElement):
    """
    A relationship element is used to define a relationship between two referable elements.

    :ivar first: Reference to the first element in the relationship taking the role of the subject which have to be of
                 class Referable.

    :ivar second: Reference to the second element in the relationship taking the role of the object which have to be of
                 class Referable.
    """

    def __init__(self,
                 id_short: str,
                 first: base.AASReference,
                 second: base.AASReference,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of RelationshipElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param first: Reference to the first element in the relationship taking the role of the subject which have to
                      be of class Referable.
        :param second: Reference to the second element in the relationship taking the role of the object which have to
                       be of class Referable.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.first: base.AASReference = first
        self.second: base.AASReference = second


class AnnotatedRelationshipElement(RelationshipElement):
    """
    An annotated relationship element is a relationship element that can be annotated with additional data elements.

    :ivar annotation: Unordered list of annotations that hold for the relationship between to elements
    """

    def __init__(self,
                 id_short: str,
                 first: base.AASReference,
                 second: base.AASReference,
                 annotation: Optional[Set[base.AASReference[DataElement]]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of AnnotatedRelationshipElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param annotation: Unordered list of annotations that hold for the relationship between to elements
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, first, second, category, description, parent, data_specification, semantic_id,
                         qualifier, kind)
        self.annotation: Set[base.AASReference[DataElement]] = set() if annotation is None else annotation


class OperationVariable(SubmodelElement):
    """
    An operation variable is a submodel element that is used as input or output variable of an operation.

    :ivar value: Describes the needed argument for an operation via a submodel element of kind=Type.
                 Constraint AASd-008: The submodel element value of an operation variable shall be of kind=Template.
    """

    def __init__(self,
                 id_short: str,
                 value: SubmodelElement,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of OperationVariable

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: Describes the needed argument for an operation via a submodel element of kind=Type.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                         (from base.Qualifiable)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        # Constraint AASd-008: The submodel element shall be of kind=Template.
        self.value: SubmodelElement = value  # TODO check the kind of the object in value


class Operation(SubmodelElement, base.Namespace):
    """
    An operation is a submodel element with input and output variables.

    :ivar input_variable: Unordered list of input parameters of the operation
    :ivar output_variable: Unordered list of output parameters of the operation
    :ivar in_output_variable: Unordered list of parameters that are input and output of the operation
    """
    def __init__(self,
                 id_short: str,
                 input_variable: Iterable[OperationVariable] = (),
                 output_variable: Iterable[OperationVariable] = (),
                 in_output_variable: Iterable[OperationVariable] = (),
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Operation

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param input_variable: Unordered list of input parameters of the operation
        :param output_variable: Unordered list output parameters of the operation
        :param in_output_variable: Unordered list of parameters that is input and output of the operation
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.input_variable: base.NamespaceSet[OperationVariable] = base.NamespaceSet(self, input_variable)
        self.output_variable: base.NamespaceSet[OperationVariable] = base.NamespaceSet(self, output_variable)
        self.in_output_variable: base.NamespaceSet[OperationVariable] = base.NamespaceSet(self, in_output_variable)


class Capability(SubmodelElement):
    """
    A capability is the implementation-independent description of the potential of an asset to achieve a certain effect
    in the physical or virtual world
    """

    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Capability

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)


class Entity(SubmodelElement, base.Namespace):
    """
    An entity is a submodel element that is used to model entities

    :ivar entity_type: Describes whether the entity is a co-managed or a self-managed entity.
    :ivar statement: Unordered list of statements applicable to the entity, typically with a qualified value.
    :ivar asset: Reference to the asset the entity is representing.
                 Constraint AASd-014: The asset attribute must be set if entityType is set to “SelfManagedEntity”. It
                 is empty otherwise.
    """

    def __init__(self,
                 id_short: str,
                 entity_type: base.EntityType,
                 statement: Iterable[SubmodelElement] = (),
                 asset: Optional[base.AASReference["aas.Asset"]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Entity

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param entity_type: Describes whether the entity is a co-managed or a self-managed entity.
        :param statement: Unordered list of statements applicable to the entity, typically with a qualified value.
        :param asset: Reference to the asset the entity is representing.
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.entity_type: base.EntityType = entity_type
        self.statement = base.NamespaceSet(self, statement)
        if self.entity_type == base.EntityType.SELF_MANAGED_ENTITY and asset is None:
            raise ValueError("A self-managed entity has to have an asset-reference")
        if self.entity_type == base.EntityType.SELF_MANAGED_ENTITY:
            self.asset: Optional[base.AASReference["aas.Asset"]] = asset
        else:
            self.asset = None


class Event(SubmodelElement, metaclass=abc.ABCMeta):
    """
    An event
    """

    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Event

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)


class BasicEvent(Event):
    """
    An event

    :ivar observed: Reference to the data or other elements that are being observed
    """

    def __init__(self,
                 id_short: str,
                 observed: base.AASReference,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 data_specification: Optional[Set[base.Reference]] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of BasicEvent

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param observed: Reference to the data or other elements that are being observed
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, data_specification, semantic_id, qualifier, kind)
        self.observed: base.AASReference = observed
