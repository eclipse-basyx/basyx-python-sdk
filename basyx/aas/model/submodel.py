# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
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

    *Note:* The concept of type and instance applies to submodel elements. :class:`Properties <.Property>` are special
    submodel elements. The property types are defined in dictionaries (like the IEC Common Data Dictionary or eCl\\@ss),
    they do not have a value. The property type (`kind=Type`) is also called data element type in some standards.
    The property instances (`kind=Instance`) typically have a value. A property instance is also called
    property-value pair in certain standards.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__()
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.qualifier = base.NamespaceSet(self, [("type", True)], qualifier)
        self._kind: base.ModelingKind = kind
        self.extension = base.NamespaceSet(self, [("name", True)], extension)


class Submodel(base.Identifiable, base.HasSemantics, base.HasKind, base.Qualifiable, base.UniqueIdShortNamespace):
    """
    A Submodel defines a specific aspect of the asset represented by the AAS.

    A submodel is used to structure the virtual representation and technical functionality of an Administration Shell
    into distinguishable parts. Each submodel refers to a well-defined domain or subject matter. Submodels can become
    standardized and thus become submodel types. Submodels can have different life-cycles.

    :ivar ~.id: The globally unique id of the element.
                            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar submodel_element: Unordered list of :class:`SubmodelElements <.SubmodelElement>`
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
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_: base.Identifier,
                 submodel_element: Iterable[SubmodelElement] = (),
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        super().__init__()
        self.id: base.Identifier = id_
        self.submodel_element = base.NamespaceSet(self, [("id_short", True)], submodel_element)
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.qualifier = base.NamespaceSet(self, [("type", True)], qualifier)
        self._kind: base.ModelingKind = kind
        self.extension = base.NamespaceSet(self, [("name", True)], extension)


ALLOWED_DATA_ELEMENT_CATEGORIES: Set[str] = {
    "CONSTANT",
    "PARAMETER",
    "VARIABLE"
}


class DataElement(SubmodelElement, metaclass=abc.ABCMeta):
    """
    A data element is a :class:`~.SubmodelElement` that is not further composed out of other
    :class:`SubmodelElements <.SubmodelElement>`.
    A data element is a :class:`~.SubmodelElement` that has a value. The type of value differs for different subtypes
    of data elements.

    <<abstract>>

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)

    def _set_category(self, category: Optional[str]):
        if category == "":
            raise base.AASConstraintViolation(100,
                                              "category is not allowed to be an empty string")
        if category is None:
            self._category = None
        else:
            if category not in ALLOWED_DATA_ELEMENT_CATEGORIES:
                if not (isinstance(self, File) or isinstance(self, Blob)):
                    raise base.AASConstraintViolation(
                        90,
                        "DataElement.category must be one of the following: " +
                        ", ".join(ALLOWED_DATA_ELEMENT_CATEGORIES))
            self._category = category


class Property(DataElement):
    """
    A property is a :class:`DataElement` that has a single value.

    *Constraint AASd-007:* if both, the value and the valueId are present then the value needs to be
    identical to the value of the referenced coded value in valueId

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value_type: Data type of the value
    :ivar value: The value of the property instance.
    :ivar value_id: :class:`~aas.model.base.Reference` to the global unique id of a coded value
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value_type: base.DataTypeDefXsd,
                 value: Optional[base.ValueDataType] = None,
                 value_id: Optional[base.Reference] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value_type: base.DataTypeDefXsd = value_type
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
    A multi language property is a :class:`~.DataElement` that has a multi language value.

    *Constraint AASd-012*: if both, the value and the valueId are present then for each string in a
    specific language the meaning must be the same as specified in valueId.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: The value of the property instance.
    :ivar value_id: :class:`~aas.model.base.Reference` to the global unique id of a coded value
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value: Optional[base.LangStringSet] = None,
                 value_id: Optional[base.Reference] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value: base.LangStringSet = dict() if value is None else value
        self.value_id: Optional[base.Reference] = value_id


class Range(DataElement):
    """
    A range is a :class:`~.DataElement` that has a range value.

    *Constraint AASd-013:* In case of a range with `kind=Instance` either the min or the max value or both
    need to be defined

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value_type: Data type of the min and max
    :ivar min: The minimum value of the range. If the min value is missing then the value is assumed to be negative
               infinite
    :ivar max: The maximum of the range. If the max value is missing then the value is assumed to be positive infinite
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value_type: base.DataTypeDefXsd,
                 min: Optional[base.ValueDataType] = None,
                 max: Optional[base.ValueDataType] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value_type: base.DataTypeDefXsd = value_type
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
    A BLOB is a :class:`~.DataElement` that represents a file that is contained with its source code in the value
    attribute.

    *Note:* In contrast to the file property the file content is stored directly as value in the Blob data element.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar content_type: Mime type of the content of the BLOB. The mime type states which file extension the file has.
                     Valid values are e.g. “application/json”, “application/xls”, ”image/jpg”. The allowed values
                     are defined as in RFC2046.
    :ivar value: The value of the BLOB instance of a blob data element.
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 content_type: base.ContentType,
                 value: Optional[base.BlobType] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value: Optional[base.BlobType] = value
        self.content_type: base.ContentType = content_type


