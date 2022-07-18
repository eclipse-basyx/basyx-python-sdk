"""
This package contains a python implementation of the meta-model of the AssetAdministrationShell.
The model is divided into 5 modules, splitting it in sensible parts. However, all classes (except for the
specialized Concept Descriptions) are imported into this top-level package, for simple imports like

.. code-block:: python

    from aas.model import AssetAdministrationShell, Submodel, Property

The different modules are:

aas.py
    The main module, implementing high-level structures, such as AssetAdministrationShell and ConceptDictionary.

base.py
    Basic structures of the model, including all abstract classes and enumerations. This provides inheritance for the
    higher level structures.

concept.py
    :class:`~aas.model.concept.ConceptDescription` from the AAS meta model
    as well as specialized :class:`ConceptDescriptions <aas.model.concept.ConceptDescription>` like
    :class:`~aas.model.concept.IEC61360ConceptDescription`

provider.py
    Providers for AAS objects, in order to store and retrieve :class:`~aas.model.base.Identifiable` objects by their
    :class:`~aas.model.base.Identifier`.

security.py
    Security model of the AAS. Currently not existing.

submodel.py
    Meta-model of the submodels and events.
"""

from .aas import *
from .security import *
from .base import *
from .submodel import *
from .provider import *
from .concept import ConceptDescription, IEC61360ConceptDescription
from . import datatypes

# A mapping of BaSyx Python SDK implementation classes to the corresponding `KeyTypes` enum members for all classes
# that are covered by this enum.
KEY_TYPES_CLASSES: Dict[Type[Referable], KeyTypes] = {
    AssetAdministrationShell: KeyTypes.ASSET_ADMINISTRATION_SHELL,
    ConceptDescription: KeyTypes.CONCEPT_DESCRIPTION,
    Submodel: KeyTypes.SUBMODEL,
    Entity: KeyTypes.ENTITY,
    BasicEventElement: KeyTypes.BASIC_EVENT_ELEMENT,
    EventElement: KeyTypes.EVENT_ELEMENT,
    Blob: KeyTypes.BLOB,
    File: KeyTypes.FILE,
    Operation: KeyTypes.OPERATION,
    Capability: KeyTypes.CAPABILITY,
    Property: KeyTypes.PROPERTY,
    MultiLanguageProperty: KeyTypes.MULTI_LANGUAGE_PROPERTY,
    Range: KeyTypes.RANGE,
    ReferenceElement: KeyTypes.REFERENCE_ELEMENT,
    DataElement: KeyTypes.DATA_ELEMENT,
    SubmodelElementCollection: KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
    AnnotatedRelationshipElement: KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT,
    RelationshipElement: KeyTypes.RELATIONSHIP_ELEMENT,
    SubmodelElement: KeyTypes.SUBMODEL_ELEMENT,
}
