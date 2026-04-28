# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from basyx.aas import model
from basyx.aas.util.traversal import walk_submodel, walk_submodel_element


class TestWalkSubmodel(unittest.TestCase):
    def _submodel(self, *elements: model.SubmodelElement) -> model.Submodel:
        return model.Submodel("test-submodel", submodel_element=list(elements))

    def test_flat_submodel(self):
        prop = model.Property("prop", model.datatypes.String)
        sm = self._submodel(prop)
        result = list(walk_submodel(sm))
        self.assertCountEqual([prop], result)

    def test_collection_traversal(self):
        child1 = model.Property("child1", model.datatypes.String)
        child2 = model.Property("child2", model.datatypes.String)
        coll = model.SubmodelElementCollection("coll", value=[child1, child2])
        sm = self._submodel(coll)
        result = list(walk_submodel(sm))
        self.assertCountEqual([child1, child2, coll], result)

    def test_list_traversal(self):
        child = model.Property(None, model.datatypes.String)
        sml = model.SubmodelElementList("sml", type_value_list_element=model.Property,
                                        value_type_list_element=model.datatypes.String, value=[child])
        sm = self._submodel(sml)
        result = list(walk_submodel(sm))
        self.assertCountEqual([child, sml], result)

    def test_entity_statement_traversal(self):
        stmt = model.Property("stmt", model.datatypes.String)
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY, statement=[stmt])
        sm = self._submodel(entity)
        result = list(walk_submodel(sm))
        self.assertCountEqual([stmt, entity], result)

    def test_entity_empty_statement(self):
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY)
        sm = self._submodel(entity)
        result = list(walk_submodel(sm))
        self.assertCountEqual([entity], result)

    def test_operation_variables_traversal(self):
        in_var = model.Property("in_var", model.datatypes.String)
        out_var = model.Property("out_var", model.datatypes.String)
        inout_var = model.Property("inout_var", model.datatypes.String)
        op = model.Operation("op", input_variable=[in_var], output_variable=[out_var],
                             in_output_variable=[inout_var])
        sm = self._submodel(op)
        result = list(walk_submodel(sm))
        self.assertCountEqual([in_var, out_var, inout_var, op], result)

    def test_operation_empty_variables(self):
        op = model.Operation("op")
        sm = self._submodel(op)
        result = list(walk_submodel(sm))
        self.assertCountEqual([op], result)

    def test_collection_inside_entity_statement(self):
        inner = model.Property("inner", model.datatypes.String)
        coll = model.SubmodelElementCollection("coll", value=[inner])
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY, statement=[coll])
        sm = self._submodel(entity)
        result = list(walk_submodel(sm))
        self.assertCountEqual([inner, coll, entity], result)

    def test_entity_inside_operation_input_variable(self):
        stmt = model.Property("stmt", model.datatypes.String)
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY, statement=[stmt])
        op = model.Operation("op", input_variable=[entity])
        sm = self._submodel(op)
        result = list(walk_submodel(sm))
        self.assertCountEqual([stmt, entity, op], result)

    def test_walk_from_collection(self):
        prop = model.Property("prop", model.datatypes.String)
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY, statement=[prop])
        coll = model.SubmodelElementCollection("coll", value=[entity])
        # walk_submodel_element yields descendants of coll, not coll itself
        result = list(walk_submodel_element(coll))
        self.assertCountEqual([prop, entity], result)

    def test_walk_from_list(self):
        op = model.Operation(None)
        sml = model.SubmodelElementList("sml", type_value_list_element=model.Operation, value=[op])
        # walk_submodel_element yields descendants of sml, not sml itself
        result = list(walk_submodel_element(sml))
        self.assertCountEqual([op], result)

    def test_file_inside_entity_is_found(self):
        """Regression test for issue #423: File inside Entity.statement must be yielded."""
        f = model.File("file", content_type="application/pdf", value="/some/file.pdf")
        entity = model.Entity("entity", model.EntityType.CO_MANAGED_ENTITY, statement=[f])
        sm = self._submodel(entity)
        files = [e for e in walk_submodel(sm) if isinstance(e, model.File)]
        self.assertIn(f, files)

    def test_file_inside_operation_variable_is_found(self):
        """Regression test for issue #423: File inside Operation variable must be yielded."""
        f = model.File("file", content_type="application/pdf", value="/some/file.pdf")
        op = model.Operation("op", input_variable=[f])
        sm = self._submodel(op)
        files = [e for e in walk_submodel(sm) if isinstance(e, model.File)]
        self.assertIn(f, files)
