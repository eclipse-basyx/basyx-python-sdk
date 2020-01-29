# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the serialization and deserialization of asset administration shells, submodels and assets
"""

# to get all functions import model
import io
import json

from aas import model
from aas.adapter.json import json_serialization, json_deserialization
from aas.model import Asset, AssetAdministrationShell, Submodel

# create asset, submodel and asset administration shell, for more details look at 'tutorial_create_simple_aas'
asset = Asset(
    kind=model.AssetKind.INSTANCE,
    identification=model.Identifier('https://acplt.org/Simple_Asset', model.IdentifierType.IRI)
)
submodel = Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI),
    submodel_element={
        model.Property(
            id_short='ExampleProperty',
            value_type=model.datatypes.String,
            value='exampleValue',
            semantic_id=model.Reference(
                (model.Key(
                    type_=model.KeyElements.GLOBAL_REFERENCE,
                    local=False,
                    value='http://acplt.org/Properties/SimpleProperty',
                    id_type=model.KeyType.IRI
                ),)
            )
        )}
)
aas = AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset=model.AASReference.from_referable(asset),
    submodel_={model.AASReference.from_referable(submodel)}
)

# serialize an object to json with help of the standard json and json_serialization module
# json_serialization.AASToJsonEncoder is a custom JSONDecoder class for serializing Asset Administration Shell data
# into the official JSON format according to 'Details of the Asset Administration Shell', chapter 5.5
json_data = json.loads(json.dumps(aas, cls=json_serialization.AASToJsonEncoder))
json_data = json.loads(json.dumps(submodel.submodel_element.get_referable('ExampleProperty'),
                                  cls=json_serialization.AASToJsonEncoder))
# write json data to file
# define a file stream, here an internal file stream is used. For an external file stream use
# 'open('tutorial.json', 'w', encoding='utf-8')' for opening a json-File to write json data inside
file = io.StringIO()
# write json_data to file
json.dump(json_data, file)

# serialize a data store to json with help of the json_serialization module
# create a store, for more detail look at 'tutorial_storage.py'
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
obj_store.add(asset)
obj_store.add(submodel)
obj_store.add(aas)
# serialize the store using the function 'object_store_to_json' of the 'json_serialization' module
json_data = json_serialization.object_store_to_json(obj_store)

# serialize a data store and directly write it to a file with help of the 'json_serialization' module
# define a file stream, here an internal file stream is used. For an external file stream use
# 'open('tutorial.json', 'w', encoding='utf-8')' for opening a json-File to write json data inside
file2 = io.StringIO()
# serialize data and write it to file using the function 'write_aas_json_file'
json_serialization.write_aas_json_file(file=file2, data=obj_store)

# read a json string from file and deserialize it into a DictObjectStore of AAS objects with help of the
# 'json_deserialization' module
# define a file stream, here the internal file stream from above is used. For an external file stream use
# 'open('tutorial.json', 'r', encoding='utf-8')' for opening a json-File to read json data inside
file2.seek(0)
json_object_store = json_deserialization.read_json_aas_file(file2, failsafe=False)
