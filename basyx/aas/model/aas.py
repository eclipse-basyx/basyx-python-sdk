# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
The main module of the AAS meta-model. It is used to define the class structures of high level elements such as
:class:`~.AssetAdministrationShell` and :class:`~.Asset`.

This module contains the following classes from an up-to-down-level:

 - :class:`~.AssetAdministrationShell`
 - :class:`~.Asset`
 - :class:`~.View`
"""

from typing import Optional, Set, Iterable, TYPE_CHECKING

from . import base, concept
from .security import Security
from .submodel import Submodel


class View(base.Referable, base.HasSemantics):
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one or more stakeholders.

    todo: what does this exactly?

    :ivar id_short: Identifying string of the element within its name space.
        (inherited from :class:`~aas.model.base.Referable`)
    :ivar contained_element: Unordered list of :class:`References <aas.model.base.Reference>` to elements of class
        :class:`~aas.model.base.Referable`
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar semantic_id: :class:`~aas.model.base.Identifier` of the semantic definition of the element. It is called
        semantic id of the element. The semantic id may either reference an external global id or it may reference a
        :class:`~aas.model.base.Referable` model element of kind=Type that defines the semantics of the element.
        (inherited from :class:`~aas.model.base.HasSemantics`)
    """
    def __init__(self,
                 id_short: str,
                 contained_element: Optional[Set[base.AASReference]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None):
        """
        TODO: Add instruction what to do after construction
        """
        super().__init__()
        self.id_short = id_short
        self.contained_element: Set[base.AASReference] = set() if contained_element is None else contained_element
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id


class Asset(base.Identifiable):
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance. The asset has a globally unique
    :class:`~aas.model.base.Identifier` plus – if needed – additional domain specific (proprietary) identifiers.

    :ivar kind: Denotes whether the Asset is of kind "Type" or "Instance".
    :ivar ~.identification: The globally unique identification of the element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar id_short: Identifying string of the element within its name space.
        (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an :class:`~aas.model.base.Identifiable` element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar asset_identification_model: A :class:`~aas.model.base.AASReference` to a :class:`~aas.model.submodel.Submodel`
                                      that defines the handling of additional domain
                                      specific (proprietary) Identifiers for the asset like e.g. serial number etc
    :ivar bill_of_material: Bill of material of the asset represented by a :class:`~aas.model.submodel.Submodel` of the
                            same AAS. This submodel
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
                 asset_identification_model: Optional[base.AASReference[Submodel]] = None,
                 bill_of_material: Optional[base.AASReference[Submodel]] = None):
        super().__init__()
        self.kind: base.AssetKind = kind
        self.identification: base.Identifier = identification
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.asset_identification_model: Optional[base.AASReference[Submodel]] = asset_identification_model
        self.bill_of_material: Optional[base.AASReference[Submodel]] = bill_of_material


class AssetAdministrationShell(base.Identifiable, base.Namespace):
    """
    An Asset Administration Shell

    :ivar asset: :class:`~aas.model.base.Reference` to the :class:`~.Asset` the AAS is representing.
    :ivar ~.identification: The globally unique identification of the element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar id_short: Identifying string of the element within its name space.
        (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                     It affects the expected existence of attributes and the applicability of constraints.
                     (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: :class:`~aas.model.base.Reference` to the next :class:`~aas.model.base.Referable` parent element of
        the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar administration: Administrative information of an :class:`~aas.model.base.Identifiable` element.
        (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar ~.security: Definition of the security relevant aspects of the AAS.
    :ivar ~.submodel: Unordered list of :class:`AASReferences <aas.model.base.AASReference>` to
        :class:`Submodels <aas.model.submodel.Submodel>` to describe typically the asset of an AAS.
    :ivar concept_dictionary: Unordered list of :class:`ConceptDictionaries <aas.model.concept.ConceptDictionary>`.
                              The concept dictionaries typically contain only
                              descriptions for elements that are also used within the AAS
    :ivar view: Unordered list of stakeholder specific :class:`Views <~.View>` that can group the elements of the AAS.
    :ivar derived_from: The :class:`~aas.model.base.AASReference` to the AAS the AAs was derived from
    """
    def __init__(self,
                 asset: base.AASReference[Asset],
                 identification: base.Identifier,
                 id_short: str = "",
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 security: Optional[Security] = None,
                 submodel: Optional[Set[base.AASReference[Submodel]]] = None,
                 concept_dictionary: Iterable[concept.ConceptDictionary] = (),
                 view: Iterable[View] = (),
                 derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = None):
        super().__init__()
        self.identification: base.Identifier = identification
        self.id_short = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.derived_from: Optional[base.AASReference[AssetAdministrationShell]] = derived_from
        self.security: Optional[Security] = security
        self.asset: base.AASReference[Asset] = asset
        self.submodel: Set[base.AASReference[Submodel]] = set() if submodel is None else submodel
        self.concept_dictionary: base.NamespaceSet[concept.ConceptDictionary] = \
            base.NamespaceSet(self, concept_dictionary)
        self.view: base.NamespaceSet[View] = base.NamespaceSet(self, view)
