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
This module contains everything needed to model Submodels and define Events according to the AAS metamodel.
"""

import abc
from typing import Optional, Set, Iterable, TYPE_CHECKING, List, Type

from . import base, datatypes
if TYPE_CHECKING:
    from . import aas


class SubmodelElement(base.Referable, base.Qualifiable, base.HasSemantics, base.HasKind, metaclass=abc.ABCMeta):
    """
    A submodel element is an element suitable for the description and differentiation of assets.

    NOTE: The concept of type and instance applies to submodel elements. Properties are special submodel elements.
    The property types are defined in dictionaries (like the IEC Common Data Dictionary or eCl@ss),
    they do not have a value. The property type (kind=Type) is also called data element type in some standards.
    The property instances (kind=Instance) typically have a value. A property instance is also called
    property-value pair in certain standards.
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
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
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.qualifier: Set[base.Constraint] = set() if qualifier is None else qualifier
        self._kind: base.ModelingKind = kind


class Submodel(base.Identifiable, base.HasSemantics, base.HasKind, base.Qualifiable, base.Namespace):
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
                 id_short: str = "NotSet",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
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
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
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
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)


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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.value_type: Type[datatypes.AnyXSDType] = value_type
        self._value: Optional[base.ValueDataType] = (datatypes.trivial_cast(value, value_type)
                                                     if value is not None else None)
        self.value_id: Optional[base.Reference] = value_id

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value) -> None:
        if value is None:
            self._value = None
        else:
            self._value = datatypes.trivial_cast(value, self.value_type)


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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                           (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.value: base.LangStringSet = dict() if value is None else value
        self.value_id: Optional[base.Reference] = value_id


class Range(DataElement):
    """
    A property is a data element that has a multi language value.

    :ivar value_type: Data type of the min and max
    :ivar min: The minimum value of the range. If the min value is missing then the value is assumed to be negative
                infinite.
                Constraint AASd-013: In case of a range with kind=Instance either the min or the max value or both need
                                     to be defined
    :ivar max: The maximum of the range. If the max value is missing then the value is assumed to be positive infinite
    """

    def __init__(self,
                 id_short: str,
                 value_type: base.DataTypeDef,
                 min: Optional[base.ValueDataType] = None,
                 max: Optional[base.ValueDataType] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Range

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value_type: Data type of the min and max
        :param min: The minimum value of the range. If the min value is missing then the value is assumed to be
                     negative infinite.
        :param max: The maximum of the range. If the max value is missing then the value is assumed to be positive
                     infinite
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.value_type: base.DataTypeDef = value_type
        self._min: Optional[base.ValueDataType] = datatypes.trivial_cast(min, value_type) if min is not None else None
        self._max: Optional[base.ValueDataType] = datatypes.trivial_cast(max, value_type) if max is not None else None

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, value) -> None:
        if value is None:
            self._min = None
        else:
            self._min = datatypes.trivial_cast(value, self.value_type)

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, value) -> None:
        if value is None:
            self._max = None
        else:
            self._max = datatypes.trivial_cast(value, self.value_type)


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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
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
                 value: Optional[base.Reference] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.value: Optional[base.Reference] = value


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
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.first: base.AASReference = first
        self.second: base.AASReference = second


class AnnotatedRelationshipElement(RelationshipElement, base.Namespace):
    """
    An annotated relationship element is a relationship element that can be annotated with additional data elements.

    :ivar annotation: Unordered list of annotations that hold for the relationship between to elements
    """

    def __init__(self,
                 id_short: str,
                 first: base.AASReference,
                 second: base.AASReference,
                 annotation: Optional[Iterable[DataElement]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of AnnotatedRelationshipElement

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param annotation: Unordered list of annotations that hold for the relationship between two elements
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, first, second, category, description, parent, semantic_id, qualifier, kind)
        if annotation is None:
            self.annotation: base.NamespaceSet[DataElement] = base.NamespaceSet(self)
        else:
            self.annotation = base.NamespaceSet(self, annotation)


class OperationVariable:
    """
    An operation variable is a submodel element that is used as input or output variable of an operation.

    :ivar value: Describes the needed argument for an operation via a submodel element of kind=Type.
                 Constraint AASd-008: The submodel element value of an operation variable shall be of kind=Template.
    """

    def __init__(self,
                 value: SubmodelElement):
        """
        Initializer of OperationVariable

        :param value: Describes the needed argument for an operation via a submodel element of kind=Type.

        TODO: Add instruction what to do after construction
        """
        # Constraint AASd-008: The submodel element shall be of kind=Template.
        self.value: SubmodelElement = value  # TODO check the kind of the object in value


class Operation(SubmodelElement):
    """
    An operation is a submodel element with input and output variables.

    :ivar input_variable: list of input parameters of the operation
    :ivar output_variable: of output parameters of the operation
    :ivar in_output_variable: of parameters that are input and output of the operation
    """
    def __init__(self,
                 id_short: str,
                 input_variable: Optional[List[OperationVariable]] = None,
                 output_variable:  Optional[List[OperationVariable]] = None,
                 in_output_variable:  Optional[List[OperationVariable]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Operation

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param input_variable: list of input parameters of the operation
        :param output_variable: list output parameters of the operation
        :param in_output_variable: list of parameters that is input and output of the operation
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.input_variable = input_variable if input_variable is not None else []
        self.output_variable = output_variable if output_variable is not None else []
        self.in_output_variable = in_output_variable if in_output_variable is not None else []


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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)


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
                 global_asset_id: Optional[base.Reference] = None,
                 specific_asset_id: Optional[base.IdentifierKeyValuePair] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Optional[Set[base.Constraint]] = None,
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE):
        """
        Initializer of Entity

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param entity_type: Describes whether the entity is a co-managed or a self-managed entity.
        :param statement: Unordered list of statements applicable to the entity, typically with a qualified value.
        :param global_asset_id: Reference to either an Asset object or a global reference to the asset the AAS is
                                representing. This attribute is required as soon as the AAS is exchanged via partners
                                in the life cycle of the asset. In a first phase of the life cycle the asset might not
                                yet have a global id but already an internal identifier. The internal identifier would
                                be modelled via “specificAssetId”.
        :param specific_asset_id: Reference to an identifier key value pair representing a specific identifier
                                  of the asset represented by the asset administration shell. See Constraint AASd-014
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.statement = base.NamespaceSet(self, statement)
        self.specific_asset_id: Optional[base.IdentifierKeyValuePair] = specific_asset_id
        self.global_asset_id: Optional[base.Reference] = global_asset_id
        self.entity_type = entity_type

    def _get_entity_type(self):
        return self._entity_type

    def _set_entity_type(self, entity_type: base.EntityType):
        if self.global_asset_id is None and self.specific_asset_id is None \
                and entity_type == base.EntityType.SELF_MANAGED_ENTITY:
            raise ValueError("A self-managed entity has to have a globalAssetId or a specificAssetId")
        self._entity_type = entity_type

    entity_type = property(_get_entity_type, _set_entity_type)


class Event(SubmodelElement, metaclass=abc.ABCMeta):
    """
    An event
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)


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
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Constraints that gives additional qualification of a qualifiable element.
                          (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)

        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, category, description, parent, semantic_id, qualifier, kind)
        self.observed: base.AASReference = observed