class File(DataElement):
    """
    A File is a :class:`~.DataElement` that represents a file via its path description.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar content_type: Mime type of the content of the File.
    :ivar value: Path and name of the referenced file (with file extension). The path can be absolute or relative.
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 content_type: base.ContentType,
                 value: Optional[base.PathType] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value: Optional[base.PathType] = value
        self.content_type: base.ContentType = content_type


class ReferenceElement(DataElement):
    """
    A reference element is a :class:`DataElement` that defines a :class:`~aas.model.base.Reference` to another element
    within the same or another AAS or a :class:`~aas.model.base.Reference` to an external object or entity.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: :class:`~aas.model.base.Reference` to any other :class:`~aas.model.base.Referable` element of the same
                 or any other AAS or a :class:`~aas.model.base.Reference` to an external object or entity.
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value: Optional[base.Reference] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value: Optional[base.Reference] = value


class SubmodelElementCollection(SubmodelElement, metaclass=abc.ABCMeta):
    """
    A submodel element collection is a set or list of :class:`SubmodelElements <.SubmodelElement>`.

    <<abstract>>

    :ivar value: Ordered or unordered list of :class:`SubmodelElements <.SubmodelElement>`
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value: base.NamespaceSet[SubmodelElement] = None  # type: ignore

    @property
    @abc.abstractmethod
    def ordered(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def allow_duplicates(self):
        pass

    @staticmethod
    def create(id_short: str,
               value: Iterable[SubmodelElement] = (),
               display_name: Optional[base.LangStringSet] = None,
               category: Optional[str] = None,
               description: Optional[base.LangStringSet] = None,
               parent: Optional[base.UniqueIdShortNamespace] = None,
               semantic_id: Optional[base.Reference] = None,
               qualifier: Iterable[base.Qualifier] = (),
               kind: base.ModelingKind = base.ModelingKind.INSTANCE,
               extension: Iterable[base.Extension] = (),
               allow_duplicates: bool = False,
               ordered: bool = False):
        """
        A factory to create a SubmodelElementCollection based on the parameter dublicates_allowed and ordered.

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param value: Ordered or unordered list of submodel elements.
        :param display_name: Can be provided in several languages. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the
                         element. It affects the expected existence of attributes and the applicability of
                         constraints. (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference
                            a referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable
                          element. (from base.Qualifiable)
        :param kind: Kind of the element: either type or instance. Default = Instance. (from base.HasKind)
        :param extension: An extension of the element. (from base.HasExtension)
        :param ordered: If ordered=false then the elements in the property collection are not ordered. If
                        ordered=true then the elements in the collection are ordered.
        :param allow_duplicates: If allowDuplicates=true, then it is allowed that the collection contains several
                                 elements with the same semantics (i.e. the same semanticId).
                                 If allowDuplicates=false, then it is not allowed that the collection contains
                                 several elements with the same semantics (i.e. the same semanticId).
        """
        if ordered:
            if allow_duplicates:
                return SubmodelElementCollectionOrdered(id_short, value, display_name, category, description, parent,
                                                        semantic_id, qualifier, kind, extension)
            else:
                return SubmodelElementCollectionOrderedUniqueSemanticId(id_short, value, display_name, category,
                                                                        description, parent, semantic_id, qualifier,
                                                                        kind, extension)
        else:
            if allow_duplicates:
                return SubmodelElementCollectionUnordered(id_short, value, display_name, category, description, parent,
                                                          semantic_id, qualifier, kind, extension)
            else:
                return SubmodelElementCollectionUnorderedUniqueSemanticId(id_short, value, display_name, category,
                                                                          description, parent, semantic_id, qualifier,
                                                                          kind, extension)


class SubmodelElementCollectionOrdered(SubmodelElementCollection, base.UniqueIdShortNamespace):
    """
    A SubmodelElementCollectionOrdered is an ordered list of :class:`SubmodelElements <.SubmodelElement>`

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: Ordered or unordered list of :class:`SubmodelElements <.SubmodelElement>`
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind,
                         extension)
        self.value = base.OrderedNamespaceSet(self, [("id_short", False)], value)

    @property
    def ordered(self) -> bool:
        return True

    @property
    def allow_duplicates(self):
        return True


