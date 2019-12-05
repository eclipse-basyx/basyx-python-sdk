from .. import model
from json import JSONEncoder

MODELING_KIND = {'TEMPLATE': 'Template', 'INSTANCE': 'Instance'}

ASSET_KIND = {'TYPE': 'Type', 'INSTANCE': 'Instance'}

KEY_ELEMENTS = {'ASSET': 'Asset',
                'ASSET_ADMINISTRATION_SHELL': 'AssetAdministrationShell',
                'CONCEPT_DESCRIPTION': 'ConceptDescription',
                'SUBMODEL': 'Submodel',
                'ACCESS_PERMISSION_RULE': 'AccessPermissionRule',
                'ANNOTATION_RELATIONSHIP_ELEMENT': 'AnnotatedRelationshipElement',
                'BASIC_EVENT': 'BasicEvent',
                'BLOB': 'Blob',
                'CAPABILITY': 'Capability',
                'CONCEPT_DICTIONARY': 'ConceptDictionary',
                'DATA_ELEMENT': 'DataElement',
                'ENTITY': 'Entity',
                'EVENT': 'Event',
                'FILE': 'File',
                'MULTI_LANGUAGE_PROPERTY': 'MultiLanguageProperty',
                'OPERATION': 'Operation',
                'PROPERTY': 'Property',
                'RANGE': 'Range',
                'REFERENCE_ELEMENT': 'ReferenceElement',
                'RELATIONSHIP_ELEMENT': 'RelationshipElement',
                'SUBMODEL_ELEMENT': 'SubmodelElement',
                'SUBMODEL_ELEMENT_COLLECTION': 'SubmodelElementCollection',
                'VIEW': 'View',
                'GLOBAL_REFERENCE': 'GlobalReference',
                'FRAGMENT_REFERENCE': 'FragmentReference'}

KEY_TYPES = {'CUSTOM': 'Custom',
             'IRDI': 'IRDI',
             'IRI': 'IRI',
             'IDSHORT': 'IdShort',
             'FRAGMENT_ID': 'FragmentId'}

ENTITY_TYPES = {'CO_MANAGED_ENTITY': 'CoManagedEntity',
                'SELF_MANAGED_ENTITY': 'SelfManagedEntity'}


#  function to serialize abstract base classes
def referable_to_json(obj):
    data = {}
    if isinstance(obj, model.Referable):
        data['idShort'] = obj.id_short
        if obj.category:
            data['category'] = obj.category
        if obj.description:
            data['description'] = obj.description
        data['modelType'] = obj.__class__.__name__
    return data


def identifiable_to_json(obj):
    data = {}
    if isinstance(obj, model.Identifiable):
        data['identification'] = obj.identification
        if obj.administration:
            data['AdministrativeInformation'] = obj.administration
    return data


def has_data_specification_to_json(obj):  # TODO add DataSpecificationContent
    if isinstance(obj, model.HasDataSpecification):
        if obj.data_specification:
            return {"embeddedDataSpecification": list(obj.data_specification)}
    return {}


def has_semantics_to_json(obj):
    if isinstance(obj, model.HasSemantics):
        return {"semanticID": obj.semantic_id}
    return {}


def has_kind_to_json(obj):
    if isinstance(obj, model.HasKind):
        return {"kind": MODELING_KIND[obj.kind._name_]}
    return {}


def qualifiable_to_json(obj):
    if isinstance(obj, model.Qualifiable):
        if obj.qualifier:
            return {'qualifiers': list(obj.qualifier)}
    return {}


def abstract_classes_to_json(obj):
    data = {}
    data.update(referable_to_json(obj))
    data.update(identifiable_to_json(obj))
    data.update(has_data_specification_to_json(obj))
    data.update(has_semantics_to_json(obj))
    data.update(has_kind_to_json(obj))
    data.update(qualifiable_to_json(obj))
    return data


#  function to serialize classes from model.base
def lang_string_set_to_json(obj):  # TODO check if correct
    return {dict(obj)}


def key_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'type': KEY_ELEMENTS[obj.type_],
                 'idType': KEY_TYPES[obj.id_type],
                 'value': obj.value,
                 'local': obj.local})
    return data


def administrative_information_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.version:
        data['version'] = obj.version
    if obj.revision:
        data['revision'] = obj.revision
    return data


def identifier_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['id'] = obj.id
    data['idType'] = KEY_TYPES[obj.id_type._name_]
    return data


def reference_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['keys'] = list(obj.key)
    return data


def constraint_to_json(obj):  # TODO check if correct for each class
    if isinstance(obj, model.Constraint):
        return {'modelType': obj.__class__.__name__}
    return {}


def namespace_to_json(obj):  # not in specification yet
    return {}


def formula_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update(constraint_to_json(obj))
    if obj.depends_on:
        data['dependsOn'] = list(obj.depends_on)
    return data


def qualifier_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update(constraint_to_json(obj))
    if obj.value:
        data['value'] = obj.value
    if obj.valueId:
        data['valueId'] = obj.valueId
    data['valueType'] = obj.value_type
    data['type'] = obj.type_
    return


def value_reference_pair_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'value': obj.value,
                 'valueId': obj.valueId,
                 'valueType': obj.value_type})
    return data


def value_list_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['valueReferencePairTypes'] = obj.value_reference_pair_type
    return data


def namespace_set_to_json(obj):
    data = abstract_classes_to_json(obj)
    return data


def ordered_namespace_set_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update(namespace_to_json(obj))
    return data


#  function to serialize classes from model.aas

def view_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.contained_element:
        data['containedElements'] = obj.contained_element
    return data


