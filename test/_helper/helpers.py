# Copyright 2019 PyI40AAS Contributors
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
Tests for the example aas

Functions to test if an object is the same to the example aas from example_create_aas.py
"""
import unittest
from typing import Set, Optional
from aas import model


def find_Reference_in_set(reference: model.Reference, set_to_search: Set) -> bool:
    for reference_to_find in set_to_search:
        if reference_to_find == reference:
            return True
    else:
        return False


class ExampleHelper(unittest.TestCase):
    def assert_example_asset_identification_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('http://acplt.org/Submodels/Assets/TestAsset/Identification', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(2, len(submodel.submodel_element))
        self.assertEqual('Identification', submodel.id_short)
        self.assertIsNone(submodel.category)
        self.assertEqual({'en-us': 'An example asset identification submodel for the test application',
                          'de': 'Ein Beispiel-Identifikations-Submodel für eine Test-Anwendung'}, submodel.description)
        self.assertIsNone(submodel.parent)
        self.assertEqual('0.9', submodel.administration.version)  # type: ignore
        self.assertEqual('0', submodel.administration.revision)  # type: ignore
        self.assertEqual(1, len(submodel.data_specification))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/DataSpecifications/Submodels/AssetIdentification',
                              id_type=model.KeyType.IRDI),)), submodel.data_specification))
        self.assertEqual(submodel.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='http://acplt.org/SubmodelTemplates/AssetIdentification',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(submodel.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, submodel.kind)

        # test attributes of property ManufacturerName
        manufacturer_name: model.Property = submodel.get_referable('ManufacturerName')  # type: ignore
        self.assertIsInstance(manufacturer_name, model.Property)
        self.assertEqual('ManufacturerName', manufacturer_name.id_short)
        self.assertEqual('string', manufacturer_name.value_type)
        self.assertEqual('ACPLT', manufacturer_name.value)
        self.assertEqual(manufacturer_name.value_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ValueId/ExampleValueId',
                      id_type=model.KeyType.IRDI),)))
        self.assertIsNone(manufacturer_name.category)
        self.assertEqual({'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                                   'responsible for the design, production, packaging and labeling of a product in '
                                   'respect to its being brought into circulation.',
                          'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                                'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf '
                                'das \'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
                         manufacturer_name.description)
        self.assertIs(manufacturer_name.parent, submodel)
        self.assertEqual(0, len(manufacturer_name.data_specification))
        self.assertEqual(manufacturer_name.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='0173-1#02-AAO677#002',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(2, len(manufacturer_name.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, manufacturer_name.kind)

        # Test attributes of property qualifier
        qualifier: model.Qualifier
        for qualifier in manufacturer_name.qualifier:  # type: ignore
            if qualifier.type_ == 'http://acplt.org/Qualifier/ExampleQualifier':
                self.assertIsInstance(qualifier, model.Qualifier)
                self.assertEqual('http://acplt.org/Qualifier/ExampleQualifier', qualifier.type_)
                self.assertEqual('string', qualifier.value_type)
                self.assertEqual('100', qualifier.value)
                self.assertEqual(qualifier.value_id, model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/ValueId/ExampleValueId',
                              id_type=model.KeyType.IRDI),)))
            elif qualifier.type_ == 'http://acplt.org/Qualifier/ExampleQualifier2':
                self.assertIsInstance(qualifier, model.Qualifier)
                self.assertEqual('http://acplt.org/Qualifier/ExampleQualifier2', qualifier.type_)
                self.assertEqual('string', qualifier.value_type)
                self.assertEqual('50', qualifier.value)
                self.assertEqual(qualifier.value_id, model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/ValueId/ExampleValueId',
                              id_type=model.KeyType.IRDI),)))
            else:
                raise KeyError()

        instance_id: model.Property = submodel.get_referable('InstanceId')  # type: ignore
        self.assertIsInstance(instance_id, model.Property)
        self.assertEqual(1, len(instance_id.qualifier))
        # Test attributes of property qualifier
        formula: model.Formula
        for formula in instance_id.qualifier:  # type: ignore
            self.assertIsInstance(formula, model.Formula)
            self.assertEqual(1, len(formula.depends_on))
            for reference in formula.depends_on:
                self.assertEqual(reference, model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/Formula/ExampleFormula',
                              id_type=model.KeyType.IRDI),)))

    def assert_example_bill_of_material_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('http://acplt.org/Submodels/Assets/TestAsset/BillOfMaterial', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(2, len(submodel.submodel_element))
        self.assertEqual('BillOfMaterial', submodel.id_short)
        self.assertIsNone(submodel.category)
        self.assertEqual({'en-us': 'An example bill of material submodel for the test application',
                          'de': 'Ein Beispiel-BillofMaterial-Submodel für eine Test-Anwendung'}, submodel.description)
        self.assertIsNone(submodel.parent)
        self.assertEqual('0.9', submodel.administration.version)  # type: ignore
        self.assertIsNone(submodel.administration.revision)  # type: ignore
        self.assertEqual(1, len(submodel.data_specification))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.ASSET,
                              local=False,
                              value='http://acplt.org/DataSpecifications/Submodels/BillOfMaterial',
                              id_type=model.KeyType.IRDI),)), submodel.data_specification))
        self.assertEqual(submodel.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='http://acplt.org/SubmodelTemplates/BillOfMaterial',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(submodel.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, submodel.kind)

        # test attributes of entity ExampleEntity
        example_entity: model.Entity = submodel.get_referable('ExampleEntity')  # type: ignore
        self.assertIsInstance(example_entity, model.Entity)
        self.assertEqual('ExampleEntity', example_entity.id_short)
        self.assertEqual(model.EntityType.CO_MANAGED_ENTITY, example_entity.entity_type)
        self.assertEqual(2, len(example_entity.statement))
        self.assertIsNone(example_entity.category)
        self.assertEqual({'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                                   'responsible for the design, production, packaging and labeling of a product in '
                                   'respect to its being brought into circulation.',
                          'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                                'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                                '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
                         example_entity.description)
        self.assertIs(example_entity.parent, submodel)
        self.assertEqual(0, len(example_entity.data_specification))
        self.assertEqual(example_entity.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://opcfoundation.org/UA/DI/1.1/DeviceType/Serialnumber',
                      id_type=model.KeyType.IRI),)))
        self.assertEqual(0, len(example_entity.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_entity.kind)

        # Test attributes of property ExampleProperty in statements
        example_property: model.Property = example_entity.statement.get_referable('ExampleProperty')  # type: ignore
        self.assertIsInstance(example_property, model.Property)
        self.assertEqual('ExampleProperty', example_property.id_short)
        self.assertEqual('string', example_property.value_type)
        self.assertEqual('exampleValue', example_property.value)
        self.assertEqual(example_property.value_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ValueId/ExampleValueId',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual('CONSTANT', example_property.category)
        self.assertEqual({'en-us': 'Example Property object', 'de': 'Beispiel Property Element'},
                         example_property.description)
        self.assertIs(example_property.parent, example_entity)
        self.assertEqual(0, len(example_property.data_specification))
        self.assertEqual(example_property.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Properties/ExampleProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_property.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_property.kind)

        # Test attributes of property ExampleProperty2 in statements
        example_property2: model.Property = example_entity.statement.get_referable('ExampleProperty2')  # type: ignore
        self.assertIsInstance(example_property2, model.Property)
        self.assertEqual('ExampleProperty2', example_property2.id_short)
        self.assertEqual('string', example_property2.value_type)
        self.assertEqual('exampleValue2', example_property2.value)
        self.assertEqual(example_property2.value_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ValueId/ExampleValueId',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual('CONSTANT', example_property2.category)
        self.assertEqual({'en-us': 'Example Property object', 'de': 'Beispiel Property Element'},
                         example_property2.description)
        self.assertIs(example_property2.parent, example_entity)
        self.assertEqual(0, len(example_property2.data_specification))
        self.assertEqual(example_property2.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Properties/ExampleProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_property2.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_property2.kind)

        # test attributes of entity ExampleEntity2
        example_entity2: model.Entity = submodel.get_referable('ExampleEntity2')  # type: ignore
        self.assertIsInstance(example_entity2, model.Entity)
        self.assertEqual('ExampleEntity2', example_entity2.id_short)
        self.assertEqual(model.EntityType.SELF_MANAGED_ENTITY, example_entity2.entity_type)
        self.assertEqual(0, len(example_entity2.statement))
        self.assertEqual(example_entity2.asset, model.Reference((
            model.Key(type_=model.KeyElements.ASSET,
                      local=False,
                      value='https://acplt.org/Test_Asset2',
                      id_type=model.KeyType.IRDI),)))
        self.assertIsNone(example_entity2.category)
        self.assertEqual({'en-us': 'Legally valid designation of the natural or judicial person which is directly '
                                   'responsible for the design, production, packaging and labeling of a product in '
                                   'respect to its being brought into circulation.',
                          'de': 'Bezeichnung für eine natürliche oder juristische Person, die für die Auslegung, '
                                'Herstellung und Verpackung sowie die Etikettierung eines Produkts im Hinblick auf das '
                                '\'Inverkehrbringen\' im eigenen Namen verantwortlich ist'},
                         example_entity2.description)
        self.assertIs(example_entity2.parent, submodel)
        self.assertEqual(0, len(example_entity2.data_specification))
        self.assertEqual(example_entity2.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://opcfoundation.org/UA/DI/1.1/DeviceType/Serialnumber',
                      id_type=model.KeyType.IRI),)))
        self.assertEqual(0, len(example_entity2.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_entity2.kind)

    def assert_example_asset(self, asset: model.Asset) -> None:
        # Test attributes of Asset
        self.assertEqual(model.AssetKind.INSTANCE, asset.kind)
        self.assertEqual('https://acplt.org/Test_Asset', asset.identification.id)
        self.assertEqual(model.IdentifierType.IRI, asset.identification.id_type)
        self.assertEqual('Test_Asset', asset.id_short)
        self.assertIsNone(asset.category)
        self.assertEqual({'en-us': 'An example asset for the test application',
                          'de': 'Ein Beispiel-Asset für eine Test-Anwendung'}, asset.description)
        self.assertIsNone(asset.parent)
        self.assertEqual('0.9', asset.administration.version)  # type: ignore
        self.assertEqual('0', asset.administration.revision)  # type: ignore
        self.assertEqual(1, len(asset.data_specification))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/DataSpecifications/AssetTypes/TestAsset',
                              id_type=model.KeyType.IRDI),)), asset.data_specification))
        self.assertEqual(asset.asset_identification_model, model.Reference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='http://acplt.org/Submodels/Assets/TestAsset/Identification',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(asset.bill_of_material, model.Reference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='http://acplt.org/Submodels/Assets/TestAsset/BillOfMaterial',
                      id_type=model.KeyType.IRDI),)))

    def assert_example_concept_description(self, concept_description: model.ConceptDescription) -> None:
        # Test attributes of ConceptDescription
        self.assertEqual('https://acplt.org/Test_ConceptDescription', concept_description.identification.id)
        self.assertEqual(model.IdentifierType.IRI, concept_description.identification.id_type)
        self.assertEqual(1, len(concept_description.is_case_of))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/DataSpecifications/ConceptDescriptions/TestConceptDescription',
                              id_type=model.KeyType.IRDI),)), concept_description.is_case_of))
        self.assertEqual('TestConceptDescription', concept_description.id_short)
        self.assertIsNone(concept_description.category)
        self.assertEqual({'en-us': 'An example concept description  for the test application',
                          'de': 'Ein Beispiel-ConceptDescription für eine Test-Anwendung'},
                         concept_description.description)
        self.assertIsNone(concept_description.parent)
        self.assertEqual('0.9', concept_description.administration.version)  # type: ignore
        self.assertEqual('0', concept_description.administration.revision)  # type: ignore
        self.assertEqual(1, len(concept_description.data_specification))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/DataSpecifications/ConceptDescriptions/TestConceptDescription',
                              id_type=model.KeyType.IRDI),)), concept_description.data_specification))

    def assert_example_concept_dictionary(self, concept_dictionary: model.ConceptDictionary,
                                          shell: Optional[model.AssetAdministrationShell] = None) -> None:
        # Test attributes of ConceptDictionary
        self.assertEqual('TestConceptDictionary', concept_dictionary.id_short)
        self.assertIsNone(concept_dictionary.category)
        self.assertEqual({'en-us': 'An example concept dictionary for the test application',
                          'de': 'Ein Beispiel-ConceptDictionary für eine Test-Anwendung'},
                         concept_dictionary.description)
        if shell:
            self.assertEqual(concept_dictionary.parent, shell)
        else:
            self.assertIsNone(concept_dictionary.parent)
        self.assertEqual(True, find_Reference_in_set(model.AASReference((
            model.Key(type_=model.KeyElements.CONCEPT_DESCRIPTION,
                      local=False,
                      value='https://acplt.org/Test_ConceptDescription',
                      id_type=model.KeyType.IRDI),), model.ConceptDescription),
            concept_dictionary.concept_description))

    def assert_example_asset_administration_shell(self, shell: model.AssetAdministrationShell) -> None:
        # Test attributes of AssetAdministrationShell
        self.assertEqual(shell.asset, model.AASReference((
            model.Key(type_=model.KeyElements.ASSET,
                      local=False,
                      value='https://acplt.org/Test_Asset',
                      id_type=model.KeyType.IRDI),),
            model.Asset))
        self.assertEqual('https://acplt.org/Test_AssetAdministrationShell', shell.identification.id)
        self.assertEqual(model.IdentifierType.IRI, shell.identification.id_type)
        self.assertEqual('TestAssetAdministrationShell', shell.id_short)
        self.assertIsNone(shell.category)
        self.assertEqual({'en-us': 'An Example Asset Administration Shell for the test application',
                          'de': 'Ein Beispiel-Verwaltungsschale für eine Test-Anwendung'}, shell.description)
        self.assertIsNone(shell.parent)
        self.assertEqual('0.9', shell.administration.version)  # type: ignore
        self.assertEqual('0', shell.administration.revision)  # type: ignore
        self.assertEqual(0, len(shell.data_specification))
        self.assertIsNone(shell.security_)
        self.assertEqual(1, len(shell.submodel_))
        self.assertEqual(True, find_Reference_in_set(model.AASReference((
            model.Key(type_=model.KeyElements.SUBMODEL,
                      local=False,
                      value='https://acplt.org/Test_Submodel',
                      id_type=model.KeyType.IRDI),),
            model.Submodel),
            shell.submodel_))
        self.assertEqual(1, len(shell.concept_dictionary))
        cd: model.ConceptDictionary = shell.concept_dictionary.get_referable('TestConceptDictionary')  # type: ignore
        self.assert_example_concept_dictionary(cd, shell)
        self.assertEqual(0, len(shell.view))
        self.assertEqual(shell.derived_from, model.AASReference((
             model.Key(type_=model.KeyElements.ASSET_ADMINISTRATION_SHELL,
                       local=False,
                       value='https://acplt.org/TestAssetAdministrationShell2',
                       id_type=model.KeyType.IRDI),),
             model.AssetAdministrationShell))

    def assert_example_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('https://acplt.org/Test_Submodel', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(7, len(submodel.submodel_element))
        self.assertEqual('TestSubmodel', submodel.id_short)
        self.assertIsNone(submodel.category)
        self.assertEqual({'en-us': 'An example submodel for the test application',
                          'de': 'Ein Beispiel-Teilmodell für eine Test-Anwendung'}, submodel.description)
        self.assertIsNone(submodel.parent)
        self.assertEqual('0.9', submodel.administration.version)  # type: ignore
        self.assertEqual('0', submodel.administration.revision)  # type: ignore
        self.assertEqual(1, len(submodel.data_specification))
        self.assertEqual(True, find_Reference_in_set(model.Reference((
                    model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                              local=False,
                              value='http://acplt.org/DataSpecifications/Submodels/TestSubmodel',
                              id_type=model.KeyType.IRDI),)), submodel.data_specification))
        self.assertEqual(submodel.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelTemplates/ExampleSubmodel',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(submodel.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, submodel.kind)

        # test attributes of relationship element ExampleRelationshipElement
        rel_element: model.RelationshipElement = submodel.get_referable('ExampleRelationshipElement')  # type: ignore
        self.assertIsInstance(rel_element, model.RelationshipElement)
        self.assertEqual('ExampleRelationshipElement', rel_element.id_short)
        self.assertEqual(rel_element.first, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual(rel_element.second, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual('PARAMETER', rel_element.category)
        self.assertEqual({'en-us': 'Example RelationshipElement object', 'de': 'Beispiel RelationshipElement Element'},
                         rel_element.description)
        self.assertIs(rel_element.parent, submodel)
        self.assertEqual(0, len(rel_element.data_specification))
        self.assertEqual(rel_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/RelationshipElements/ExampleRelationshipElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(rel_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, rel_element.kind)

        # test attributes of annotated relationship element ExampleAnnotatedRelationshipElement
        rel_element_annotated: model.AnnotatedRelationshipElement = \
            submodel.get_referable('ExampleAnnotatedRelationshipElement')  # type: ignore
        self.assertIsInstance(rel_element_annotated, model.RelationshipElement)
        self.assertEqual('ExampleAnnotatedRelationshipElement', rel_element_annotated.id_short)
        self.assertEqual(rel_element_annotated.first, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual(rel_element_annotated.second, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual(True, find_Reference_in_set(model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property),
            rel_element_annotated.annotation))
        self.assertEqual('PARAMETER', rel_element_annotated.category)
        self.assertEqual({'en-us': 'Example AnnotatedRelationshipElement object',
                          'de': 'Beispiel AnnotatedRelationshipElement Element'}, rel_element_annotated.description)
        self.assertIs(rel_element_annotated.parent, submodel)
        self.assertEqual(0, len(rel_element_annotated.data_specification))
        self.assertEqual(rel_element_annotated.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/RelationshipElements/ExampleAnnotatedRelationshipElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(rel_element_annotated.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, rel_element_annotated.kind)

        # test attributes of operation element ExampleOperation
        operation_element: model.Operation = submodel.get_referable('ExampleOperation')  # type: ignore
        self.assertIsInstance(operation_element, model.Operation)
        self.assertEqual('ExampleOperation', operation_element.id_short)
        self.assertEqual(1, len(operation_element.input_variable))
        self.assertEqual(1, len(operation_element.output_variable))
        self.assertEqual(1, len(operation_element.in_output_variable))
        self.assertEqual('PARAMETER', operation_element.category)
        self.assertEqual({'en-us': 'Example Operation object',
                          'de': 'Beispiel Operation Element'}, operation_element.description)
        self.assertIs(operation_element.parent, submodel)
        self.assertEqual(0, len(operation_element.data_specification))
        self.assertEqual(operation_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Operations/ExampleOperation',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(operation_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, operation_element.kind)

        # test attributes of capability element ExampleCapability
        capability_element: model.Capability = submodel.get_referable('ExampleCapability')  # type: ignore
        self.assertIsInstance(capability_element, model.Capability)
        self.assertEqual('ExampleCapability', capability_element.id_short)
        self.assertEqual('PARAMETER', capability_element.category)
        self.assertEqual({'en-us': 'Example Capability object',
                          'de': 'Beispiel Capability Element'}, capability_element.description)
        self.assertIs(capability_element.parent, submodel)
        self.assertEqual(0, len(capability_element.data_specification))
        self.assertEqual(capability_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Capabilities/ExampleCapability',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(capability_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, capability_element.kind)

        # test attributes of basic event element ExampleBasicEvent
        basic_event_element: model.BasicEvent = submodel.get_referable('ExampleBasicEvent')  # type: ignore
        self.assertIsInstance(basic_event_element, model.BasicEvent)
        self.assertEqual('ExampleBasicEvent', basic_event_element.id_short)
        self.assertEqual(basic_event_element.observed, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual('PARAMETER', basic_event_element.category)
        self.assertEqual({'en-us': 'Example BasicEvent object',
                          'de': 'Beispiel BasicEvent Element'}, basic_event_element.description)
        self.assertIs(basic_event_element.parent, submodel)
        self.assertEqual(0, len(basic_event_element.data_specification))
        self.assertEqual(basic_event_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Events/ExampleBasicEvent',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(basic_event_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, basic_event_element.kind)

        # test attributes of ordered collection element ExampleSubmodelCollectionOrdered
        ordered_collection: model.SubmodelElementCollectionOrdered =\
            submodel.get_referable('ExampleSubmodelCollectionOrdered')  # type: ignore
        self.assertIsInstance(ordered_collection, model.SubmodelElementCollectionOrdered)
        self.assertEqual('ExampleSubmodelCollectionOrdered', ordered_collection.id_short)
        self.assertEqual(3, len(ordered_collection.value))
        self.assertEqual('PARAMETER', ordered_collection.category)
        self.assertEqual({'en-us': 'Example SubmodelElementCollectionOrdered object',
                          'de': 'Beispiel SubmodelElementCollectionOrdered Element'}, ordered_collection.description)
        self.assertIs(ordered_collection.parent, submodel)
        self.assertEqual(0, len(ordered_collection.data_specification))
        self.assertEqual(ordered_collection.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelElementCollections/ExampleSubmodelElementCollectionOrdered',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(ordered_collection.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, ordered_collection.kind)

        # test attributes of elements of ExampleSubmodelCollectionOrdered
        # test attributes of property ExampleProperty
        example_property: model.Property = ordered_collection.get_referable('ExampleProperty')  # type: ignore
        self.assertIsInstance(example_property, model.Property)
        self.assertEqual('ExampleProperty', example_property.id_short)
        self.assertEqual('string', example_property.value_type)
        self.assertEqual('exampleValue', example_property.value)
        self.assertEqual(example_property.value_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ValueId/ExampleValueId',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual('CONSTANT', example_property.category)
        self.assertEqual({'en-us': 'Example Property object', 'de': 'Beispiel Property Element'},
                         example_property.description)
        self.assertIs(example_property.parent, ordered_collection)
        self.assertEqual(0, len(example_property.data_specification))
        self.assertEqual(example_property.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Properties/ExampleProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_property.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_property.kind)

        # test attributes of multi language property ExampleMultiLanguageProperty
        example_ml_property: model.MultiLanguageProperty = \
            ordered_collection.get_referable('ExampleMultiLanguageProperty')  # type: ignore
        self.assertIsInstance(example_ml_property, model.MultiLanguageProperty)
        self.assertEqual('ExampleMultiLanguageProperty', example_ml_property.id_short)
        self.assertEqual({'en-us': 'Example value of a MultiLanguageProperty element',
                          'de': 'Beispielswert für ein MulitLanguageProperty-Element'}, example_ml_property.value)
        self.assertEqual(example_ml_property.value_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ValueId/ExampleMultiLanguageValueId',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual('CONSTANT', example_ml_property.category)
        self.assertEqual({'en-us': 'Example MultiLanguageProperty object',
                          'de': 'Beispiel MulitLanguageProperty Element'},
                         example_ml_property.description)
        self.assertIs(example_ml_property.parent, ordered_collection)
        self.assertEqual(0, len(example_ml_property.data_specification))
        self.assertEqual(example_ml_property.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/MultiLanguageProperties/ExampleMultiLanguageProperty',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(example_ml_property.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, example_ml_property.kind)

        # test attributes of range ExampleRange
        range_element: model.Range = ordered_collection.get_referable('ExampleRange')  # type: ignore
        self.assertIsInstance(range_element, model.Range)
        self.assertEqual('ExampleRange', range_element.id_short)
        self.assertEqual('int', range_element.value_type)
        self.assertEqual('0', range_element.min_)
        self.assertEqual('100', range_element.max_)
        self.assertEqual('PARAMETER', range_element.category)
        self.assertEqual({'en-us': 'Example Range object', 'de': 'Beispiel Range Element'},
                         range_element.description)
        self.assertIs(range_element.parent, ordered_collection)
        self.assertEqual(0, len(range_element.data_specification))
        self.assertEqual(range_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Ranges/ExampleRange',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(range_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, range_element.kind)

        # test attributes of unordered collection element ExampleSubmodelCollectionUnordered
        unordered_collection: model.SubmodelElementCollectionUnordered = \
            submodel.get_referable('ExampleSubmodelCollectionUnordered')  # type: ignore
        self.assertIsInstance(unordered_collection, model.SubmodelElementCollectionUnordered)
        self.assertEqual('ExampleSubmodelCollectionUnordered', unordered_collection.id_short)
        self.assertEqual(3, len(unordered_collection.value))
        self.assertEqual('PARAMETER', unordered_collection.category)
        self.assertEqual({'en-us': 'Example SubmodelElementCollectionUnordered object',
                          'de': 'Beispiel SubmodelElementCollectionUnordered Element'},
                         unordered_collection.description)
        self.assertIs(unordered_collection.parent, submodel)
        self.assertEqual(0, len(unordered_collection.data_specification))
        self.assertEqual(unordered_collection.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/SubmodelElementCollections/ExampleSubmodelElementCollectionUnordered',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(unordered_collection.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, unordered_collection.kind)

        # test attributes of blob ExampleBlob
        blob_element: model.Blob = unordered_collection.get_referable('ExampleBlob')  # type: ignore
        self.assertIsInstance(blob_element, model.Blob)
        self.assertEqual('ExampleBlob', blob_element.id_short)
        self.assertEqual('application/pdf', blob_element.mime_type)
        self.assertEqual(bytearray(b'\x01\x02\x03\x04\x05'), blob_element.value)
        self.assertEqual('PARAMETER', blob_element.category)
        self.assertEqual({'en-us': 'Example Blob object', 'de': 'Beispiel Blob Element'},
                         blob_element.description)
        self.assertIs(blob_element.parent, unordered_collection)
        self.assertEqual(0, len(blob_element.data_specification))
        self.assertEqual(blob_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Blobs/ExampleBlob',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(blob_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, blob_element.kind)

        # test attributes of file ExampleFile
        file_element: model.File = unordered_collection.get_referable('ExampleFile')  # type: ignore
        self.assertIsInstance(file_element, model.File)
        self.assertEqual('ExampleFile', file_element.id_short)
        self.assertEqual('application/pdf', file_element.mime_type)
        self.assertEqual('/TestFile.pdf', file_element.value)
        self.assertEqual('PARAMETER', file_element.category)
        self.assertEqual({'en-us': 'Example File object', 'de': 'Beispiel File Element'},
                         file_element.description)
        self.assertIs(file_element.parent, unordered_collection)
        self.assertEqual(0, len(file_element.data_specification))
        self.assertEqual(file_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/Files/ExampleFile',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(file_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, file_element.kind)

        # test attributes of reference element ExampleFile
        ref_element: model.ReferenceElement = \
            unordered_collection.get_referable('ExampleReferenceElement')  # type: ignore
        self.assertIsInstance(ref_element, model.ReferenceElement)
        self.assertEqual('ExampleReferenceElement', ref_element.id_short)
        self.assertEqual(ref_element.value, model.AASReference((
            model.Key(type_=model.KeyElements.PROPERTY,
                      local=True,
                      value='ExampleProperty',
                      id_type=model.KeyType.IDSHORT),),
            model.Property))
        self.assertEqual('PARAMETER', ref_element.category)
        self.assertEqual({'en-us': 'Example Reference Element object', 'de': 'Beispiel Reference Element Element'},
                         ref_element.description)
        self.assertIs(ref_element.parent, unordered_collection)
        self.assertEqual(0, len(ref_element.data_specification))
        self.assertEqual(ref_element.semantic_id, model.Reference((
            model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                      local=False,
                      value='http://acplt.org/ReferenceElements/ExampleReferenceElement',
                      id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, len(ref_element.qualifier))
        self.assertEqual(model.ModelingKind.INSTANCE, ref_element.kind)

    def assert_full_example(self, obj_store: model.DictObjectStore) -> None:
        # separate different kind of objects
        submodels = []
        for obj in obj_store:
            if isinstance(obj, model.Asset):
                self.assert_example_asset(obj)
            if isinstance(obj, model.AssetAdministrationShell):
                self.assert_example_asset_administration_shell(obj)
            if isinstance(obj, model.Submodel):
                submodels.append(obj)
            if isinstance(obj, model.ConceptDescription):
                self.assert_example_concept_description(obj)

        for submodel in submodels:
            if submodel.id_short == 'Identification':
                self.assert_example_asset_identification_submodel(submodel)
            elif submodel.id_short == 'BillOfMaterial':
                self.assert_example_bill_of_material_submodel(submodel)
            elif submodel.id_short == 'TestSubmodel':
                self.assert_example_submodel(submodel)
            else:
                raise KeyError()
