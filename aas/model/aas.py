
from typing import List, Optional

from . import util, security, submodel


class View:
    """
    If needed stakeholder specific views can be defined on the elements of the AAS

    todo: what does this exactly?

    :param contained_elements: List of references to elements of class Referable
    """
    def __init__(self, contained_elements: List[util.Reference] = []):
        self.contained_elements: List[util.Reference] = contained_elements


class Asset(util.HasDataSpecification, util.Identifiable):
    """
    An Asset describes meta data of an asset that is represented by an AAS

    The asset may either represent an asset type or an asset instance.

    :param kind: Denotes whether the Asset is of kind "Type" or "Instance".
    :param asset_identification_model: A reference to a Submodel that defines the handling of additional domain
                                       specific (proprietary) Identifiers for the asset like e.g. serial number etc
    :param bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
                             contains a set of entities describing the material used to compose the composite I4.0
                             Component.
    """

    def __init__(self, kind: util.AssetKind, asset_identification_model: Optional[util.Reference], bill_of_material: Optional[util.Reference]):
        super().__init__()
        self.kind: util.AssetKind = kind
        self.asset_identification_model: Optional[util.Reference] = asset_identification_model
        self.bill_of_material: Optional[util.Reference] = bill_of_material


class ConceptDescription(util.HasDataSpecification, util. Identifiable):
    """
    TODO
    """

    def __init__(self, identification: util.Identifier, is_case_of: List[util.Reference] = [],  has_data_specification: List[util.Reference] = [],
                 administration: Optional[util.AdministrativeInformation] = None):
        self.is_case_of: List[util.Reference] = is_case_of
        self.identification: util.Identifier = identification
        self.has_data_specification: List[util.Reference] = has_data_specification
        self.administration: Optional[util.AdministrativeInformation] = administration



class ConceptDictionary(util.Referable):
    """
    Contains descriptions for elements that are used within the AAS

    todo: see if there is more info about this

    :param concept_descriptions: List of references to elements of class ConceptDescription
    """
    def __init__(self, id_short: str, concept_descriptions: List[util.Reference] = [], category: Optional[str] = None,
                 description: Optional[util.LangStringSet] = None, parent: Optional[util.Reference] = None):
        super().__init__()
        self.concept_descriptions: List[util.Reference] = concept_descriptions
        self.id_short: str = id_short
        self.category: Optional[str] = category
        self.description: Optional[util.LangStringSet] = description
        self.parent: Optional[util.Reference] = parent


class AssetAdministrationShell(util.HasDataSpecification, util.Identifiable):
    """
    An Asset Administration Shell

    :param security_instance: Definition of the security relevant aspects of the AAS (mandatory)
    :param asset: reference to the asset the AAS is representing (mandatory)
                TODO: Check if referenced element is of class Asset
    :param submodel_list: The asset of an AAS is typically described by one or more submodels
                          TODO: Check if referenced elements are of class Submodel
    :param concept_dictionary: An AAS max have one or more concept dictionaries assigned to it. The concept dictionaries
                               typically contain only descriptions for elements that are also used within the AAS
    :param view_list: If needed stakeholder specific views can be defined on the elements of the AAS
    :param derived_from: The reference to the AAS the AAs was derived from
                         TODO: Check if referenced element is of class AssetAdministrationShell
    """
    def __init__(self, security_instance: security.Security, asset: util.Reference,
                 submodel_list: Optional[List[util.Reference]] = [],
                 concept_dictionary: Optional[List[ConceptDictionary]] = [],
                 view_list: Optional[List[View]] = [], derived_from: Optional[util.Reference] = None):

        super().__init__()
        self.derived_from: Optional[util.Reference] = derived_from
        self.security: security.Security = security_instance
        self.asset: util.Reference = asset
        self.submodel_list: Optional[List[util.Reference]] = submodel_list
        self.concept_dictionary: Optional[List[ConceptDictionary]] = concept_dictionary
        self.view_list: Optional[List[View]] = view_list
