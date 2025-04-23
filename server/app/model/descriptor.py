from __future__ import absolute_import

import abc
from typing import Optional, Iterable, List

from basyx.aas import model
from server.app.model.endpoint import Endpoint


class Descriptor(model.HasExtension, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, description: Optional[model.MultiLanguageTextType] = None,
                 display_name: Optional[model.MultiLanguageNameType] = None, extension: Iterable[model.Extension] = ()):
        super().__init__()
        self.description: Optional[model.MultiLanguageTextType] = description
        self.display_name: Optional[model.MultiLanguageNameType] = display_name
        self.extension = model.NamespaceSet(self, [("name", True)], extension)

    def commit(self):
        pass

    def update(self):
        pass

    def update_from(self, other: "Descriptor", update_source: bool = False):
        """
        Updates the descriptor's attributes from another descriptor.

        :param other: The descriptor to update from.
        :param update_source: Placeholder for compatibility; not used in this context.
        """
        for attr in vars(other):
            if attr == "id":
                continue  # Skip updating the unique identifier of the AAS
            setattr(self, attr, getattr(other, attr))


class SubmodelDescriptor(Descriptor):

    def __init__(self, id_: model.Identifier, endpoints: List[Endpoint],
                 administration: Optional[model.AdministrativeInformation] = None,
                 id_short: Optional[model.NameType] = None, semantic_id: Optional[model.Reference] = None,
                 supplemental_semantic_id: Iterable[model.Reference] = ()):
        super().__init__()
        self.id: model.Identifier = id_
        self.endpoints: List[Endpoint] = endpoints
        self.administration: Optional[model.AdministrativeInformation] = administration
        self.id_short: Optional[model.NameType] = id_short
        self.semantic_id: Optional[model.Reference] = semantic_id
        self.supplemental_semantic_id: model.ConstrainedList[model.Reference] = \
            model.ConstrainedList(supplemental_semantic_id)


class AssetAdministrationShellDescriptor(Descriptor):

    def __init__(self,
                 id_: model.Identifier,
                 administration: Optional[model.AdministrativeInformation] = None,
                 asset_kind: Optional[model.AssetKind] = None,
                 asset_type: Optional[model.Identifier] = None,
                 endpoints: Optional[List[Endpoint]] = None,
                 global_asset_id: Optional[model.Identifier] = None,
                 id_short: Optional[model.NameType] = None,
                 specific_asset_id: Iterable[model.SpecificAssetId] = (),
                 submodel_descriptors: Optional[List[SubmodelDescriptor]] = None,
                 description: Optional[model.MultiLanguageTextType] = None,
                 display_name: Optional[model.MultiLanguageNameType] = None,
                 extension: Iterable[model.Extension] = ()):
        """AssetAdministrationShellDescriptor -

        Nur das 'id'-Feld (id_) ist zwingend erforderlich. Alle anderen Felder erhalten Defaultwerte.
        """
        super().__init__()
        self.administration: Optional[model.AdministrativeInformation] = administration
        self.asset_kind: Optional[model.AssetKind] = asset_kind
        self.asset_type: Optional[model.Identifier] = asset_type
        self.endpoints: Optional[
            List[Endpoint]] = endpoints if endpoints is not None else []  # leere Liste, falls nicht gesetzt
        self.global_asset_id: Optional[model.Identifier] = global_asset_id
        self.id_short: Optional[model.NameType] = id_short
        self.id: model.Identifier = id_
        self._specific_asset_id: model.ConstrainedList[model.SpecificAssetId] = model.ConstrainedList(
            specific_asset_id,
            item_set_hook=self._check_constraint_set_spec_asset_id,
            item_del_hook=self._check_constraint_del_spec_asset_id
        )
        self.submodel_descriptors = submodel_descriptors if submodel_descriptors is not None else []
        self.description: Optional[model.MultiLanguageTextType] = description
        self.display_name: Optional[model.MultiLanguageNameType] = display_name
        self.extension = model.NamespaceSet(self, [("name", True)], extension)

    @property
    def specific_asset_id(self) -> model.ConstrainedList[model.SpecificAssetId]:
        return self._specific_asset_id

    @specific_asset_id.setter
    def specific_asset_id(self, specific_asset_id: Iterable[model.SpecificAssetId]) -> None:
        # constraints are checked via _check_constraint_set_spec_asset_id() in this case
        self._specific_asset_id[:] = specific_asset_id

    def _check_constraint_set_spec_asset_id(self, items_to_replace: List[model.SpecificAssetId],
                                            new_items: List[model.SpecificAssetId],
                                            old_list: List[model.SpecificAssetId]) -> None:
        model.AssetInformation._validate_aasd_131(self.global_asset_id,
                                            len(old_list) - len(items_to_replace) + len(new_items) > 0)

    def _check_constraint_del_spec_asset_id(self, _item_to_del: model.SpecificAssetId,
                                            old_list: List[model.SpecificAssetId]) -> None:
        model.AssetInformation._validate_aasd_131(self.global_asset_id, len(old_list) > 1)
