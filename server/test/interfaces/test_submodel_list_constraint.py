# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

"""SubmodelElementList constraint violations must be 400, not 500 (#672)."""

import json
import unittest
from unittest import mock

from app.interfaces import repository
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.adapter.json import json_serialization
from werkzeug.test import Client


class SubmodelListConstraintClientErrorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.object_store = model.DictIdentifiableStore()
        self.file_store = mock.Mock(spec=aasx.AbstractSupplementaryFileContainer)
        app = repository.WSGIApp(self.object_store, self.file_store, base_path="")
        self.client = Client(app)

    def test_post_property_with_wrong_value_type_returns_400(self) -> None:
        submodel = model.Submodel("https://acplt.org/Test_Submodel_ListConstraint")
        sml = model.SubmodelElementList(
            "L",
            model.Property,
            value_type_list_element=model.datatypes.String,
        )
        submodel.add_referable(sml)
        self.object_store.add(submodel)

        payload = json.dumps(
            model.Property(None, model.datatypes.Int, 1),
            cls=json_serialization.AASToJsonEncoder,
        )
        from app.util.converters import base64url_encode

        response = self.client.post(
            f"/submodels/{base64url_encode(submodel.id)}/submodel-elements/L",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
