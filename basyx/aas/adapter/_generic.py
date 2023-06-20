# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
The dicts defined in this module are used in the json and xml modules to translate enum members of our
implementation to the respective string and vice versa.
"""
from typing import Dict, Type

from basyx.aas import model

# XML Namespace definition
XML_NS_MAP = {"aas": "https://admin-shell.io/aas/3/0"}
XML_NS_AAS = "{" + XML_NS_MAP["aas"] + "}"

MODELING_KIND: Dict[model.ModelingKind, str] = {
    model.ModelingKind.TEMPLATE: 'Template',
    model.ModelingKind.INSTANCE: 'Instance'}

ASSET_KIND: Dict[model.AssetKind, str] = {
    model.AssetKind.TYPE: 'Type',
    model.AssetKind.INSTANCE: 'Instance',
    model.AssetKind.NOT_APPLICABLE: 'NotApplicable'}

QUALIFIER_KIND: Dict[model.QualifierKind, str] = {
    model.QualifierKind.CONCEPT_QUALIFIER: 'ConceptQualifier',
    model.QualifierKind.TEMPLATE_QUALIFIER: 'TemplateQualifier',
    model.QualifierKind.VALUE_QUALIFIER: 'ValueQualifier'}

DIRECTION: Dict[model.Direction, str] = {
    model.Direction.INPUT: 'input',
    model.Direction.OUTPUT: 'output'}

STATE_OF_EVENT: Dict[model.StateOfEvent, str] = {
    model.StateOfEvent.ON: 'on',
    model.StateOfEvent.OFF: 'off'}

REFERENCE_TYPES: Dict[Type[model.Reference], str] = {
    model.GlobalReference: 'GlobalReference',
    model.ModelReference: 'ModelReference'}

KEY_TYPES: Dict[model.KeyTypes, str] = {
    model.KeyTypes.ASSET_ADMINISTRATION_SHELL: 'AssetAdministrationShell',
    model.KeyTypes.CONCEPT_DESCRIPTION: 'ConceptDescription',
    model.KeyTypes.SUBMODEL: 'Submodel',
    model.KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement',
    model.KeyTypes.BASIC_EVENT_ELEMENT: 'BasicEventElement',
    model.KeyTypes.BLOB: 'Blob',
    model.KeyTypes.CAPABILITY: 'Capability',
    model.KeyTypes.DATA_ELEMENT: 'DataElement',
    model.KeyTypes.ENTITY: 'Entity',
    model.KeyTypes.EVENT_ELEMENT: 'EventElement',
    model.KeyTypes.FILE: 'File',
    model.KeyTypes.MULTI_LANGUAGE_PROPERTY: 'MultiLanguageProperty',
    model.KeyTypes.OPERATION: 'Operation',
    model.KeyTypes.PROPERTY: 'Property',
    model.KeyTypes.RANGE: 'Range',
    model.KeyTypes.REFERENCE_ELEMENT: 'ReferenceElement',
    model.KeyTypes.RELATIONSHIP_ELEMENT: 'RelationshipElement',
    model.KeyTypes.SUBMODEL_ELEMENT: 'SubmodelElement',
    model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION: 'SubmodelElementCollection',
    model.KeyTypes.SUBMODEL_ELEMENT_LIST: 'SubmodelElementList',
    model.KeyTypes.GLOBAL_REFERENCE: 'GlobalReference',
    model.KeyTypes.FRAGMENT_REFERENCE: 'FragmentReference'}

ENTITY_TYPES: Dict[model.EntityType, str] = {
    model.EntityType.CO_MANAGED_ENTITY: 'CoManagedEntity',
    model.EntityType.SELF_MANAGED_ENTITY: 'SelfManagedEntity'}

IEC61360_DATA_TYPES: Dict[model.base.IEC61360DataType, str] = {
    model.base.IEC61360DataType.DATE: 'DATE',
    model.base.IEC61360DataType.STRING: 'STRING',
    model.base.IEC61360DataType.STRING_TRANSLATABLE: 'STRING_TRANSLATABLE',
    model.base.IEC61360DataType.REAL_MEASURE: 'REAL_MEASURE',
    model.base.IEC61360DataType.REAL_COUNT: 'REAL_COUNT',
    model.base.IEC61360DataType.REAL_CURRENCY: 'REAL_CURRENCY',
    model.base.IEC61360DataType.BOOLEAN: 'BOOLEAN',
    model.base.IEC61360DataType.URL: 'URL',
    model.base.IEC61360DataType.RATIONAL: 'RATIONAL',
    model.base.IEC61360DataType.RATIONAL_MEASURE: 'RATIONAL_MEASURE',
    model.base.IEC61360DataType.TIME: 'TIME',
    model.base.IEC61360DataType.TIMESTAMP: 'TIMESTAMP',
}

IEC61360_LEVEL_TYPES: Dict[model.base.IEC61360LevelType, str] = {
    model.base.IEC61360LevelType.MIN: 'min',
    model.base.IEC61360LevelType.NOM: 'nom',
    model.base.IEC61360LevelType.TYP: 'typ',
    model.base.IEC61360LevelType.MAX: 'max',
}

MODELING_KIND_INVERSE: Dict[str, model.ModelingKind] = {v: k for k, v in MODELING_KIND.items()}
ASSET_KIND_INVERSE: Dict[str, model.AssetKind] = {v: k for k, v in ASSET_KIND.items()}
QUALIFIER_KIND_INVERSE: Dict[str, model.QualifierKind] = {v: k for k, v in QUALIFIER_KIND.items()}
DIRECTION_INVERSE: Dict[str, model.Direction] = {v: k for k, v in DIRECTION.items()}
STATE_OF_EVENT_INVERSE: Dict[str, model.StateOfEvent] = {v: k for k, v in STATE_OF_EVENT.items()}
REFERENCE_TYPES_INVERSE: Dict[str, Type[model.Reference]] = {v: k for k, v in REFERENCE_TYPES.items()}
KEY_TYPES_INVERSE: Dict[str, model.KeyTypes] = {v: k for k, v in KEY_TYPES.items()}
ENTITY_TYPES_INVERSE: Dict[str, model.EntityType] = {v: k for k, v in ENTITY_TYPES.items()}
IEC61360_DATA_TYPES_INVERSE: Dict[str, model.base.IEC61360DataType] = {v: k for k, v in IEC61360_DATA_TYPES.items()}
IEC61360_LEVEL_TYPES_INVERSE: Dict[str, model.base.IEC61360LevelType] = \
    {v: k for k, v in IEC61360_LEVEL_TYPES.items()}

KEY_TYPES_CLASSES_INVERSE: Dict[model.KeyTypes, Type[model.Referable]] = \
    {v: k for k, v in model.KEY_TYPES_CLASSES.items()}
