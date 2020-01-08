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

import os

from aas import model
from aas.adapter import couchdb

from aas.examples import example_create_aas
from .._helper.helpers import ExampleHelper


JSON_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'aasJSONSchemaV2.0.json')


class CouchDBTest(ExampleHelper):
    def test_example_submodel_storing(self) -> None:
        example_submodel = example_create_aas.create_example_submodel()

        # Create CouchDB store, login and check database
        db = couchdb.CouchDBDatabase("http://localhost:5984", "aas_test")
        db.login("aas_test", "aas_test")
        # TODO create clean database before test
        db.check_database()

        # Add exmaple submodel
        db.add(example_submodel)

        # Restore example submodel and check data
        submodel_restored = db.get_identifiable(
            model.Identifier(id_='https://acplt.org/Test_Submodel', id_type=model.IdentifierType.IRI))

        db.discard(submodel_restored)
        db.logout()

        assert(isinstance(submodel_restored, model.Submodel))
        self.assert_example_submodel(submodel_restored)
