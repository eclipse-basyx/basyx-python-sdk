# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from basyx.aas import model


class IEC61360ConceptDescriptionTest(unittest.TestCase):
    def test_set_value(self):
        cp = model.IEC61360ConceptDescription(model.Identifier('test', model.IdentifierType.CUSTOM),
                                              {'de': 'test'},
                                              model.concept.IEC61360DataType.STRING,
                                              value_format=model.datatypes.Int,
                                              value=2)
        self.assertEqual(cp.value, 2)
        cp.value = None
        self.assertIsNone(cp.value)
