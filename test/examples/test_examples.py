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
import unittest

from aas.examples.data import example_aas, example_aas_mandatory_attributes, example_aas_missing_attributes, \
    example_concept_description, example_submodel_template
from aas.examples.data._helper import AASDataChecker
from aas import model


class ExampleAASTest(unittest.TestCase):
    def test_example_asset_identification_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas.create_example_asset_identification_submodel()
        example_aas.check_example_asset_identification_submodel(checker, submodel)

    def test_example_bill_of_material_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas.create_example_bill_of_material_submodel()
        example_aas.check_example_bill_of_material_submodel(checker, submodel)

    def test_example_asset(self):
        checker = AASDataChecker(raise_immediately=True)
        asset = example_aas.create_example_asset()
        example_aas.check_example_asset(checker, asset)

    def test_example_concept_description(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_description = example_aas.create_example_concept_description()
        example_aas.check_example_concept_description(checker, concept_description)

    def test_example_asset_administration_shell(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_dictionary = example_aas.create_example_concept_dictionary()
        shell = example_aas.create_example_asset_administration_shell(concept_dictionary)
        example_aas.check_example_asset_administration_shell(checker, shell)

    def test_example_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas.create_example_submodel()
        example_aas.check_example_submodel(checker, submodel)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store = example_aas.create_full_example()
        example_aas.check_full_example(checker, obj_store)

        failed_asset = model.Asset(kind=model.AssetKind.INSTANCE,
                                   identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_asset)
        with self.assertRaises(KeyError) as cm:
            example_aas.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Asset[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_asset)

        failed_shell = model.AssetAdministrationShell(
            asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                                local=False,
                                                value='test',
                                                id_type=model.KeyType.IRI),),
                                     model.Asset),
            identification=model.Identifier('test', model.IdentifierType.CUSTOM)
        )
        obj_store.add(failed_shell)
        with self.assertRaises(KeyError) as cm:
            example_aas.check_full_example(checker, obj_store)
        self.assertEqual(
            "'AssetAdministrationShell[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_shell)

        failed_submodel = model.Submodel(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_submodel)
        with self.assertRaises(KeyError) as cm:
            example_aas.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Submodel[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_submodel)

        failed_cd = model.ConceptDescription(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_cd)
        with self.assertRaises(KeyError) as cm:
            example_aas.check_full_example(checker, obj_store)
        self.assertEqual(
            "'ConceptDescription[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_cd)

        class DummyIdentifiable(model.Identifiable):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification
        failed_identifiable = DummyIdentifiable(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_identifiable)
        with self.assertRaises(KeyError) as cm:
            example_aas.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Check for DummyIdentifiable[Identifier(CUSTOM=test)] not implemented'",
            str(cm.exception)
        )
        example_aas.check_full_example(checker, obj_store, False)
        obj_store.discard(failed_identifiable)


class ExampleAASMandatoryTest(unittest.TestCase):
    def test_example_asset(self):
        checker = AASDataChecker(raise_immediately=True)
        asset = example_aas_mandatory_attributes.create_example_asset()
        example_aas_mandatory_attributes.check_example_asset(checker, asset)

    def test_example_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas_mandatory_attributes.create_example_submodel()
        example_aas_mandatory_attributes.check_example_submodel(checker, submodel)

    def test_example_empty_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas_mandatory_attributes.create_example_empty_submodel()
        example_aas_mandatory_attributes.check_example_empty_submodel(checker, submodel)

    def test_example_concept_description(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_description = example_aas_mandatory_attributes.create_example_concept_description()
        example_aas_mandatory_attributes.check_example_concept_description(checker, concept_description)

    def test_example_asset_administration_shell(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_dictionary = example_aas_mandatory_attributes.create_example_concept_dictionary()
        shell = example_aas_mandatory_attributes.create_example_asset_administration_shell(concept_dictionary)
        example_aas_mandatory_attributes.check_example_asset_administration_shell(checker, shell)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store = example_aas_mandatory_attributes.create_full_example()
        example_aas_mandatory_attributes.check_full_example(checker, obj_store)

        failed_asset = model.Asset(kind=model.AssetKind.INSTANCE,
                                   identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_asset)
        with self.assertRaises(KeyError) as cm:
            example_aas_mandatory_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Asset[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_asset)

        failed_shell = model.AssetAdministrationShell(
            asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                                local=False,
                                                value='test',
                                                id_type=model.KeyType.IRI),),
                                     model.Asset),
            identification=model.Identifier('test', model.IdentifierType.CUSTOM)
        )
        obj_store.add(failed_shell)
        with self.assertRaises(KeyError) as cm:
            example_aas_mandatory_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'AssetAdministrationShell[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_shell)

        failed_submodel = model.Submodel(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_submodel)
        with self.assertRaises(KeyError) as cm:
            example_aas_mandatory_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Submodel[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_submodel)

        failed_cd = model.ConceptDescription(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_cd)
        with self.assertRaises(KeyError) as cm:
            example_aas_mandatory_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'ConceptDescription[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_cd)

        class DummyIdentifiable(model.Identifiable):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification

        failed_identifiable = DummyIdentifiable(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_identifiable)
        with self.assertRaises(KeyError) as cm:
            example_aas_mandatory_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Check for DummyIdentifiable[Identifier(CUSTOM=test)] not implemented'",
            str(cm.exception)
        )
        example_aas_mandatory_attributes.check_full_example(checker, obj_store, False)
        obj_store.discard(failed_identifiable)


