
from typing import List

from . import util
from . import security
# from .import submodel


# todo: Add Inheritances
# todo: Change security.Submodel to submodel.Submodel as soon as exists


class View:
    """
    If needed stakeholder specific views can be defined on the elements of the AAS

    todo: what does this exactly?

    :param referable_list: List of referables
    """
    def __init__(self, referable_list: List[util.Referable]):
        self.contained_elements: List[util.Referable] = referable_list


class Asset:
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance.
    todo: identifier

    :param submodel:
    :param kind: Kind (Type, Instance)
    """
    def __init__(self, submodel: security.Submodel,
                 kind: util.HasKind):
        self.asset_identification_model: security.Submodel = submodel
        self.kind: util.HasKind = kind


class ConceptDictionary:
    """
    Contains descriptions for elements that are used within the AAS

    todo: see if there is more info about this

    :param reference:
    """
    def __init__(self, reference: util.Referable):
        self.reference: util.Referable = reference


class AssetAdministrationShell:
    """
    An Asset Administration Shell

    :param security_instance: Definition of the security relevant aspects of the AAS (mandatory)
    :param asset_administration_shell_parent: The reference to the AAS this AAS was derived from (can be empty)
    :param asset: asset the AAS is representing (mandatory)
    :param view_list: containing a list of referable items (can be empty)
    """
    def __init__(self, asset_administration_shell_parent: "AssetAdministrationShell",
                 security_instance: security.Security,
                 asset: Asset,
                 submodel: security.Submodel,
                 concept_dictionary: ConceptDictionary,
                 view_list: List[View]):
        self.derived_from: AssetAdministrationShell = asset_administration_shell_parent
        self.security: security.Security = security_instance
        self.asset: Asset = asset
        self.submodel: security.Submodel = submodel
        self.concept_dictionary: ConceptDictionary = concept_dictionary
        self.view_list: List[View] = view_list
