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
The dicts defined in this module are used in the json and xml modules to translate enum members of our
implementation to the respective string and vice versa.
"""
from typing import Dict, Type

from aas import model

MODELING_KIND: Dict[model.ModelingKind, str] = {
    model.ModelingKind.TEMPLATE: 'Template',
    model.ModelingKind.INSTANCE: 'Instance'}

ASSET_KIND: Dict[model.AssetKind, str] = {
    model.AssetKind.TYPE: 'Type',
    model.AssetKind.INSTANCE: 'Instance'}

KEY_ELEMENTS: Dict[model.KeyElements, str] = {
    model.KeyElements.ASSET: 'Asset',
    model.KeyElements.ASSET_ADMINISTRATION_SHELL: 'AssetAdministrationShell',
    model.KeyElements.CONCEPT_DESCRIPTION: 'ConceptDescription',
    model.KeyElements.SUBMODEL: 'Submodel',
    model.KeyElements.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement',
    model.KeyElements.BASIC_EVENT: 'BasicEvent',
    model.KeyElements.BLOB: 'Blob',
    model.KeyElements.CAPABILITY: 'Capability',
    model.KeyElements.CONCEPT_DICTIONARY: 'ConceptDictionary',
    model.KeyElements.DATA_ELEMENT: 'DataElement',
    model.KeyElements.ENTITY: 'Entity',
    model.KeyElements.EVENT: 'Event',
    model.KeyElements.FILE: 'File',
    model.KeyElements.MULTI_LANGUAGE_PROPERTY: 'MultiLanguageProperty',
    model.KeyElements.OPERATION: 'Operation',
    model.KeyElements.PROPERTY: 'Property',
    model.KeyElements.RANGE: 'Range',
    model.KeyElements.REFERENCE_ELEMENT: 'ReferenceElement',
    model.KeyElements.RELATIONSHIP_ELEMENT: 'RelationshipElement',
    model.KeyElements.SUBMODEL_ELEMENT: 'SubmodelElement',
    model.KeyElements.SUBMODEL_ELEMENT_COLLECTION: 'SubmodelElementCollection',
    model.KeyElements.VIEW: 'View',
    model.KeyElements.GLOBAL_REFERENCE: 'GlobalReference',
    model.KeyElements.FRAGMENT_REFERENCE: 'FragmentReference'}

KEY_TYPES: Dict[model.KeyType, str] = {
    model.KeyType.CUSTOM: 'Custom',
    model.KeyType.IRDI: 'IRDI',
    model.KeyType.IRI: 'IRI',
    model.KeyType.IDSHORT: 'IdShort',
    model.KeyType.FRAGMENT_ID: 'FragmentId'}

IDENTIFIER_TYPES: Dict[model.IdentifierType, str] = {
    model.IdentifierType.CUSTOM: 'Custom',
    model.IdentifierType.IRDI: 'IRDI',
    model.IdentifierType.IRI: 'IRI'}

ENTITY_TYPES: Dict[model.EntityType, str] = {
    model.EntityType.CO_MANAGED_ENTITY: 'CoManagedEntity',
    model.EntityType.SELF_MANAGED_ENTITY: 'SelfManagedEntity'}

IEC61360_DATA_TYPES: Dict[model.concept.IEC61360DataType, str] = {
    model.concept.IEC61360DataType.DATE: 'DATE',
    model.concept.IEC61360DataType.STRING: 'STRING',
    model.concept.IEC61360DataType.STRING_TRANSLATABLE: 'STRING_TRANSLATABLE',
    model.concept.IEC61360DataType.REAL_MEASURE: 'REAL_MEASURE',
    model.concept.IEC61360DataType.REAL_COUNT: 'REAL_COUNT',
    model.concept.IEC61360DataType.REAL_CURRENCY: 'REAL_CURRENCY',
    model.concept.IEC61360DataType.BOOLEAN: 'BOOLEAN',
    model.concept.IEC61360DataType.URL: 'URL',
    model.concept.IEC61360DataType.RATIONAL: 'RATIONAL',
    model.concept.IEC61360DataType.RATIONAL_MEASURE: 'RATIONAL_MEASURE',
    model.concept.IEC61360DataType.TIME: 'TIME',
    model.concept.IEC61360DataType.TIMESTAMP: 'TIMESTAMP',
}

IEC61360_LEVEL_TYPES: Dict[model.concept.IEC61360LevelType, str] = {
    model.concept.IEC61360LevelType.MIN: 'Min',
    model.concept.IEC61360LevelType.MAX: 'Max',
    model.concept.IEC61360LevelType.NOM: 'Nom',
    model.concept.IEC61360LevelType.TYP: 'Typ',
}

MODELING_KIND_INVERSE: Dict[str, model.ModelingKind] = {v: k for k, v in MODELING_KIND.items()}
ASSET_KIND_INVERSE: Dict[str, model.AssetKind] = {v: k for k, v in ASSET_KIND.items()}
KEY_ELEMENTS_INVERSE: Dict[str, model.KeyElements] = {v: k for k, v in KEY_ELEMENTS.items()}
KEY_TYPES_INVERSE: Dict[str, model.KeyType] = {v: k for k, v in KEY_TYPES.items()}
IDENTIFIER_TYPES_INVERSE: Dict[str, model.IdentifierType] = {v: k for k, v in IDENTIFIER_TYPES.items()}
ENTITY_TYPES_INVERSE: Dict[str, model.EntityType] = {v: k for k, v in ENTITY_TYPES.items()}
IEC61360_DATA_TYPES_INVERSE: Dict[str, model.concept.IEC61360DataType] = {v: k for k, v in IEC61360_DATA_TYPES.items()}
IEC61360_LEVEL_TYPES_INVERSE: Dict[str, model.concept.IEC61360LevelType] = \
    {v: k for k, v in IEC61360_LEVEL_TYPES.items()}

KEY_ELEMENTS_CLASSES_INVERSE: Dict[model.KeyElements, Type[model.Referable]] = \
    {v: k for k, v in model.KEY_ELEMENTS_CLASSES.items()}
