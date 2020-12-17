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
The main module of the AAS meta-model. It is used to define the class structures of high level elements such as
AssetAdministrationShell and Asset.

This module contains the following classes from an up-to-down-level:
 - AssetAdministrationShell
 - Asset
 - View
"""

from typing import Optional, Set, Iterable

from . import base, concept
from .security import Security
from .submodel import File, Submodel


class View(base.Referable, base.HasSemantics):
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one or more stakeholders.

    todo: what does this exactly?

    :ivar contained_element: Unordered list of :class:`references <aas.model.base.AASReference>` to elements
                             of class :class:`~aas.model.base.Referable`
    """
    def __init__(self,
                 id_short: str,
                 contained_element: Optional[Set[base.AASReference]] = None,
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 semantic_id: Optional[base.Reference] = None,
                 extension: Optional[Set[base.Extension]] = None):
        """
        Initializer of View

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param contained_element: Unordered list of references to elements of class Referable
        :param display_name: Can be provided in several languages. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param semantic_id: Identifier of the semantic definition of the element. It is called semantic id of the
                            element. The semantic id may either reference an external global id or it may reference a
                            referable model element of kind=Type that defines the semantics of the element.
                            (from base.HasSemantics)
        :param extension: Element that can be extended by proprietary extensions. (from base.HasExtension)
        TODO: Add instruction what to do after construction
        """

        super().__init__()
        self.id_short = id_short
        self.contained_element: Set[base.AASReference] = set() if contained_element is None else contained_element
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.extension: Set[base.Extension] = set() if extension is None else extension


class Asset(base.Identifiable):
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance. The asset has a globally unique identifier plus
    – if needed – additional domain specific (proprietary) identifiers.    
    :ivar ~.identification: The globally unique identification (:class:`~aas.model.base.Identifier`) of the element.
                            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
    :ivar category: The category is a value that gives further meta information w.r.t. to the class of the element.
                    It affects the expected existence of attributes and the applicability of constraints.
                    (inherited from :class:`~aas.model.base.Referable`)
    :ivar description: Description or comments on the element. (inherited from :class:`~aas.model.base.Referable`)
    :ivar parent: Reference to the next referable parent element of the element. (inherited from
                  :class:`~aas.model.base.Referable`)
    :ivar administration: :class:`~aas.model.base.AdministrativeInformation` of an
                          :class:`~.aas.model.base.Identifiable` element. (inherited from
                          :class:`~aas.model.base.Identifiable`)
    :ivar asset_identification_model: An :class:`~aas.model.base.AASReference` to a
                                      :class:`~aas.model.submodel.Submodel` that defines the handling of additional
                                      domain specific (proprietary) Identifiers for the asset like e.g.
                                      serial number etc
    :ivar bill_of_material: Bill of material of the asset represented by a :class:`~aas.model.submodel.Submodel` of the
                            same AAS. This submodel contains a set of entities describing the material used to compose
                            the composite I4.0 Component.
    """

    def __init__(self,

                 identification: base.Identifier,
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 extension: Optional[Set[base.Extension]] = None):
        """
        Initializer of Asset

        :param kind: Denotes whether the Asset is of kind "Type" or "Instance".
        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param display_name: Can be provided in several languages. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param extension: Element that can be extended by proprietary extensions. (from base.HasExtension)
        """
        super().__init__()
        self.kind: base.AssetKind = kind
        self.identification: base.Identifier = identification
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.extension: Set[base.Extension] = set() if extension is None else extension


class AssetInformation():
    """
    In AssetInformation identifying meta data of the asset that is represented by an AAS is defined.

    The asset may either represent an asset type or an asset instance.
    The asset has a globally unique identifier plus – if needed – additional domain specific (proprietary)
    identifiers. However, to support the corner case of very first phase of lifecycle where a stabilised/constant
    global asset identifier does not already exist, the corresponding attribute “globalAssetId” is optional.

    :ivar asset_kind Denotes whether the Asset is of kind "Type" or "Instance".
    :ivar global_asset_id: Reference to either an Asset object or a global reference to the asset the AAS is
                           representing. This attribute is required as soon as the AAS is exchanged via partners in the
                           life cycle of the asset. In a first phase of the life cycle the asset might not yet have a
                           global id but already an internal identifier. The internal identifier would be modelled via
                           “specificAssetId”.
    :ivar specific_asset_id: Additional domain specific specific, typically proprietary Identifier for the asset like
                             e.g. serial number etc.
    :ivar bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
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
        """
        Initializer of Asset

        :param asset_kind: Denotes whether the Asset is of kind "Type" or "Instance".
        :param global_asset_id: Reference to either an Asset object or a global reference to the asset the AAS is
                                representing. This attribute is required as soon as the AAS is exchanged via partners
                                in the life cycle of the asset. In a first phase of the life cycle the asset might not
                                yet have a global id but already an internal identifier. The internal identifier would
                                be modelled via “specificAssetId”.
        :param specific_asset_id: Additional domain specific specific, typically proprietary Identifier for the asset
                                  like e.g. serial number etc.
        :param bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
                                 contains a set of entities describing the material used to compose the composite I4.0
                                 Component.
        :param default_thumbnail: Thumbnail of the asset represented by the asset administration shell. Used as default.
        """
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


