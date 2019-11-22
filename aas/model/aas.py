
from typing import List

from . import util, security, submodel


class View:
    """
    If needed stakeholder specific views can be defined on the elements of the AAS

    todo: what does this exactly?

    :param referable_list: List of referables
    """
    def __init__(self, referable_list: List[util.Referable]):
        self.contained_elements: List[util.Referable] = referable_list


class Asset(util.HasDataSpecification, util.Identifiable, util.HasKind):
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance.

    :param asset_identification_model: A reference to a Submodel that defines the handling of additional domain
                                       specific (proprietary) Identifiers for the asset like e.g. serial number etc
    """

    def __init__(self, asset_identification_model: submodel.Submodel):
        super().__init__()
        self.asset_identification_model: submodel.Submodel = asset_identification_model


class ConceptDictionary:
    """
    Contains descriptions for elements that are used within the AAS

    todo: see if there is more info about this

    :param reference:
    """
    def __init__(self, reference: util.Referable):
        self.reference: util.Referable = reference


class AssetAdministrationShell(util.HasDataSpecification, util.Identifiable):
    """
    An Asset Administration Shell

    :param asset_administration_shell_parent: The reference to the AAS the AAs was derived from
    :param security_instance: Definition of the security relevant aspects of the AAS (mandatory)
    :param asset: asset the AAS is representing (mandatory)
    :param submodel_list: The asset of an AAS is typically described by one or more submodels
    :param concept_dictionary: An AAS max have one or more concept dictionaries assigned to it. The concept dictionaries
                               typically contain only descriptions for elements that are also used within the AAS
    :param view_list: If needed stakeholder specific views can be defined on the elements of the AAS
    """
    def __init__(self, asset_administration_shell_parent: "AssetAdministrationShell",
                 security_instance: security.Security,
                 asset: Asset,
                 submodel_list: List[submodel.Submodel],
                 concept_dictionary: ConceptDictionary,
                 view_list: List[View]):

        super().__init__()
        self.derived_from: AssetAdministrationShell = asset_administration_shell_parent
        self.security: security.Security = security_instance
        self.asset: Asset = asset
        self.submodel_list: List[submodel.Submodel] = submodel_list
        self.concept_dictionary: ConceptDictionary = concept_dictionary
        self.view_list: List[View] = view_list