def asset_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['kind'] = ASSET_KIND[obj.kind._name_]
    if obj.asset_identification_model:
        data['assetIdentificationModel'] = obj.asset_identification_model
    if obj.bill_of_material:
        data['billOfMaterial'] = obj.bill_of_material
    return data


def concept_description_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.is_case_of:
        data['isCaseOf'] = list(obj.is_case_of)
    return data


def concept_dictionary_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.concept_description:
        data['conceptDescriptions'] = list(obj.concept_description)
    return data


def asset_administration_shell_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update(namespace_to_json(obj))
    if obj.derived_from:
        data["derivedFrom"] = obj.derived_from
    data["asset"] = obj.asset
    if obj.submodel_:
        data["submodels"] = list(obj.submodel_)
    if obj.view:
        data["views"] = list(obj.view)
    if obj.concept_dictionary:
        data["conceptDictionaries"] = list(obj.concept_dictionary)
    if obj.security_:
        data["security"] = obj.security_
    return data


#  function to serialize classes from model.security


def security_to_json(obj):  # has no attributes in our implementation
    return {}


#  function to serialize classes from model.submodel

def submodel_element_to_json(obj):  # TODO make kind optional
    data = abstract_classes_to_json(obj)
    return data


def submodel_to_json(obj):  # TODO make kind optional
    data = abstract_classes_to_json(obj)
    data['submodelElements'] = list(obj.submodel_element)
    return data


def data_element_to_json(obj):  # no attributes in specification yet
    return {}


def property_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = obj.value
    if obj.value_id:
        data['valueId'] = obj.value_id
    data['valueType'] = obj.value_type
    return data


def multi_language_property_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = obj.value
    if obj.value_id:
        data['valueId'] = obj.value_id
    return data


def range_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'valueType': obj.value_type, 'min': obj.min_, 'max': obj.max_})
    return data


def blob_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'value': obj.value, 'mimeType': obj.mime_type})
    return data


def file_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'value': obj.value, 'mimeType': obj.mime_type})
    return data


def reference_element_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = obj.value
    return data


def submodel_element_collection_to_json(obj):
    # serialization for SubmodelELementCollectionOrdered and SubmodelELementCollectionUnOrdered
    data = abstract_classes_to_json(obj)
    if obj.value:
        data['value'] = list(obj.value)
    if obj.ordered:
        data['odered'] = obj.ordered
    return data


def relationship_element_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'first': obj.first, 'second': obj.second})
    return data


def annotated_relationship_element_to_json(obj):
    data = abstract_classes_to_json(obj)
    data.update({'first': obj.first, 'second': obj.second})
    if obj.annotation:
        data['annotation'] = list(obj.annotation)
    return data


def operation_variable_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['value'] = obj.value
    return data


def operation_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.input_variable:
        data['inputVariable'] = list(obj.input_variable)
    if obj.output_variable:
        data['outputVariable'] = list(obj.output_variable)
    if obj.inoutput_variable:
        data['inoutputVariable'] = list(obj.inoutput_variable)
    return data


def capability_to_json(obj):  # no attributes in specification yet
    data = abstract_classes_to_json(obj)
    return data


def entity_to_json(obj):
    data = abstract_classes_to_json(obj)
    if obj.statement:
        data['statements'] = list(obj.statement)
    data['entityType'] = ENTITY_TYPES[obj.entity_type._name_]
    if obj.asset:
        data['asset'] = obj.asset
    return data


def event_to_json(obj):  # no attributes in specification yet
    return {}


def basic_event_to_json(obj):
    data = abstract_classes_to_json(obj)
    data['observed'] = obj.observed
    return data


class AASToJsonEncoder(JSONEncoder):
    """

    """

    def default(self, obj):
        if isinstance(obj, model.AssetAdministrationShell):
            return asset_administration_shell_to_json(obj)
        if isinstance(obj, model.Identifier):
            return identifier_to_json()
        if isinstance(obj, model.AdministrativeInformation):
            return administrative_information_to_json()
        if isinstance(obj, model.Reference):
            return reference_to_json(obj)
        if isinstance(obj, model.Key):
            return key_to_json(obj)
        if isinstance(obj, model.Asset):
            return asset_to_json(obj)
        if isinstance(obj, model.Submodel):
            return submodel_to_json(obj)
        if isinstance(obj, model.Operation):
            return operation_to_json(obj)
        if isinstance(obj, model.OperationVariable):
            return operation_variable_to_json(obj)
        if isinstance(obj, model.BasicEvent):
            return basic_event_to_json(obj)
        if isinstance(obj, model.Entity):
            return entity_to_json(obj)
        if isinstance(obj, model.View):
            return view_to_json(obj)
        if isinstance(obj, model.ConceptDictionary):
            return concept_dictionary_to_json(obj)
        if isinstance(obj, model.ConceptDescription):
            return concept_description_to_json(obj)
        if isinstance(obj, model.Property):
            return property_to_json(obj)
        if isinstance(obj, model.Range):
            return range_to_json(obj)
        if isinstance(obj, model.MultiLanguageProperty):
            return multi_language_property_to_json(obj)
        if isinstance(obj, model.File):
            return file_to_json(obj)
        if isinstance(obj, model.Blob):
            return blob_to_json(obj)
        if isinstance(obj, model.ReferenceElement):
            return reference_element_to_json(obj)
        if isinstance(obj, model.SubmodelElementCollection):
            return submodel_element_collection_to_json(obj)
        if isinstance(obj, model.RelationshipElement):
            return relationship_element_to_json(obj)
        if isinstance(obj, model.AnnotatedRelationshipElement):
            return annotated_relationship_element_to_json(obj)
        if isinstance(obj, model.Qualifier):
            return qualifier_to_json(obj)
        if isinstance(obj, model.Formula):
            return formula_to_json(obj)
        return super().default()
