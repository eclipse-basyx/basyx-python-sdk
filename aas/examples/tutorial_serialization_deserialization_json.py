# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the serialization and deserialization of asset administration shells, submodels and assets
"""

import io
import json

# Import all PyI40AAS classes from model package
from aas import model
from aas.adapter.json import json_serialization, json_deserialization
from aas.model import Asset, AssetAdministrationShell, Submodel

# In this tutorial you get a step by step guide how to serialize objects of the meta model according to
# 'Details of the Asset Administration Shell'. Therefore, you will learn how to serialize one object and an object
# store to json data. You also will learn how to write this json data to a json file. This tutorial close with a
# demonstration of how to deserialize json data from a json file.
# Step by step guide:
# step 1: create asset, submodel and asset administration shell, for more details look at
#         'tutorial_create_simple_aas.py'
# step 2: serialize an object to json and write it to file
# step 3: serialize an object store to json and write it to file
# step 4: # read a json string from file and deserialize it into an object store of AAS objects

#################################################################
# step 1: create asset, submodel and asset administration shell #
#################################################################
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

############################################################
# step 2: serialize an object to json and write it to file #
############################################################
# step 2.1: serialize an object to json
# json_serialization.AASToJsonEncoder is a custom JSONDecoder class for serializing Asset Administration Shell data
# into the official JSON format according to 'Details of the Asset Administration Shell', chapter 5.5
# serialize an asset administration shell
json_data_object = json.loads(json.dumps(aas, cls=json_serialization.AASToJsonEncoder))
# serialize a property
json_data_object = json.loads(json.dumps(submodel.submodel_element.get_referable('ExampleProperty'),
                                         cls=json_serialization.AASToJsonEncoder))
# step 2.2: write json data to file
# define a file stream, here an internal file stream is used. For an external file stream use
# 'open('tutorial.json', 'w', encoding='utf-8')' for opening a json-File to write json data inside
file_object = io.StringIO()
# write json_data to file
json.dump(json_data_object, file_object)

##################################################################
# step 3: serialize an object store to json and write it to file #
##################################################################
# step 2.1: serialize an object store to json
# create an object store containing the asset administration shell, the asset and submodel, defined above, for more
# detail look at 'tutorial_storage.py'
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
obj_store.add(asset)
obj_store.add(submodel)
obj_store.add(aas)
# serialize the store using the function 'object_store_to_json' of the 'json_serialization' module
json_data_store = json_serialization.object_store_to_json(obj_store)
# step 2.2: write json data to file
# define a file stream, here an internal file stream is used. For an external file stream use
# 'open('tutorial.json', 'w', encoding='utf-8')' for opening a json-File to write json data inside
file_store = io.StringIO()
# write json_data to file
json.dump(json_data_store, file_store)

# serialize an object store and write it to a file can be done in one step using the function 'write_aas_json_file'
file_store_2 = io.StringIO()
json_serialization.write_aas_json_file(file=file_store_2, data=obj_store)

#################################################################################################
# step 4: # read a json string from file and deserialize it into an object store of AAS objects #
#################################################################################################
# define a file stream, here the internal file stream from above is used. For an external file stream use
# 'open('tutorial.json', 'r', encoding='utf-8-sig')' for opening a json-File to read json data inside
# we have to set the file pointer to the beginning cause we are using the same file stream. Normally, you do not need
# to do this.
file_store_2.seek(0)
json_object_store = json_deserialization.read_json_aas_file(file_store_2, failsafe=False)
