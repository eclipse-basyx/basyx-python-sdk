"""
This package contains a python implementation of the meta-model of the AssetAdministrationShell.
The model is divided into 5 modules, splitting it where it in sensible parts.

aas.py
    The main module, implementing high-level structures, such as AssetAdministrationShell, Asset and ConceptDictionary.

base.py
    Basic structures of the model, including all abstract classes and enumerations. This provides inheritance for the
    higher level structures.

registry.py
    Registries for the AAS, in order to enable resolving global identifiers; and mapping identifiers to identifiable
    objects.

security.py
    Security model of the AAS. Currently not existing.

submodel.py
    Meta-model of the submodels and events.
"""

from typing import Dict

from .aas import *
from .security import *
from .base import *
from .submodel import *
from .registry import *

# A mapping of PyI40AAS implementation classes to the corresponding `KeyElements` enum members for all classes that are
# covered by this enum.
KEY_ELEMENTS_CLASSES: Dict[type, KeyElements] = {
    Asset: KeyElements.ASSET,
    AssetAdministrationShell: KeyElements.ASSET_ADMINISTRATION_SHELL,
    ConceptDescription: KeyElements.CONCEPT_DESCRIPTION,
    Submodel: KeyElements.SUBMODEL,
    View: KeyElements.VIEW,
    ConceptDictionary: KeyElements.CONCEPT_DICTIONARY,
    Entity: KeyElements.ENTITY,
    BasicEvent: KeyElements.BASIC_EVENT,
    Event: KeyElements.EVENT,
    Blob: KeyElements.BLOB,
    File: KeyElements.FILE,
    Operation: KeyElements.OPERATION,
    Capability: KeyElements.CAPABILITY,
    Property: KeyElements.PROPERTY,
    MultiLanguageProperty: KeyElements.MULTI_LANGUAGE_PROPERTY,
    Range: KeyElements.RANGE,
    ReferenceElement: KeyElements.REFERENCE_ELEMENT,
    DataElement: KeyElements.DATA_ELEMENT,
    SubmodelElementCollection: KeyElements.SUBMODEL_ELEMENT_COLLECTION,
    AnnotatedRelationshipElement: KeyElements.ANNOTATED_RELATIONSHIP_ELEMENT,
    RelationshipElement: KeyElements.RELATIONSHIP_ELEMENT,
    SubmodelElement: KeyElements.SUBMODEL_ELEMENT,
}