class ExampleAASMissingTest(unittest.TestCase):
    def test_example_asset(self):
        checker = AASDataChecker(raise_immediately=True)
        asset = example_aas_missing_attributes.create_example_asset()
        example_aas_missing_attributes.check_example_asset(checker, asset)

    def test_example_submodel(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_aas_missing_attributes.create_example_submodel()
        example_aas_missing_attributes.check_example_submodel(checker, submodel)

    def test_example_concept_description(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_description = example_aas_missing_attributes.create_example_concept_description()
        example_aas_missing_attributes.check_example_concept_description(checker, concept_description)

    def test_example_asset_administration_shell(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_dictionary = example_aas_missing_attributes.create_example_concept_dictionary()
        shell = example_aas_missing_attributes.create_example_asset_administration_shell(concept_dictionary)
        example_aas_missing_attributes.check_example_asset_administration_shell(checker, shell)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store = example_aas_missing_attributes.create_full_example()
        example_aas_missing_attributes.check_full_example(checker, obj_store)

        failed_asset = model.Asset(kind=model.AssetKind.INSTANCE,
                                   identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_asset)
        with self.assertRaises(KeyError) as cm:
            example_aas_missing_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Asset[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_asset)

        failed_shell = model.AssetAdministrationShell(
            asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                                local=False,
                                                value='test',
                                                id_type=model.KeyType.IRI),),
                                     model.Asset),
            identification=model.Identifier('test', model.IdentifierType.CUSTOM)
        )
        obj_store.add(failed_shell)
        with self.assertRaises(KeyError) as cm:
            example_aas_missing_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'AssetAdministrationShell[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_shell)

        failed_submodel = model.Submodel(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_submodel)
        with self.assertRaises(KeyError) as cm:
            example_aas_missing_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Submodel[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_submodel)

        failed_cd = model.ConceptDescription(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_cd)
        with self.assertRaises(KeyError) as cm:
            example_aas_missing_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'ConceptDescription[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_cd)

        class DummyIdentifiable(model.Identifiable):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification

        failed_identifiable = DummyIdentifiable(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_identifiable)
        with self.assertRaises(KeyError) as cm:
            example_aas_missing_attributes.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Check for DummyIdentifiable[Identifier(CUSTOM=test)] not implemented'",
            str(cm.exception)
        )
        example_aas_missing_attributes.check_full_example(checker, obj_store, False)
        obj_store.discard(failed_identifiable)