class SubmodelElementCollectionOrderedUniqueSemanticId(SubmodelElementCollectionOrdered,
                                                       base.UniqueSemanticIdNamespace):
    """
    A SubmodelElementCollectionOrderedUniqueSemanticId is an ordered list of submodel elements where id_shorts and
    semantic_ids are unique.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: Ordered or unordered list of :class:`SubmodelElements <.SubmodelElement>`
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, (), display_name, category, description, parent, semantic_id, qualifier, kind,
                         extension)
        # super().__init__() adds an unused NamespaceSet
        self.namespace_element_sets.pop()
        self.value = base.OrderedNamespaceSet(self, [("id_short", False), ("semantic_id", True)], value)

    @property
    def allow_duplicates(self):
        return False


class SubmodelElementCollectionUnordered(SubmodelElementCollection, base.UniqueIdShortNamespace):
    """
    A SubmodelElementCollectionOrdered is an unordered list of submodel elements where id_shorts are unique.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: Ordered or unordered list of :class:`SubmodelElements <.SubmodelElement>`
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.value = base.NamespaceSet(self, [("id_short", False)], value)

    @property
    def ordered(self) -> bool:
        return False

    @property
    def allow_duplicates(self):
        return True


class SubmodelElementCollectionUnorderedUniqueSemanticId(SubmodelElementCollectionUnordered,
                                                         base.UniqueSemanticIdNamespace):
    """
    A SubmodelElementCollectionOrdered is an unordered list of submodel elements where where id_shorts and
    semanticIds are unique.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar value: Ordered or unordered list of :class:`SubmodelElements <.SubmodelElement>`
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 value: Iterable[SubmodelElement] = (),
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, (), display_name, category, description, parent, semantic_id, qualifier, kind,
                         extension)
        # super().__init__() adds an unused NamespaceSet
        self.namespace_element_sets.pop()
        self.value = base.NamespaceSet(self, [("id_short", False), ("semantic_id", True)], value)

    @property
    def allow_duplicates(self):
        return False


class RelationshipElement(SubmodelElement):
    """
    A relationship element is used to define a relationship between two :class:`~aas.model.base.Referable` elements.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar first: Reference to the first element in the relationship taking the role of the subject which have to
                 be of class Referable. (inherited from :class:`~.RelationshipElement`)
    :ivar second: Reference to the second element in the relationship taking the role of the object which have to
                  be of class Referable. (inherited from :class:`~.RelationshipElement`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 first: base.Reference,
                 second: base.Reference,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.first: base.Reference = first
        self.second: base.Reference = second


class AnnotatedRelationshipElement(RelationshipElement, base.UniqueIdShortNamespace):
    """
    An annotated relationship element is a :class:`~.RelationshipElement` that can be annotated
    with additional :class:`DataElements <.DataElement>`.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar first: Reference to the first element in the relationship taking the role of the subject which have to
                 be of class Referable. (inherited from :class:`~.RelationshipElement`)
    :ivar second: Reference to the second element in the relationship taking the role of the object which have to
                  be of class Referable. (inherited from :class:`~.RelationshipElement`)
    :ivar annotation: Unordered list of :class:`DataElements <.DataElement>` that hold for the relationship between two
                      elements
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 first: base.Reference,
                 second: base.Reference,
                 display_name: Optional[base.LangStringSet] = None,
                 annotation: Iterable[DataElement] = (),
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, first, second, display_name, category, description, parent, semantic_id, qualifier,
                         kind, extension)
        self.annotation = base.NamespaceSet(self, [("id_short", True)], annotation)


class OperationVariable:
    """
    An operation variable is part of an operation that is used to define an input or output variable of that operation.

    *Constraint AASd-008:* The submodel element value of an operation variable shall be of kind=Template.

    :ivar value: Describes the needed argument for an operation via a :class:`~.SubmodelElement` of `kind=TYPE`.
    """

    def __init__(self,
                 value: SubmodelElement):
        """
        TODO: Add instruction what to do after construction
        """
        # Constraint AASd-008: The submodel element shall be of kind=Template.
        self._value: SubmodelElement
        self.value = value

    def _get_value(self):
        return self._value

    def _set_value(self, value: SubmodelElement) -> None:
        if value.kind is not base.ModelingKind.TEMPLATE:
            raise base.AASConstraintViolation(
                8,
                "The SubmodelElement `OperationVariable.value` must have the attribute `kind==ModelingType.TEMPLATE`"
            )
        self._value = value

    value = property(_get_value, _set_value)


class Operation(SubmodelElement):
    """
    An operation is a :class:`~.SubmodelElement` with input and output variables.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar input_variable: List of input parameters (:class:`OperationVariables <.OperationVariable>`) of the operation
    :ivar output_variable: List of output parameters (:class:`OperationVariables <.OperationVariable>`) of the operation
    :ivar in_output_variable: List of parameters (:class:`OperationVariables <.OperationVariable>`) that are input and
                              output of the operation
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    def __init__(self,
                 id_short: str,
                 input_variable: Optional[List[OperationVariable]] = None,
                 output_variable:  Optional[List[OperationVariable]] = None,
                 in_output_variable:  Optional[List[OperationVariable]] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.input_variable = input_variable if input_variable is not None else []
        self.output_variable = output_variable if output_variable is not None else []
        self.in_output_variable = in_output_variable if in_output_variable is not None else []


class Capability(SubmodelElement):
    """
    A capability is the implementation-independent description of the potential of an asset to achieve a certain effect
    in the physical or virtual world

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
                    (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)


class Entity(SubmodelElement, base.UniqueIdShortNamespace):
    """
    An entity is a :class:`~.SubmodelElement` that is used to model entities

    *Constraint AASd-014:* global_asset_id or specific_asset_id must be set if :attr:`~.entity_type` is set to
    :attr:`~.EntityType.SELF_MANAGED_ENTITY`. They must be empty otherwise.

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar entity_type: Describes whether the entity is a co-managed or a self-managed entity.
    :ivar statement: Unordered list of statements (:class:`SubmodelElements <.SubmodelElement>`) applicable to the
                     entity, typically with a qualified value.
    :ivar global_asset_id: :class:`~aas.model.base.Reference` to the asset the AAS is
                           representing. This attribute is required as soon as the AAS is exchanged via partners
                           in the life cycle of the asset. In a first phase of the life cycle the asset might not
                           yet have a global id but already an internal identifier. The internal identifier would
                           be modelled via “specificAssetId”.
    :ivar specific_asset_id: :class:`~aas.model.base.Reference` to an identifier key value pair representing a specific
                             identifier
                             of the asset represented by the asset administration shell. See Constraint AASd-014
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 entity_type: base.EntityType,
                 statement: Iterable[SubmodelElement] = (),
                 global_asset_id: Optional[base.GlobalReference] = None,
                 specific_asset_id: Optional[base.SpecificAssetId] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.statement = base.NamespaceSet(self, [("id_short", True)], statement)
        self.specific_asset_id: Optional[base.SpecificAssetId] = specific_asset_id
        self.global_asset_id: Optional[base.GlobalReference] = global_asset_id
        self._entity_type: base.EntityType
        self.entity_type = entity_type

    def _get_entity_type(self) -> base.EntityType:
        return self._entity_type

    def _set_entity_type(self, entity_type: base.EntityType) -> None:
        if self.global_asset_id is None and self.specific_asset_id is None \
                and entity_type == base.EntityType.SELF_MANAGED_ENTITY:
            raise base.AASConstraintViolation(
                14,
                "A self-managed entity has to have a globalAssetId or a specificAssetId"
            )
        if (self.global_asset_id or self.specific_asset_id) and entity_type == base.EntityType.CO_MANAGED_ENTITY:
            raise base.AASConstraintViolation(
                14,
                "A co-managed entity has to have neither a globalAssetId nor a specificAssetId")
        self._entity_type = entity_type

    entity_type = property(_get_entity_type, _set_entity_type)


class EventElement(SubmodelElement, metaclass=abc.ABCMeta):
    """
    An event
    <<abstract>>

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """
    @abc.abstractmethod
    def __init__(self,
                 id_short: str,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)


class BasicEventElement(EventElement):
    """
    An event

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar observed: :class:`~aas.model.base.ModelReference` to the data or other elements that are being observed
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                       element. The semantic id may either reference an external global id or it may reference a
                       referable model element of kind=Type that defines the semantics of the element.
                       (inherited from :class:`~aas.model.base.HasSemantics`)
    :ivar qualifier: Unordered list of Qualifiers that gives additional qualification of a qualifiable element.
                     (from :class:`~aas.model.base.Qualifiable`)
    :ivar kind: Kind of the element: Either `TYPE` or `INSTANCE`. Default is `INSTANCE`. (inherited from
                :class:`aas.model.base.HasKind`)
    :ivar extension: An extension of the element. (inherited from
                     :class:`aas.model.base.HasExtension`)
    """

    def __init__(self,
                 id_short: str,
                 observed: base.ModelReference,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 qualifier: Iterable[base.Qualifier] = (),
                 kind: base.ModelingKind = base.ModelingKind.INSTANCE,
                 extension: Iterable[base.Extension] = ()):
        """
        TODO: Add instruction what to do after construction
        """

        super().__init__(id_short, display_name, category, description, parent, semantic_id, qualifier, kind, extension)
        self.observed: base.ModelReference = observed
