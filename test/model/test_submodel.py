# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0

import unittest

from basyx.aas import model


class EntityTest(unittest.TestCase):

    def test_set_entity(self):
        with self.assertRaises(ValueError) as cm:
            obj = model.Entity(id_short='Test', entity_type=model.EntityType.SELF_MANAGED_ENTITY, statement=())
        self.assertEqual('A self-managed entity has to have an asset-reference', str(cm.exception))


class PropertyTest(unittest.TestCase):
    def test_set_value(self):
        property = model.Property('test', model.datatypes.Int, 2)
        self.assertEqual(property.value, 2)
        property.value = None
        self.assertIsNone(property.value)


class RangeTest(unittest.TestCase):
    def test_set_min_max(self):
        range = model.Range('test', model.datatypes.Int, 2, 5)
        self.assertEqual(range.min, 2)
        self.assertEqual(range.max, 5)
        range.min = None
        self.assertIsNone(range.min)
        range.max = None
        self.assertIsNone(range.max)
