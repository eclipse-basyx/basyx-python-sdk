# Copyright (c) 2024 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import unittest

from basyx.aas import model
from basyx.aas.examples.data import create_example, create_example_aas_binding


class TestExampleFunctions(unittest.TestCase):

    def test_create_example(self):
        obj_store = create_example()

        # Check that the object store is not empty
        self.assertGreater(len(obj_store), 0)

        # Check that the object store contains expected elements
        expected_ids = [
            'https://acplt.org/Test_AssetAdministrationShell',
            'https://acplt.org/Test_Submodel_Template',
            'https://acplt.org/Test_ConceptDescription_Mandatory'
        ]
        for id in expected_ids:
            self.assertIsNotNone(obj_store.get_identifiable(id))

    def test_create_example_aas_binding(self):
        obj_store = create_example_aas_binding()

        # Check that the object store is not empty
        self.assertGreater(len(obj_store), 0)

        # Check that the object store contains expected elements
        aas_id = 'https://acplt.org/Test_AssetAdministrationShell'
        sm_id = 'https://acplt.org/Test_Submodel_Template'
        cd_id = 'https://acplt.org/Test_ConceptDescription_Mandatory'

        aas = obj_store.get_identifiable(aas_id)
        sm = obj_store.get_identifiable(sm_id)
        cd = obj_store.get_identifiable(cd_id)

        self.assertIsNotNone(aas)
        self.assertIsNotNone(sm)
        self.assertIsNotNone(cd)

        # Check types
        self.assertIsInstance(aas, model.aas.AssetAdministrationShell)
        self.assertIsInstance(sm, model.submodel.Submodel)
        self.assertIsInstance(cd, model.concept.ConceptDescription)

        # Check that the submodel is referred by the AAS
        self.assertIn(model.ModelReference.from_referable(sm), aas.submodel)
