# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime

from typing import List, Dict, Optional,Iterable, Set

from . import base, _string_constraints, aas
from . import descriptor
from .submodel_descriptor import SubmodelDescriptor
import re

class AssetAdministrationShellDescriptor(descriptor.Descriptor):

    def __init__(self,
                 id_: base.Identifier,
                 administration: Optional[base.AdministrativeInformation] = None,
                 asset_kind: Optional[base.AssetKind] = None,
                 asset_type: Optional[base.Identifier] = None,
                 endpoints: Optional[List[descriptor.Endpoint]] = None,
                 global_asset_id: Optional[base.Identifier] = None,
                 id_short: Optional[base.NameType] = None,
                 specific_asset_id: Iterable[base.SpecificAssetId] = (),
                 submodel_descriptors: Optional[List[SubmodelDescriptor]] = None,
                 description: Optional[base.MultiLanguageTextType] = None,
                 display_name: Optional[base.MultiLanguageNameType] = None,
                 extension: Iterable[base.Extension] = ()):
        """AssetAdministrationShellDescriptor -

        Nur das 'id'-Feld (id_) ist zwingend erforderlich. Alle anderen Felder erhalten Defaultwerte.
        """
        super().__init__()
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.asset_kind: Optional[base.AssetKind] = asset_kind
        self.asset_type: Optional[base.Identifier] = asset_type
        self.endpoints: Optional[List[descriptor.Endpoint]] = endpoints if endpoints is not None else []  # leere Liste, falls nicht gesetzt
        self.global_asset_id: Optional[base.Identifier] = global_asset_id
        self.id_short: Optional[base.NameType] = id_short
        self.id: base.Identifier = id_
        self._specific_asset_id: base.ConstrainedList[base.SpecificAssetId] = base.ConstrainedList(
            specific_asset_id,
            item_set_hook=self._check_constraint_set_spec_asset_id,
            item_del_hook=self._check_constraint_del_spec_asset_id
        )
        self.submodel_descriptors = submodel_descriptors if submodel_descriptors is not None else []
        self.description: Optional[base.MultiLanguageTextType] = description
        self.display_name: Optional[base.MultiLanguageNameType] = display_name
        self.extension = base.NamespaceSet(self, [("name", True)], extension)

    @property
    def specific_asset_id(self) -> base.ConstrainedList[base.SpecificAssetId]:
        return self._specific_asset_id

    @specific_asset_id.setter
    def specific_asset_id(self, specific_asset_id: Iterable[base.SpecificAssetId]) -> None:
        # constraints are checked via _check_constraint_set_spec_asset_id() in this case
        self._specific_asset_id[:] = specific_asset_id

    def _check_constraint_set_spec_asset_id(self, items_to_replace: List[base.SpecificAssetId],
                                            new_items: List[base.SpecificAssetId],
                                            old_list: List[base.SpecificAssetId]) -> None:
        self._validate_aasd_131(self.global_asset_id,
                                len(old_list) - len(items_to_replace) + len(new_items) > 0)

    def _check_constraint_del_spec_asset_id(self, _item_to_del: base.SpecificAssetId,
                                            old_list: List[base.SpecificAssetId]) -> None:
        self._validate_aasd_131(self.global_asset_id, len(old_list) > 1)