class AssetAdministrationShell(base.Identifiable, base.Namespace):
    """
    An Asset Administration Shell

    :ivar asset: :class:`Reference <aas.model.base.AASReference>` to the :class:`~aas.model.aas.Asset` the AAS is
                 representing.
    :ivar ~.identification: The globally unique identification (:class:`~aas.model.base.Identifier`) of the element.
                            (inherited from :class:`~aas.model.base.Identifiable`)
    :ivar id_short: Identifying string of the element within its name space. (inherited from
                    :class:`~aas.model.base.Referable`)
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
    :ivar concept_dictionary: Unordered list of :class:`ConceptDictionaries <aas.model.concept.ConceptDictionary>`.
                              The concept dictionaries typically contain only descriptions for elements that are also
                              used within the AAS
    :ivar view: Unordered list of stakeholder specific :class:`views <aas.model.aas.View>` that can group the elements
                of the AAS.
    :ivar derived_from: The :class:`reference <aas.model.base.AASReference>` to the AAS the AAs was derived from
    """
    def __init__(self,
                 asset_information: AssetInformation,
                 identification: base.Identifier,
                 id_short: str = "NotSet",
                 display_name: Optional[base.LangStringSet] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None,
                 administration: Optional[base.AdministrativeInformation] = None,
                 security: Optional[Security] = None,
                 submodel: Optional[Set[base.AASReference[Submodel]]] = None,
                 view: Iterable[View] = (),
                 derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = None,
                 extension: Optional[Set[base.Extension]] = None):
        """
        Initializer of AssetAdministrationShell
        :param asset_information: Meta information about the asset the AAS is representing.
        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param display_name: Can be provided in several languages. (from base.Referable)
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints.
                         (from base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        :param security: Definition of the security relevant aspects of the AAS.
        :param submodel: Unordered list of submodels to describe typically the asset of an AAS.
        :param concept_dictionary: Unordered list of concept dictionaries. The concept dictionaries typically contain
                                   only descriptions for elements that are also used within the AAS
        :param view: Unordered list of stakeholder specific views that can group the elements of the AAS.
        :param derived_from: The reference to the AAS the AAS was derived from
        :param extension: Element that can be extended by proprietary extensions. (from base.HasExtension)
        """

        super().__init__()
        self.identification: base.Identifier = identification
        self.asset_information: AssetInformation = asset_information
        self.id_short = id_short
        self.display_name: Optional[base.LangStringSet] = dict() if display_name is None else display_name
        self.category = category
        self.description: Optional[base.LangStringSet] = dict() if description is None else description
        self.parent: Optional[base.Namespace] = parent
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.derived_from: Optional[base.AASReference["AssetAdministrationShell"]] = derived_from
        self.security: Optional[Security] = security
        self.submodel: Set[base.AASReference[Submodel]] = set() if submodel is None else submodel
        self.view: base.NamespaceSet[View] = base.NamespaceSet(self, view)
        self.extension: Set[base.Extension] = set() if extension is None else extension
