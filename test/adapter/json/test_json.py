import unittest
import json

from aas import model
from aas.adapter.json import json_serialization


class JsonSerializationTest(unittest.TestCase):
    def test_serialize_Object(self):
        test_object = model.Property("test_id_short", "string", category="PARAMETER",
                                     description={"en-us": "Germany", "de": "Deutschland"})
        json_data = json.dumps(test_object, cls=json_serialization.AASToJsonEncoder)
        print(json_data)
