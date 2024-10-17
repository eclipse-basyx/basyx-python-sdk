# Copyright (c) 2023 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
.. _adapter.json.rdf_serialization:

Module for serializing Asset Administration Shell objects to the official RDF format

How to use:

- For generating an RDF-File from a :class:`~basyx.aas.model.provider.AbstractObjectStore`, check out the function
  :func:`write_aas_rdf_file`.
- To receive the rdf as a serialized string, you can also use :func:`object_store_to_rdf` directly.
- The serializer class:`AASToJsonEncoder` is the main class which iteratively builds an rdflib Graph from all objects
  in the object store. It is currently not possible to serialize single objects due to their relationships which are
  part of the shacl validation.
"""


from typing import Dict, Type, Union
import base64

from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import OWL, RDF, Namespace, XSD

from basyx.aas import model
from .. import _generic

NS_AAS = _generic.XML_NS_MAP["aas"]


class AASToRDFEncoder():
    def __init__(self) -> None:
        self.graph = Graph()
        self.aas = Namespace(NS_AAS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
        self.graph.bind("aas", self.aas)

    def object_store_to_rdflib_graph(self, data: model.AbstractObjectStore) -> Graph:
        """
        Serialize a set of AAS objects to an RDFlib graph object.
        This class function is used internally by :meth:`write_aas_rdf_file` and shouldn't be
        called directly for most use-cases.

        :param data: :class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` which contains different objects of
                    the AAS meta model which should be serialized to an RDF file
        """
        for obj in data:
            if isinstance(obj, model.AssetAdministrationShell):
                self._asset_administration_shell_to_rdf(obj)
            elif isinstance(obj, model.Submodel):
                self._submodel_to_rdf(obj)
            elif isinstance(obj, model.ConceptDescription):
                self._concept_description_to_rdf(obj)
        return self.graph

    def _boolean_to_rdf(self, obj: bool) -> str:
        """
        Serialize a boolean

        :param obj: Boolean (``True``, ``False``)
        :return: String in the XML accepted form (``true``, ``false``)
        """
        if obj:
            return "true"
        else:
            return "false"

    def _abstract_classes_to_rdf(self, obj: object, parent: Union[URIRef, BNode]) -> None:
        """
        Adds attributes of abstract base classes of ``obj``.

        If the object obj is inheriting from any abstract AAS class, this function adds all the serialized information of
        those abstract classes to the generated element.

        :param obj: An object of the AAS
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        if isinstance(obj, model.HasExtension):
            if obj.extension:
                for extension in obj.extension:
                    if isinstance(extension, model.Extension):
                        self._extension_to_rdf(extension, parent)
        if isinstance(obj, model.Referable):
            if obj.category:
                self.graph.add((parent, self.aas["Referable/category"], Literal(str(obj.category), datatype=XSD.string)))
            if obj.id_short and not isinstance(obj.parent, model.SubmodelElementList):
                self.graph.add((parent, self.aas["Referable/idShort"], Literal(str(obj.id_short), datatype=XSD.string)))
            if obj.display_name:
                self._lang_string_set_to_rdf(obj.display_name, parent, self.aas["Referable/displayName"])
            if obj.description:
                self._lang_string_set_to_rdf(obj.description, parent, self.aas["Referable/description"])
        if isinstance(obj, model.Identifiable):
            if obj.administration:
                self._administrative_information_to_rdf(obj.administration, parent)
            self.graph.add((parent, self.aas["Identifiable/id"], Literal(str(obj.id), datatype=XSD.string)))
        if isinstance(obj, model.HasKind):
            if obj.kind is model.ModellingKind.TEMPLATE:
                self.graph.add((parent, self.aas["HasKind/kind"], self.aas["ModellingKind/Template"]))
            else:
                self.graph.add((parent, self.aas["HasKind/kind"], self.aas["ModellingKind/Instance"]))
        if isinstance(obj, model.HasSemantics):
            if obj.semantic_id:
                self._reference_to_rdf(obj.semantic_id, parent, self.aas["HasSemantics/semanticId"])
            if obj.supplemental_semantic_id:
                for supplemental_semantic_id in obj.supplemental_semantic_id:
                    self._reference_to_rdf(supplemental_semantic_id, parent, self.aas["HasSemantics/supplementalSemanticIds"])
        if isinstance(obj, model.Qualifiable):
            if obj.qualifier:
                for qualifier in obj.qualifier:
                    self._qualifier_to_rdf(qualifier, parent)
        if isinstance(obj, model.HasDataSpecification):
            if obj.embedded_data_specifications:
                for eds in obj.embedded_data_specifications:
                    self._embedded_data_specification_to_rdf(eds, parent)

    # ##############################################################
    # transformation functions to serialize classes from model.base
    # ##############################################################

    def _value_to_rdf(self, value: model.ValueDataType, value_type: model.DataTypeDefXsd, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of :class:`~basyx.aas.model.base.ValueDataType` to a joint rdflib Graph object

        :param value: :class:`~basyx.aas.model.base.ValueDataType` object
        :param value_type: Corresponding :class:`~basyx.aas.model.base.DataTypeDefXsd`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        self.graph.add((parent, objectProperty, Literal(model.datatypes.xsd_repr(value), datatype=XSD.string)))

    def _lang_string_set_to_rdf(self, obj: model.LangStringSet, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.LangStringSet` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.LangStringSet`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        # TODO: There is an ongoing bugfix of the validation shacl scheme for
        # incorrect object properties of these typse: https://github.com/aas-core-works/aas-core-codegen/issues/519
        # This should be valid once the changes get improved and merged
        LANG_STRING_SET_TAGS: Dict[Type[model.LangStringSet], URIRef] = {
            model.MultiLanguageNameType: self.aas["LangStringNameType"],
            model.MultiLanguageTextType: self.aas["LangStringTextType"],
            model.DefinitionTypeIEC61360: self.aas["LangStringDefinitionTypeIec61360"],
            model.PreferredNameTypeIEC61360: self.aas["LangStringPreferredNameTypeIec61360"],
            model.ShortNameTypeIEC61360: self.aas["LangStringShortNameTypeIec61360"]}
        for language, text in obj.items():
            lang_string = BNode()
            self.graph.add((parent, objectProperty, lang_string))
            self.graph.add((lang_string, RDF.type, LANG_STRING_SET_TAGS[type(obj)]))
            self.graph.add((lang_string, self.aas["AbstractLangString/language"], Literal(str(language), datatype=XSD.string)))
            self.graph.add((lang_string, self.aas["AbstractLangString/text"], Literal(str(text), datatype=XSD.string)))

    def _key_to_rdf(self, obj: model.Key, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.Key` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.Key`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        key = BNode()
        self.graph.add((parent, self.aas["Reference/keys"], key))
        self.graph.add((key, RDF.type, self.aas["Key"]))
        self.graph.add((key, self.aas["Key/type"], self.aas[f"KeyTypes/{_generic.KEY_TYPES[obj.type]}"]))
        self.graph.add((key, self.aas["Key/value"], Literal(str(obj.value), datatype=XSD.string)))

    def _administrative_information_to_rdf(self, obj: model.AdministrativeInformation, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.AdministrativeInformation` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.AdministrativeInformation`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        administrative_information = BNode()
        self.graph.add((parent, self.aas["Identifiable/administration"], administrative_information))
        self._abstract_classes_to_rdf(obj, administrative_information)
        if obj.version:
            self.graph.add((administrative_information, self.aas["AdministrativeInformation/version"], Literal(str(obj.version), datatype=XSD.string)))
        if obj.revision:
            self.graph.add((administrative_information, self.aas["AdministrativeInformation/revision"], Literal(str(obj.version), datatype=XSD.string)))
        if obj.creator:
            self._reference_to_rdf(obj.creator, administrative_information, self.aas["AdministrativeInformation/creator"])
        if obj.template_id:
            self.graph.add((administrative_information, self.aas["AdministrativeInformation/templateId"], Literal(str(obj.version), datatype=XSD.string)))

    def _reference_to_rdf(self, obj: model.Reference, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.Reference` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.Reference`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        reference = BNode()
        self.graph.add((parent, objectProperty, reference))
        self.graph.add((reference, RDF.type, self.aas["Reference"]))
        self.graph.add((reference, self.aas["Reference/type"], self.aas[f"ReferenceTypes/{_generic.REFERENCE_TYPES[obj.__class__]}"]))
        if obj.referred_semantic_id is not None:
            self._reference_to_rdf(obj.referred_semantic_id, reference, self.aas["Reference/referredSemanticId"])
        for aas_key in obj.key:
            self._key_to_rdf(aas_key, reference)

    def _qualifier_to_rdf(self, obj: model.Qualifier, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.Qualifier`
        to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.Qualifier`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        qualifier = BNode()
        self.graph.add((parent, self.aas["Qualifiable/qualifiers"], qualifier))
        self.graph.add((qualifier, RDF.type, self.aas["Qualifier"]))
        self._abstract_classes_to_rdf(obj, qualifier)
        self.graph.add((qualifier, self.aas["Qualifier/kind"], self.aas[f"QualifierKind/{_generic.QUALIFIER_KIND[obj.kind]}"]))
        self.graph.add((qualifier, self.aas["Qualifier/type"], Literal(str(obj.type), datatype=XSD.string)))
        self.graph.add((qualifier, self.aas["Qualifier/valueType"], self.aas[f"DataTypeDefXsd/{model.datatypes.XSD_TYPE_NAMES[obj.value_type]}"]))
        if obj.value:
            self._value_to_rdf(obj.value, obj.value_type, qualifier, self.aas["Qualifier/value"])
        if obj.value_id:
            self._reference_to_rdf(obj.value_id, qualifier, self.aas["Qualifier/valueId"])

    def _extension_to_rdf(self, obj: model.Extension, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.Extension` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.Extension`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        extension = BNode()
        self.graph.add((parent, self.aas["HasExtensions/extensions"], extension))
        self.graph.add((extension, RDF.type, self.aas["Extension"]))
        self._abstract_classes_to_rdf(obj, extension)
        self.graph.add((extension, self.aas["Extension/name"], Literal(str(obj.name), datatype=XSD.string)))
        if obj.value_type:
            self.graph.add((extension, self.aas["Extension/valueType"], self.aas[f"DataTypeDefXsd/{model.datatypes.XSD_TYPE_NAMES[obj.value_type]}"]))
        if obj.value:
            self._value_to_rdf(obj.value, obj.value_type, extension, self.aas["Extension/value"])
        if len(obj.refers_to) > 0:
            for reference in obj.refers_to:
                self._reference_to_rdf(reference, extension, self.aas["Extension/refersTo"])

    def _value_reference_pair_to_rdf(self, obj: model.ValueReferencePair, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.ValueReferencePair` to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.ValueReferencePair`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        value_reference_pair = BNode()
        self.graph.add((parent, objectProperty, value_reference_pair))
        self.graph.add((value_reference_pair, RDF.type, self.aas["ValueReferencePair"]))
        self.graph.add((value_reference_pair, self.aas["ValueReferencePair/value"], Literal(str(obj.value), datatype=XSD.string)))
        self._reference_to_rdf(obj.value_id, value_reference_pair, self.aas["ValueReferencePair/valueId"])

    def _value_list_to_rdf(self, obj: model.ValueList, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.ValueList` to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.ValueList`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        value_list = BNode()
        self.graph.add((parent, objectProperty, value_list))
        self.graph.add((value_list, RDF.type, self.aas["ValueList"]))
        self._abstract_classes_to_rdf(obj, value_list)
        for aas_reference_pair in obj:
            self._value_reference_pair_to_rdf(aas_reference_pair, value_list, self.aas["ValueList/valueReferencePairs"])

    # ############################################################
    # transformation functions to serialize classes from model.aas
    # ############################################################

    def _specific_asset_id_to_rdf(self, obj: model.SpecificAssetId, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.SpecificAssetId` to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.SpecificAssetId`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        specific_asset_id = BNode()
        self.graph.add((parent, objectProperty, specific_asset_id))
        self.graph.add((specific_asset_id, RDF.type, self.aas["SpecificAssetId"]))
        self._abstract_classes_to_rdf(obj, specific_asset_id)
        self.graph.add((specific_asset_id, self.aas["SpecificAssetId/name"], Literal(str(obj.name), datatype=XSD.string)))
        self.graph.add((specific_asset_id, self.aas["SpecificAssetId/value"], Literal(str(obj.value), datatype=XSD.string)))
        if obj.external_subject_id:
            self._reference_to_rdf(obj.external_subject_id, specific_asset_id, self.aas["SpecificAssetId/externalSubjectId"])

    def _asset_information_to_rdf(self, obj: model.AssetInformation, parent: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.aas.AssetInformation` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.aas.AssetInformation`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        asset_info = BNode()
        self.graph.add((parent, self.aas["AssetAdministrationShell/assetInformation"], asset_info))
        self.graph.add((asset_info, RDF.type, self.aas["AssetInformation"]))
        self._abstract_classes_to_rdf(obj, asset_info)
        self.graph.add((asset_info, self.aas["AssetInformation/assetKind"], self.aas[f"AssetKind/{_generic.ASSET_KIND[obj.asset_kind]}"]))
        if obj.global_asset_id:
            self.graph.add((asset_info, self.aas["AssetInformation/globalAssetId"], Literal(str(obj.global_asset_id), datatype=XSD.string)))
        if obj.specific_asset_id:
            for specific_asset_id in obj.specific_asset_id:
                self._specific_asset_id_to_rdf(specific_asset_id, asset_info, self.aas["AssetInformation/specificAssetIds"])
        if obj.asset_type:
            self.graph.add((asset_info, self.aas["AssetInformation/assetType"], Literal(str(obj.asset_type), datatype=XSD.string)))
        if obj.default_thumbnail:
            self._resource_to_rdf(obj.default_thumbnail, asset_info, self.aas["AssetInformation/defaultThumbnail"])

    def _concept_description_to_rdf(self, obj: model.ConceptDescription) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.concept.ConceptDescription` to
        to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.concept.ConceptDescription`
        :return: None
        """
        subject = URIRef(obj.id)
        self.graph.add((subject, RDF.type, self.aas["ConceptDescription"]))
        self._abstract_classes_to_rdf(obj, subject)
        if obj.is_case_of:
            for reference in obj.is_case_of:
                self._reference_to_rdf(reference, subject, self.aas["ConceptDescription/isCaseOf"])

    def _embedded_data_specification_to_rdf(self, obj: model.EmbeddedDataSpecification, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.EmbeddedDataSpecification` to
        to a joint rdflib Graph object.

        :param obj: Object of class :class:`~basyx.aas.model.base.EmbeddedDataSpecification`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        embedded_data_specification = BNode()
        self.graph.add((parent, self.aas["HasDataSpecification/embeddedDataSpecifications"], embedded_data_specification))
        self.graph.add((embedded_data_specification, RDF.type, self.aas["EmbeddedDataSpecification"]))
        self._abstract_classes_to_rdf(obj, embedded_data_specification)
        self._reference_to_rdf(obj.data_specification, embedded_data_specification, self.aas["EmbeddedDataSpecification/dataSpecification"])
        self._data_specification_content_to_rdf(obj.data_specification_content, embedded_data_specification)

    def _data_specification_content_to_rdf(self, obj: model.DataSpecificationContent, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.DataSpecificationContent` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.DataSpecificationContent`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        data_specification_content = BNode()
        self.graph.add((parent, self.aas["EmbeddedDataSpecification/dataSpecificationContent"], data_specification_content))
        if isinstance(obj, model.DataSpecificationIEC61360):
            self._data_specification_iec61360_to_rdf(obj, data_specification_content)
        else:
            raise TypeError(f"Serialization of {obj.__class__} to a joint rdflib Graph object is not supported!")

    def _data_specification_iec61360_to_rdf(self, obj: model.DataSpecificationIEC61360, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.DataSpecificationIEC61360` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.DataSpecificationIEC61360`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode``
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["DataSpecificationIec61360"]))
        self._abstract_classes_to_rdf(obj, parent)
        self._lang_string_set_to_rdf(obj.preferred_name, parent, self.aas["DataSpecificationIec61360/preferredName"])
        if obj.short_name is not None:
            self._lang_string_set_to_rdf(obj.short_name, parent, self.aas["DataSpecificationIec61360/shortName"])
        if obj.unit is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/unit"], Literal(obj.unit, datatype=XSD.string)))
        if obj.unit_id is not None:
            self._reference_to_rdf(obj.unit_id, parent, self.aas["DataSpecificationIec61360/unitId"])
        if obj.source_of_definition is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/sourceOfDefinition"], Literal(obj.source_of_definition, datatype=XSD.string)))
        if obj.symbol is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/symbol"], Literal(obj.symbol, datatype=XSD.string)))
        if obj.data_type is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/dataType"], self.aas[f"DataSpecificationIec61360/{_generic.IEC61360_DATA_TYPES[obj.data_type]}"]))
        if obj.definition is not None:
            self._lang_string_set_to_rdf(obj.definition, parent, self.aas["DataSpecificationIec61360/definition"])
        if obj.value_format is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/valueFormat"], Literal(obj.value_format, datatype=XSD.string)))
        # # this can be either None or an empty set, both of which are equivalent to the bool false
        # # thus we don't check 'is not None' for this property
        if obj.value_list:
            self._value_list_to_rdf(obj.value_list, parent, self.aas["HasDataSpecification/valueList"])
        if obj.value is not None:
            self.graph.add((parent, self.aas["DataSpecificationIec61360/value"], Literal(obj.value, datatype=XSD.string)))
        if obj.level_types:
            level_type_node = BNode()
            self.graph.add((parent, self.aas["DataSpecificationIec61360/levelType"], level_type_node))
            self.graph.add((level_type_node, RDF.type, self.aas["LevelType"]))
            for k, v in _generic.IEC61360_LEVEL_TYPES.items():
                self.graph.add((level_type_node, self.aas[f"LevelType/{v}"], Literal(self._boolean_to_rdf(k in obj.level_types), datatype=XSD.boolean)))

    def _asset_administration_shell_to_rdf(self, obj: model.AssetAdministrationShell) -> None:
        """
        serialization of an object from class :class:`~basyx.aas.model.aas.AssetAdministrationShell`
        to a joint rdflib Graph object

        :param obj: object of class AssetAdministrationShell
        :return: None
        """
        subject = URIRef(obj.id)
        self.graph.add((subject, RDF.type, self.aas["AssetAdministrationShell"]))
        self._abstract_classes_to_rdf(obj, subject)
        if obj.derived_from:
            self._reference_to_rdf(obj.derived_from, subject, self.aas["AssetAdministrationShell/derivedFrom"])
        if obj.asset_information:
            self._asset_information_to_rdf(obj.asset_information, subject)
        if obj.submodel:
            for reference in obj.submodel:
                self._reference_to_rdf(reference, subject, self.aas["AssetAdministrationShell/submodels"])

    # #################################################################
    # transformation functions to serialize classes from model.submodel
    # #################################################################

    def _submodel_element_to_rdf(self, obj: model.SubmodelElement, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.SubmodelElement` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.SubmodelElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        submodel_element = BNode()
        self.graph.add((parent, objectProperty, submodel_element))
        if isinstance(obj, model.DataElement):
            self._data_element_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.BasicEventElement):
            self._basic_event_element_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.Capability):
            self._capability_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.Entity):
            self._entity_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.Operation):
            self._operation_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.AnnotatedRelationshipElement):
            self._annotated_relationship_element_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.RelationshipElement):
            self._relationship_element_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.SubmodelElementCollection):
            self._submodel_element_collection_to_rdf(obj, submodel_element)
        elif isinstance(obj, model.SubmodelElementList):
            self._submodel_element_list_to_rdf(obj, submodel_element)
        else:
            raise AssertionError(f"Type {obj.__class__.__name__} is not yet supported by the RDF serialization!")

    def _data_element_to_rdf(self, obj: model.DataElement, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.DataElement` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.DataElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        if isinstance(obj, model.MultiLanguageProperty):
            self._multi_language_property_to_rdf(obj, parent)
        elif isinstance(obj, model.Property):
            self._property_to_rdf(obj, parent)
        elif isinstance(obj, model.Range):
            self._range_to_rdf(obj, parent)
        elif isinstance(obj, model.Blob):
            self._blob_to_rdf(obj, parent)
        elif isinstance(obj, model.File):
            self._file_to_rdf(obj, parent)
        elif isinstance(obj, model.ReferenceElement):
            self._reference_element_to_rdf(obj, parent)
        else:
            raise AssertionError(f"Type {obj.__class__.__name__} is not yet supported by the XML serialization!")

    def _submodel_to_rdf(self, obj: model.Submodel) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Submodel` to
        to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Submodel`
        :return: None
        """
        subject = URIRef(obj.id)
        self.graph.add((subject, RDF.type, self.aas["Submodel"]))
        self._abstract_classes_to_rdf(obj, subject)
        if obj.submodel_element:
            for submodel_element in obj.submodel_element:
                self._submodel_element_to_rdf(submodel_element, subject, self.aas["Submodel/submodelElements"])

    def _property_to_rdf(self, obj: model.Property, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Property` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Property`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Property"]))
        self._abstract_classes_to_rdf(obj, parent)
        self.graph.add((parent, self.aas["Property/valueType"], self.aas[f"DataTypeDefXsd/{model.datatypes.XSD_TYPE_NAMES[obj.value_type]}"]))
        if obj.value is not None:
            self._value_to_rdf(obj.value, obj.value_type, parent, self.aas["Property/value"])
        if obj.value_id:
            self._reference_to_rdf(obj.value_id, parent, self.aas["Property/valueId"])

    def _multi_language_property_to_rdf(self, obj: model.MultiLanguageProperty, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.MultiLanguageProperty`
        to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.MultiLanguageProperty`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["MultiLanguageProperty"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.value:
            self._lang_string_set_to_rdf(obj.value, parent, self.aas["MultiLanguageProperty/value"])
        if obj.value_id:
            self._reference_to_rdf(obj.value_id, parent, self.aas["MultiLanguageProperty/valueId"])

    def _range_to_rdf(self, obj: model.Range, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Range` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Range`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Range"]))
        self._abstract_classes_to_rdf(obj, parent)
        self.graph.add((parent, self.aas["Range/valueType"], self.aas[f"DataTypeDefXsd/{model.datatypes.XSD_TYPE_NAMES[obj.value_type]}"]))
        if obj.min is not None:
            self._value_to_rdf(obj.min, obj.value_type, parent, self.aas["Range/min"])
        if obj.max is not None:
            self._value_to_rdf(obj.min, obj.value_type, parent, self.aas["Range/max"])

    def _blob_to_rdf(self, obj: model.Blob, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Blob` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Blob`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Blob"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.value:
            self.graph.add((parent, self.aas["Blob/value"], Literal(base64.b64encode(obj.value).decode(), datatype=XSD.base64Binary)))
        self.graph.add((parent, self.aas["Blob/contentType"], Literal(str(obj.content_type), datatype=XSD.string)))

    def _file_to_rdf(self, obj: model.File, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.File` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.File`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["File"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.value:
            self.graph.add((parent, self.aas["File/value"], Literal(str(obj.value), datatype=XSD.string)))
        self.graph.add((parent, self.aas["File/contentType"], Literal(str(obj.content_type), datatype=XSD.string)))

    def _resource_to_rdf(self, obj: model.Resource, parent: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.base.Resource` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.base.Resource`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        ressource = BNode()
        self.graph.add((parent, objectProperty, ressource))
        self.graph.add((ressource, RDF.type, self.aas["Resource"]))
        self._abstract_classes_to_rdf(obj, ressource)
        self.graph.add((ressource, self.aas["Resource/path"], Literal(str(obj.path), datatype=XSD.string)))
        if obj.content_type:
            self.graph.add((ressource, self.aas["Ressource/contentType"], Literal(str(obj.content_type), datatype=XSD.string)))

    def _reference_element_to_rdf(self, obj: model.ReferenceElement, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.ReferenceElement`
        to a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.ReferenceElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["ReferenceElement"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.value:
            self._reference_to_rdf(obj.value, parent, self.aas["ReferenceElement/value"])

    def _submodel_element_collection_to_rdf(self, obj: model.SubmodelElementCollection, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.SubmodelElementCollection` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.SubmodelElementCollection`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["SubmodelElementCollection"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.value:
            for submodel_element in obj.value:
                self._submodel_element_to_rdf(submodel_element, parent, self.aas["SubmodelElementCollection/value"])

    def _submodel_element_list_to_rdf(self, obj: model.SubmodelElementList, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.SubmodelElementList` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.SubmodelElementList`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["SubmodelElementList"]))
        self._abstract_classes_to_rdf(obj, parent)
        self.graph.add((parent, self.aas["SubmodelElementList/orderRelevant"], Literal(self._boolean_to_rdf(obj.order_relevant), datatype=XSD.boolean)))
        if obj.semantic_id_list_element is not None:
            self._reference_to_rdf(obj.semantic_id_list_element, parent, self.aas["SubmodelElementList/semanticIdListElement"])
        self.graph.add((parent, self.aas["SubmodelElementList/typeValueListElement"],
                        self.aas[f"AasSubmodelElements/{_generic.KEY_TYPES[model.KEY_TYPES_CLASSES[obj.type_value_list_element]]}"]))
        if obj.value_type_list_element is not None:
            self.graph.add((parent, self.aas["SubmodelElementList/valueTypeListElement"],
                            self.aas[f"DataTypeDefXsd/{model.datatypes.XSD_TYPE_NAMES[obj.value_type_list_element]}"]))
        if len(obj.value) > 0:
            for submodel_element in obj.value:
                self._submodel_element_to_rdf(submodel_element, parent, self.aas["SubmodelElementList/value"])

    def _relationship_element_to_rdf(self, obj: model.RelationshipElement, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.RelationshipElement` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.RelationshipElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["RelationshipElement"]))
        self._abstract_classes_to_rdf(obj, parent)
        self._reference_to_rdf(obj.first, parent, self.aas["RelationshipElement/first"])
        self._reference_to_rdf(obj.second, parent, self.aas["RelationshipElement/second"])

    def _annotated_relationship_element_to_rdf(self, obj: model.AnnotatedRelationshipElement, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.AnnotatedRelationshipElement` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.AnnotatedRelationshipElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["RelationshipElement"]))
        self._abstract_classes_to_rdf(obj, parent)
        self._reference_to_rdf(obj.first, parent, self.aas["RelationshipElement/first"])
        self._reference_to_rdf(obj.second, parent, self.aas["RelationshipElement/second"])
        if obj.annotation:
            for data_element in obj.annotation:
                self._submodel_element_to_rdf(data_element, parent, self.aas["AnnotatedRelationshipElement/annotations"])

    def _operation_variable_to_rdf(self, obj: model.SubmodelElement, operation: Union[URIRef, BNode], objectProperty: URIRef) -> None:
        """
        Serialization of :class:`~basyx.aas.model.submodel.SubmodelElement` to a joint rdflib Graph object.
        Since we don't implement the ``OperationVariable`` class, which is just a wrapper for a single
        :class:`~basyx.aas.model.submodel.SubmodelElement`, elements are serialized as the ``aas:value`` child of an
        ``aas:operationVariable`` element.

        :param obj: Object of class :class:`~basyx.aas.model.submodel.SubmodelElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :param objectProperty: The object property that is used to connect to from the parent, :class:`~rdflib.term.URIRef`
        :return: None
        """
        operation_variable = BNode()
        self.graph.add((operation, objectProperty, operation_variable))
        self.graph.add((operation_variable, RDF.type, self.aas["OperationVariable"]))
        self._submodel_element_to_rdf(obj, operation_variable, self.aas["OperationVariable/value"])

    def _operation_to_rdf(self, obj: model.Operation, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Operation` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Operation`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Operation"]))
        self._abstract_classes_to_rdf(obj, parent)
        for objectProperty, nss in (
                (self.aas["Operation/inputVariables"], obj.input_variable),
                (self.aas["Operation/outputVariables"], obj.output_variable),
                (self.aas["Operation/inoutputVariables"], obj.in_output_variable)):
            if nss:
                for submodel_element in nss:
                    self._operation_variable_to_rdf(submodel_element, parent, objectProperty)

    def _capability_to_rdf(self, obj: model.Capability, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Capability` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Capability`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Capability"]))
        self._abstract_classes_to_rdf(obj, parent)

    def _entity_to_rdf(self, obj: model.Entity, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.Entity` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.Entity`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["Entity"]))
        self._abstract_classes_to_rdf(obj, parent)
        if obj.statement:
            for statement in obj.statement:
                self._submodel_element_to_rdf(statement, parent, self.aas["Entity/statements"])
        self.graph.add((parent, self.aas["Entity/entityType"], self.aas[f"EntityType/{_generic.ENTITY_TYPES[obj.entity_type]}"]))
        if obj.global_asset_id:
            self.graph.add((parent, self.aas["Entity/globalAssetId"], Literal(str(obj.global_asset_id), datatype=XSD.string)))
        if obj.specific_asset_id:
            for specific_asset_id in obj.specific_asset_id:
                self._specific_asset_id_to_rdf(specific_asset_id, parent, self.aas["Entity/specificAssetIds"])

    def _basic_event_element_to_rdf(self, obj: model.BasicEventElement, parent: Union[URIRef, BNode]) -> None:
        """
        Serialization of objects of class :class:`~basyx.aas.model.submodel.BasicEventElement` to
        a joint rdflib Graph object

        :param obj: Object of class :class:`~basyx.aas.model.submodel.BasicEventElement`
        :param parent: The parent node. Can either be :class:`~rdflib.term.URIRef` or :class:`~rdflib.term.BNode`
        :return: None
        """
        self.graph.add((parent, RDF.type, self.aas["BasicEventElement"]))
        self._abstract_classes_to_rdf(obj, parent)
        self._reference_to_rdf(obj.observed, parent, self.aas["BasicEventElement/observed"])
        self.graph.add((parent, self.aas["BasicEventElement/direction"], self.aas[f"Direction/{_generic.DIRECTION[obj.direction]}"]))
        self.graph.add((parent, self.aas["BasicEventElement/state"], self.aas[f"StateOfEvent/{_generic.STATE_OF_EVENT[obj.state]}"]))
        if obj.message_topic:
            self.graph.add((parent, self.aas["BasicEventElement/messageTopic"], Literal(str(obj.message_topic), datatype=XSD.string)))
        if obj.message_broker:
            self._reference_to_rdf(obj.message_broker, parent, self.aas["BasicEventElement/messageBroker"])
        if obj.last_update is not None:
            self.graph.add((parent, self.aas["BasicEventElement/lastUpdate"], Literal(model.datatypes.xsd_repr(obj.last_update), datatype=XSD.string)))
        if obj.min_interval is not None:
            self.graph.add((parent, self.aas["BasicEventElement/minInterval"], Literal(model.datatypes.xsd_repr(obj.min_interval), datatype=XSD.string)))
        if obj.max_interval is not None:
            self.graph.add((parent, self.aas["BasicEventElement/maxInterval"], Literal(model.datatypes.xsd_repr(obj.max_interval), datatype=XSD.string)))


# ##############################################################
# general functions
# ##############################################################


def object_store_to_rdf(data: model.AbstractObjectStore) -> str:
    """
    Serialize a set of AAS objects to an Asset Administration Shell as :class:`~rdflib.Graph`.
    This function is used internally by :meth:`write_aas_rdf_file` and shouldn't be
    called directly for most use-cases.

    :param data: :class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` which contains different objects of
                 the AAS meta model which should be serialized to an RDF file
    """
    encoder = AASToRDFEncoder()
    encoder.object_store_to_rdflib_graph(data)
    return encoder.graph.serialize(format="turtle")


def write_aas_rdf_file(file: _generic.PathOrIOGraph,
                       data: model.AbstractObjectStore,
                       **kwargs) -> None:
    """
    Write a set of AAS objects to an Asset Administration Shell RDF file according to 'Details of the Asset
    Administration Shell', chapter 7.5.

    :param file: A filename or file-like object to write the RDF-serialized data to
    :param data: :class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` which contains different objects of
                 the AAS meta model which should be serialized to an XML file
    :param kwargs: Additional keyword arguments to be passed to :meth:`~rdflib.Graph.serialize`
    """
    encoder = AASToRDFEncoder()
    encoder.object_store_to_rdflib_graph(data)
    # encoder.graph.serialize("test_output.ttl", format="turtle")
    encoder.graph.serialize(destination=file, format="turtle", **kwargs)
