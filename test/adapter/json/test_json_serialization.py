import unittest
import json
import os

from aas import model
from aas.adapter.json import json_serialization
from jsonschema import validate  # type: ignore


class JsonSerializationTest(unittest.TestCase):

    def test_serialize_Object(self):
        test_object = model.Property("test_id_short", "string", category="PARAMETER",
                                     description={"en-us": "Germany", "de": "Deutschland"})
        json_data = json.dumps(test_object, cls=json_serialization.AASToJsonEncoder)
        print(json_data)

    def test_validate_serialization(self):
        asset_key = [model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM)]
        asset_reference = model.Reference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = [model.Key(model.KeyElements.SUBMODEL, True, "submodel", model.KeyType.CUSTOM)]
        submodel_reference = model.Reference(submodel_key, model.Submodel)
        # submodel_identifier = model.Identifier("SM1", model.IdentifierType.CUSTOM)
        # submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel_=[submodel_reference])

        # serialize object to json
        test_aas_json_data = json.dumps(test_aas, cls=json_serialization.AASToJsonEncoder)
        test_submodel_data = ""
        test_asset_data = ""
        test_concept_description_data = ""
        json_data_new = '{"assetAdministrationShells": [' + test_aas_json_data + '], ' \
                        '"submodels": [' + test_submodel_data + '], ' \
                        '"assets": [' + test_asset_data + '], ' \
                        '"conceptDescriptions": [' + test_concept_description_data + ']}'
        json_data_new2 = json.loads(json_data_new)

        # load schema
        with open(os.path.join(os.path.dirname(__file__), 'aasJSONSchemaV2.0.json'), 'r') as json_file:
            schema_data = json_file.read()
        aas_schema = json.loads(schema_data)

        # validate serialization against schema
        validate(instance=json_data_new2, schema=aas_schema)
