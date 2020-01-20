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
The main module of the AAS meta-model. It is used to define the class structures of high level elements such as
AssetAdministrationShell, ConceptDictionary and Asset.

This module contains the following classes from an up-to-down-level:
 - AssetAdministrationShell
 - ConceptDictionary
 - ConceptDescription
 - Asset
 - View
"""

from typing import Optional, Set, Iterable, TYPE_CHECKING

from . import base, security
if TYPE_CHECKING:
    from . import submodel


class View(base.Referable, base.HasSemantics):
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one or more stakeholders.

    todo: what does this exactly?

    :ivar contained_element: Unordered list of references to elements of class Referable
    """
    def __init__(self,
                 id_short: str,
                 contained_element: Optional[Set[base.AASReference]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None):
        """
        Initializer of View

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param contained_element: Unordered list of references to elements of class Referable
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        TODO: Add instruction what to do after construction
        """

        super().__init__()
        self.id_short = id_short
        self.contained_element: Set[base.AASReference] = set() if contained_element is None else contained_element
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id


class Asset(base.Identifiable):
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance. The asset has a globally unique identifier plus
    – if needed – additional domain specific (proprietary) identifiers.

    :ivar kind: Denotes whether the Asset is of kind "Type" or "Instance".
    :ivar asset_identification_model: A reference to a Submodel that defines the handling of additional domain
                                      specific (proprietary) Identifiers for the asset like e.g. serial number etc
    :ivar bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
                            contains a set of entities describing the material used to compose the composite I4.0
                            Component.
    """

    def __init__(self,
                 kind: base.AssetKind,
                 identification: base.Identifier,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 asset_identification_model: Optional[base.AASReference["submodel.Submodel"]] = None,
                 bill_of_material: Optional[base.AASReference["submodel.Submodel"]] = None):
        """
        Initializer of Asset

        :param kind: Denotes whether the Asset is of kind "Type" or "Instance".
        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param asset_identification_model: A reference to a Submodel that defines the handling of additional domain
                                           specific (proprietary) Identifiers for the asset like e.g. serial number etc
        :param bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
                                 contains a set of entities describing the material used to compose the composite I4.0
                                 Component.
        """
        super().__init__()
        self.kind: base.AssetKind = kind
        self.identification: base.Identifier = identification
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.asset_identification_model: Optional[base.AASReference["submodel.Submodel"]] = asset_identification_model
        self.bill_of_material: Optional[base.AASReference["submodel.Submodel"]] = bill_of_material


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
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration


class ConceptDictionary(base.Referable):
    """
    A dictionary containing concept descriptions.

    Typically a concept description dictionary of an AAS contains only concept descriptions of elements used within
    submodels of the AAS.


    :param concept_description: Unordered list of references to elements of class ConceptDescription
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
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.concept_description: Set[base.AASReference[ConceptDescription]] = \
            set() if concept_description is None else concept_description


class AssetAdministrationShell(base.Identifiable, base.Namespace):
    """
    An Asset Administration Shell

    :ivar asset: reference to the asset the AAS is representing.
    :ivar security_: Definition of the security relevant aspects of the AAS.
    :ivar submodel_: Unordered list of submodels to describe typically the asset of an AAS.
    :ivar concept_dictionary: Unordered list of concept dictionaries. The concept dictionaries typically contain only
                              descriptions for elements that are also used within the AAS
    :ivar view: Unordered list of stakeholder specific views that can group the elements of the AAS.
    :ivar derived_from: The reference to the AAS the AAs was derived from
    """
    def __init__(self,
                 asset: base.AASReference[Asset],
                 identification: base.Identifier,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 security_: Optional[security.Security] = None,
                 submodel_: Optional[Set[base.AASReference["submodel.Submodel"]]] = None,
                 concept_dictionary: Iterable[ConceptDictionary] = (),
                 view: Iterable[View] = (),
                 derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = None):
        """
        Initializer of AssetAdministrationShell
        :param asset: reference to the asset the AAS is representing.
        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param security_: Definition of the security relevant aspects of the AAS.
        :param submodel_: Unordered list of submodels to describe typically the asset of an AAS.
        :param concept_dictionary: Unordered list of concept dictionaries. The concept dictionaries typically contain
                                   only descriptions for elements that are also used within the AAS
        :param view: Unordered list of stakeholder specific views that can group the elements of the AAS.
        :param derived_from: The reference to the AAS the AAS was derived from
        """

        super().__init__()
        self.identification: base.Identifier = identification
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = derived_from
        self.security_: Optional[security.Security] = security_
        self.asset: base.AASReference[Asset] = asset
        self.submodel_: Set[base.AASReference["submodel.Submodel"]] = set() if submodel_ is None else submodel_
        self.concept_dictionary: base.NamespaceSet[ConceptDictionary] = base.NamespaceSet(self, concept_dictionary)
        self.view: base.NamespaceSet[View] = base.NamespaceSet(self, view)
