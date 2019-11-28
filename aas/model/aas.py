
from typing import Optional, Set

from . import base, security


class View:
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one or more stakeholders.

    todo: what does this exactly?

    :ivar contained_element: Unordered list of references to elements of class Referable
    """
    def __init__(self,
                 contained_element: Optional[Set[base.Reference]] = None):
        """
        Initializer of View

        :param contained_element: Unordered list of references to elements of class Referable

        TODO: Add instruction what to do after construction
        """
        self.contained_element: Optional[Set[base.Reference]] = set() \
            if contained_element is None else contained_element


class Asset(base.HasDataSpecification, base.Identifiable):
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
                 asset_identification_model: Optional[base.Reference],
                 bill_of_material: Optional[base.Reference]):
        """
        Initializer of Asset

        :param kind: Denotes whether the Asset is of kind "Type" or "Instance".
        :param asset_identification_model: A reference to a Submodel that defines the handling of additional domain
                                           specific (proprietary) Identifiers for the asset like e.g. serial number etc
        :param bill_of_material: Bill of material of the asset represented by a submodel of the same AAS. This submodel
                                 contains a set of entities describing the material used to compose the composite I4.0
                                 Component.
        """
        super().__init__()
        self.kind: base.AssetKind = kind
        self.asset_identification_model: Optional[base.Reference] = asset_identification_model
        self.bill_of_material: Optional[base.Reference] = bill_of_material


class ConceptDescription(base.HasDataSpecification, base.Identifiable):
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
                 data_specification: Optional[Set[base.Reference]] = None,
                 administration: Optional[base.AdministrativeInformation] = None):
        """
        Initializer of ConceptDescription

        :param identification: The globally unique identification of the element. (from base.Identifiable)
        :param is_case_of: Unordered list of global references to external definitions the concept is compatible to or
                           was derived from.
                           Note: Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360
        :param data_specification: Unordered list of global references to the data specification template used by the
                                   element. (from base.HasDataSpecification)
        :param administration: Administrative information of an identifiable element. (from base.Identifiable)
        """
        super().__init__()
        self.identification: base.Identifier = identification
        self.is_case_of: Optional[Set[base.Reference]] = set() \
            if is_case_of is None else is_case_of
        self.data_specification: Set[base.Reference] = set() \
            if data_specification is None else data_specification
        self.administration: Optional[base.AdministrativeInformation] = administration


class ConceptDictionary(base.Referable):
    """
    A dictionary contains concept descriptions.

    Typically a concept description dictionary of an AAS contains only concept descriptions of elements used within
    submodels of the AAS.


    :param concept_description: Unordered list of references to elements of class ConceptDescription
    """
    def __init__(self,
                 id_short: str,
                 concept_description: Optional[Set[base.Reference]] = None,
                 category: Optional[str] = None,
                 description: Optional[base.LangStringSet] = None,
                 parent: Optional[base.Namespace] = None):
        """
        Initializer of ConceptDictionary

        :param id_short: Identifying string of the element within its name space. (from base.Referable)
        :param concept_description: Unordered list of references to elements of class ConceptDescription
        :param category: The category is a value that gives further meta information w.r.t. to the class of the element.
                         It affects the expected existence of attributes and the applicability of constraints. (from
                         base.Referable)
        :param description: Description or comments on the element. (from base.Referable)
        :param parent: Reference to the next referable parent element of the element. (from base.Referable)

        TODO: Add instruction what to do after construction
        """
        super().__init__()
        self.concept_description: Optional[Set[base.Reference]] = set() \
            if concept_description is None else concept_description
        self.id_short: str = id_short
        self.category: Optional[str] = category
        self.description: Optional[base.LangStringSet] = description
        self.parent: Optional[base.Namespace] = parent


class AssetAdministrationShell(base.HasDataSpecification, base.Identifiable):
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
                 asset: base.Reference,
                 security_: Optional[security.Security] = None,
                 submodel_: Optional[Set[base.Reference]] = None,
                 concept_dictionary: Optional[Set[ConceptDictionary]] = None,
                 view: Optional[Set[View]] = None,
                 derived_from: Optional[base.Reference] = None):
        """
        Initializer of AssetAdministrationShell

        :param asset: reference to the asset the AAS is representing.
        :param security_: Definition of the security relevant aspects of the AAS.
        :param submodel_: Unordered list of submodels to describe typically the asset of an AAS.
        :param concept_dictionary: Unordered list of concept dictionaries. The concept dictionaries typically contain
                                   only descriptions for elements that are also used within the AAS
        :param view: Unordered list of stakeholder specific views that can group the elements of the AAS.
        :param derived_from: The reference to the AAS the AAs was derived from
        """

        super().__init__()
        self.derived_from: Optional[base.Reference] = derived_from
        self.security_: Optional[security.Security] = security_
        self.asset: base.Reference = asset
        self.submodel_: Optional[Set[base.Reference]] = set() \
            if submodel_ is None else submodel_
        self.concept_dictionary: Optional[Set[ConceptDictionary]] = set() \
            if concept_dictionary is None else concept_dictionary
        self.view: Optional[Set[View]] = set() if view is None else view
