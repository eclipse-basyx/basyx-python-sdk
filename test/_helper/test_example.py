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
import io
import json
import logging
import unittest
from aas.adapter.json import json_deserialization
from aas import model
from aas.examples.example_create_aas import create_example_asset_identification_submodel


class ExampleAASTest(unittest.TestCase):

    def test_example_asset_identification_submodel(self):
        submodel = create_example_asset_identification_submodel()
        self.assert_example_asset_identification_submodel(submodel)

    def assert_example_asset_identification_submodel(self, submodel: model.Submodel) -> None:
        # Test attributes of Submodel
        self.assertEqual('http://acplt.org/Submodels/Assets/TestAsset/Identification', submodel.identification.id)
        self.assertEqual(model.IdentifierType.IRI, submodel.identification.id_type)
        self.assertEqual(2, submodel.submodel_element.__len__())
        self.assertEqual('Identification', submodel.id_short)
        self.assertIsNone(submodel.category)
        self.assertEqual({'en-us': 'An example asset identification submodel for the test application',
                          'de': 'Ein Beispiel-Identifikations-Submodel für eine Test-Anwendung'}, submodel.description)
        self.assertIsNone(submodel.parent)
        self.assertEqual('0.9', submodel.administration.version)  # type: ignore
        self.assertEqual('0', submodel.administration.revision)  # type: ignore
        submodel.data_specification.__eq__(model.Reference((model.Key(type_=model.KeyElements.ASSET,
                                                                      local=False,
                                                                      value='http://acplt.org/DataSpecifications/'
                                                                            'Submodels/AssetIdentification',
                                                                      id_type=model.KeyType.IRDI),)))
        submodel.semantic_id.__eq__(model.Reference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                               local=False,
                                                               value='http://acplt.org/SubmodelTemplates/'
                                                                     'AssetIdentification',
                                                               id_type=model.KeyType.IRDI),)))
        self.assertEqual(0, submodel.qualifier.__len__())
        self.assertEqual(model.ModelingKind.INSTANCE, submodel.kind)

        # test attributes of property ManufacturerName
        manufacturer_name: model.Property = submodel.get_referable('ManufacturerName')  # type: ignore
        self.assertIsInstance(manufacturer_name, model.Property)
        self.assertEqual('ManufacturerName', manufacturer_name.id_short)
        self.assertEqual('string', manufacturer_name.value_type)
        self.assertEqual('ACPLT', manufacturer_name.value)
        manufacturer_name.value_id.__eq__(model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
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
        self.assertEqual(0, manufacturer_name.data_specification.__len__())
        manufacturer_name.semantic_id.__eq__(model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                                        local=False,
                                                                        value='0173-1#02-AAO677#002',
                                                                        id_type=model.KeyType.IRDI),)))
        self.assertEqual(1, manufacturer_name.qualifier.__len__())
        self.assertEqual(model.ModelingKind.INSTANCE, manufacturer_name.kind)

        # Test attributes of property qualifier
        qualifier: model.Qualifier
        for qualifier in manufacturer_name.qualifier:  # type: ignore
            self.assertIsInstance(qualifier, model.Qualifier)
            self.assertEqual('http://acplt.org/Qualifier/ExampleQualifier', qualifier.type_)
            self.assertEqual('string', qualifier.value_type)
            self.assertEqual('100', qualifier.value)
            qualifier.value_id.__eq__(model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                                 local=False,
                                                                 value='http://acplt.org/ValueId/'
                                                                       'ExampleValueId',
                                                                 id_type=model.KeyType.IRDI),)))

        instance_id: model.Property = submodel.get_referable('InstanceId')  # type: ignore
        self.assertIsInstance(instance_id, model.Property)
        self.assertEqual(1, instance_id.qualifier.__len__())
        # Test attributes of property qualifier
        formula: model.Formula
        for formula in instance_id.qualifier:  # type: ignore
            self.assertIsInstance(formula, model.Formula)
            self.assertEqual(1, formula.depends_on.__len__())
            for reference in formula.depends_on:
                reference.__eq__(model.Reference((model.Key(type_=model.KeyElements.GLOBAL_REFERENCE,
                                                            local=False,
                                                            value='http://acplt.org/Formula/ExampleFormula',
                                                            id_type=model.KeyType.IRDI),)))
