import unittest
import json
import os

from aas import model
from aas.adapter.json import json_serialization
from jsonschema import validate  # type: ignore


class JsonSerializationTest(unittest.TestCase):

    def test_serialize_Object(self) -> None:
        test_object = model.Property("test_id_short", "string", category="PARAMETER",
                                     description={"en-us": "Germany", "de": "Deutschland"})
        json_data = json.dumps(test_object, cls=json_serialization.AASToJsonEncoder)

    def test_validate_serialization(self) -> None:
        asset_key = [model.Key(model.KeyElements.ASSET, True, "asset", model.KeyType.CUSTOM)]
        asset_reference = model.Reference(asset_key, model.Asset)
        aas_identifier = model.Identifier("AAS1", model.IdentifierType.CUSTOM)
        submodel_key = model.Key(model.KeyElements.SUBMODEL, True, "SM1", model.KeyType.CUSTOM)
        submodel_identifier = submodel_key.get_identifier()
        assert(submodel_identifier is not None)
        submodel_reference = model.Reference([submodel_key], model.Submodel)
        # The JSONSchema expects every object with HasSemnatics (like Submodels) to have a `semanticId` Reference, which
        # must be a Reference. (This seems to be a bug in the JSONSchema.)
        submodel = model.Submodel(submodel_identifier, semantic_id=model.Reference([], model.Referable))
        test_aas = model.AssetAdministrationShell(asset_reference, aas_identifier, submodel_={submodel_reference})

        # serialize object to json
        json_data = json.dumps({
                'assetAdministrationShells': [test_aas],
                'submodels': [submodel],
                'assets': [],
                'conceptDescriptions': [],
            }, cls=json_serialization.AASToJsonEncoder)
        json_data_new = json.loads(json_data)

        # load schema
        with open(os.path.join(os.path.dirname(__file__), 'aasJSONSchemaV2.0.json'), 'r') as json_file:
            aas_schema = json.load(json_file)

        # validate serialization against schema
        validate(instance=json_data_new, schema=aas_schema)
