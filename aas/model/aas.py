# Copyright (c) 2020 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
"""
The main module of the AAS meta-model. It is used to define the class structures of high level elements such as
AssetAdministrationShell.

This module contains the following classes from an up-to-down-level:
 - :class:`~.AssetAdministrationShell`
 - :class:`~.AssetInformation`
 - :class:`~.View`
"""

from typing import Optional, Set, Iterable

from . import base
from .security import Security
from .submodel import File, Submodel


class View(base.Referable, base.UniqueIdShortNamespace, base.HasSemantics):
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one or more stakeholders.

    todo: what does this exactly?

    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar contained_element: Unordered list of :class:`AASReferences <aas.model.base.AASReference>` to elements
                             of class :class:`~aas.model.base.Referable`
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
                       (inherited from from :class:`~aas.model.base.HasSemantics`)
    :ivar extension: An extension of the element.
                     (from :class:`~aas.model.base.HasExtensions`)
    """
    def __init__(self,
                 id_short: str,
                 contained_element: Optional[Set[base.AASReference]] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 extension: Iterable[base.Extension] = ()):
        """

        TODO: Add instruction what to do after construction
        """

        super().__init__()
        self.id_short = id_short
        self.contained_element: Set[base.AASReference] = set() if contained_element is None else contained_element
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.extension = base.NamespaceSet(self, [("name", True)], extension)


class AssetInformation:
    """
    In AssetInformation identifying meta data of the asset that is represented by an AAS is defined.

    The asset may either represent an asset type or an asset instance.
    The asset has a globally unique identifier plus – if needed – additional domain specific (proprietary)
    identifiers. However, to support the corner case of very first phase of lifecycle where a stabilised/constant
    global asset identifier does not already exist, the corresponding attribute “globalAssetId” is optional.

    :ivar asset_kind: Denotes whether the Asset is of :class:`~aas.model.base.AssetKind` "TYPE" or "INSTANCE".
                      Default is "INSTANCE".
    :ivar global_asset_id: :class:`~aas.model.base.Reference` to either an Asset object or a global reference to the
                           asset the AAS is representing.
                           This attribute is required as soon as the AAS is exchanged via partners in the
                           life cycle of the asset. In a first phase of the life cycle the asset might not yet have a
                           global id but already an internal identifier. The internal identifier would be modelled via
                           :attr:`~.specificAssetId`.
    :ivar specific_asset_id: Additional domain specific, typically proprietary Identifier (Set of
                             :class:`IdentifierKeyValuePairs <aas.model.base.IdentifierKeyValuePair>` for the asset like
                             e.g. serial number etc.
    :ivar bill_of_material: :class:`~aas.model.base.AASReference` to a :class:`~aas.model.submodel.Submodel`
                            representing the Bill of material of the asset. This :class:`~aas.model.submodel.Submodel`
                            contains a set of entities describing the material used to compose the composite I4.0
                            Component.
    :ivar default_thumbnail: Thumbnail of the asset represented by the asset administration shell. Used as default.
    """

    def __init__(self,
                 asset_kind: base.AssetKind = base.AssetKind.INSTANCE,
                 global_asset_id: Optional[base.Reference] = None,
                 specific_asset_id: Optional[Set[base.IdentifierKeyValuePair]] = None,
                 bill_of_material: Optional[Set[base.AASReference[Submodel]]] = None,
                 default_thumbnail: Optional[File] = None):

        super().__init__()
        self.asset_kind: base.AssetKind = asset_kind
        self._global_asset_id: Optional[base.Reference] = global_asset_id
        self.specific_asset_id: Set[base.IdentifierKeyValuePair] = set() if specific_asset_id is None \
            else specific_asset_id
        self.bill_of_material: Set[base.AASReference[Submodel]] = set() if bill_of_material is None \
            else bill_of_material
        self.default_thumbnail: Optional[File] = default_thumbnail

    def _get_global_asset_id(self):
        return self._global_asset_id

    def _set_global_asset_id(self, global_asset_id: Optional[base.Reference]):
        if global_asset_id is None and (self.specific_asset_id is None or not self.specific_asset_id):
            raise ValueError("either global or specific asset id must be set")
        self._global_asset_id = global_asset_id

    global_asset_id = property(_get_global_asset_id, _set_global_asset_id)

    def __repr__(self) -> str:
        return "AssetInformation(assetKind={}, globalAssetId={}, specificAssetId={}, billOfMaterial={}, " \
               "defaultThumbNail={})".format(self.asset_kind, self._global_asset_id, str(self.specific_asset_id),
                                             str(self.bill_of_material), str(self.default_thumbnail))


class AssetAdministrationShell(base.Identifiable, base.UniqueIdShortNamespace):
    """
    An Asset Administration Shell

    :ivar asset_information: :class:`~.AssetInformation` of the asset this AssetAdministrationShell is representing
    :ivar ~.identification: The globally unique identification (:class:`~aas.model.base.Identifier`) of the element.
                            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar display_name: Can be provided in several languages. (inherited from :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
                    (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar administration: :class:`~aas.model.base.AdministrativeInformation` of an
                          :class:`~.aas.model.base.Identifiable` element. (inherited from
                          :class:`~aas.model.base.Identifiable`)
    :ivar ~.security: Definition of the security relevant aspects of the AAS. (Initialization-parameter: `security_`)
    :ivar ~.submodel: Unordered list of :class:`submodels <aas.model.submodel.Submodel>` to describe typically the asset
                    of an AAS. (Initialization-parameter: `submodel_`)
    :ivar view: Unordered list of stakeholder specific :class:`views <aas.model.aas.View>` that can group the elements
                of the AAS.
    :ivar derived_from: The :class:`reference <aas.model.base.AASReference>` to the AAS the AAs was derived from
    :ivar extension: An extension of the element.
                     (from :class:`~aas.model.base.HasExtensions`)
    """
    def __init__(self,
                 asset_information: AssetInformation,
                 identification: base.Identifier,
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.UniqueIdShortNamespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 security: Optional[Security] = None,
                 submodel: Optional[Set[base.AASReference[Submodel]]] = None,
                 view: Iterable[View] = (),
                 derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = None,
                 extension: Iterable[base.Extension] = ()):
        super().__init__()
        self.identification: base.Identifier = identification
        self.asset_information: AssetInformation = asset_information
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.UniqueIdShortNamespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = derived_from
        self.security: Optional[Security] = security
        self.submodel: Set[base.AASReference[Submodel]] = set() if submodel is None else submodel
        self.view: base.NamespaceSet[View] = base.NamespaceSet(self, [("id_short", True)], view)
        self.extension = base.NamespaceSet(self, [("name", True)], extension)