class ExampleConceptDescriptionTest(unittest.TestCase):
    def test_iec61360_concept_description(self):
        checker = AASDataChecker(raise_immediately=True)
        concept_description = example_concept_description.create_iec61360_concept_description()
        example_concept_description.check_example_iec61360_concept_description(checker, concept_description)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        obj_store.add(example_concept_description.create_iec61360_concept_description())
        example_concept_description.check_full_example(checker, obj_store)

        failed_asset = model.Asset(kind=model.AssetKind.INSTANCE,
                                   identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_asset)
        with self.assertRaises(KeyError) as cm:
            example_concept_description.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Asset[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_asset)

        failed_shell = model.AssetAdministrationShell(
            asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                                local=False,
                                                value='test',
                                                id_type=model.KeyType.IRI),),
                                     model.Asset),
            identification=model.Identifier('test', model.IdentifierType.CUSTOM)
        )
        obj_store.add(failed_shell)
        with self.assertRaises(KeyError) as cm:
            example_concept_description.check_full_example(checker, obj_store)
        self.assertEqual(
            "'AssetAdministrationShell[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_shell)

        failed_submodel = model.Submodel(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_submodel)
        with self.assertRaises(KeyError) as cm:
            example_concept_description.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Submodel[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_submodel)

        failed_cd = model.ConceptDescription(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_cd)
        with self.assertRaises(KeyError) as cm:
            example_concept_description.check_full_example(checker, obj_store)
        self.assertEqual(
            "'ConceptDescription[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_cd)

        class DummyIdentifiable(model.Identifiable):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification

        failed_identifiable = DummyIdentifiable(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_identifiable)
        with self.assertRaises(KeyError) as cm:
            example_concept_description.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Check for DummyIdentifiable[Identifier(CUSTOM=test)] not implemented'",
            str(cm.exception)
        )
        example_concept_description.check_full_example(checker, obj_store, False)
        obj_store.discard(failed_identifiable)


class ExampleSubmodelTemplate(unittest.TestCase):
    def test_example_submodel_template(self):
        checker = AASDataChecker(raise_immediately=True)
        submodel = example_submodel_template.create_example_submodel_template()
        example_submodel_template.check_example_submodel(checker, submodel)

    def test_full_example(self):
        checker = AASDataChecker(raise_immediately=True)
        obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        obj_store.add(example_submodel_template.create_example_submodel_template())
        example_submodel_template.check_full_example(checker, obj_store)

        failed_asset = model.Asset(kind=model.AssetKind.INSTANCE,
                                   identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_asset)
        with self.assertRaises(KeyError) as cm:
            example_submodel_template.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Asset[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_asset)

        failed_shell = model.AssetAdministrationShell(
            asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                                local=False,
                                                value='test',
                                                id_type=model.KeyType.IRI),),
                                     model.Asset),
            identification=model.Identifier('test', model.IdentifierType.CUSTOM)
        )
        obj_store.add(failed_shell)
        with self.assertRaises(KeyError) as cm:
            example_submodel_template.check_full_example(checker, obj_store)
        self.assertEqual(
            "'AssetAdministrationShell[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_shell)

        failed_submodel = model.Submodel(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_submodel)
        with self.assertRaises(KeyError) as cm:
            example_submodel_template.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Submodel[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_submodel)

        failed_cd = model.ConceptDescription(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_cd)
        with self.assertRaises(KeyError) as cm:
            example_submodel_template.check_full_example(checker, obj_store)
        self.assertEqual(
            "'ConceptDescription[Identifier(CUSTOM=test)] is not in example'",
            str(cm.exception)
        )
        obj_store.discard(failed_cd)

        class DummyIdentifiable(model.Identifiable):
            def __init__(self, identification: model.Identifier):
                super().__init__()
                self.identification = identification

        failed_identifiable = DummyIdentifiable(identification=model.Identifier('test', model.IdentifierType.CUSTOM))
        obj_store.add(failed_identifiable)
        with self.assertRaises(KeyError) as cm:
            example_submodel_template.check_full_example(checker, obj_store)
        self.assertEqual(
            "'Check for DummyIdentifiable[Identifier(CUSTOM=test)] not implemented'",
            str(cm.exception)
        )
        example_submodel_template.check_full_example(checker, obj_store, False)
        obj_store.discard(failed_identifiable)
