#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the serialization and deserialization of Asset Administration Shells, Submodels and Assets into/from JSON
and XML files.
"""

import json

from aas import model
import aas.adapter.json
import aas.adapter.xml

# 'Details of the Asset Administration Shell' specifies multiple official serialization formats for AAS data. In this
# tutorial, we show, how the PyI40AAS library can be used to serialize AAS objects into JSON or XML and to create
# JSON/XML files according to the standardized format. It is also demonstrated, how these files can be parsed to
# restore the AAS objects as Python objects.
#
# Step by Step Guide:
# Step 1: creating Asset, Submodel and Asset Administration Shell objects
# Step 2: serializing single objects to JSON
# Step 3: parsing single objects or custom data structures from JSON
# Step 4: writing multiple identifiable objects to a (standard-compliant) JSON/XML file
# Step 5: reading the serialized aas objects from JSON/XML files


###########################################################################
# Step 1: Creating Asset, Submodel and Asset Administration Shell Objects #
###########################################################################

# For more details, take a look at `tutorial_create_simple_aas.py`

asset = model.Asset(
    identification=model.Identifier('https://acplt.org/Simple_Asset', model.IdentifierType.IRI)
)
submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI),
    submodel_element={
        model.Property(
            id_short='ExampleProperty',
            value_type=model.datatypes.String,
            value='exampleValue',
            semantic_id=model.Reference(
                (model.Key(
                    type_=model.KeyElements.GLOBAL_REFERENCE,
                    value='http://acplt.org/Properties/SimpleProperty',
                    id_type=model.KeyType.IRI
                ),)
            )
        )}
)
aashell = model.AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset_information=model.AssetInformation(global_asset_id=model.AASReference.from_referable(asset)),
    submodel={model.AASReference.from_referable(submodel)}
)


##############################################
# Step 2: Serializing Single Objects to JSON #
##############################################

# Before serializing the data, we should make sure, it's up to data. This is irrelevant for the static AAS objects in
# this tutorial, but may be important when dealing with dynamic data.
# See `tutorial_dynamic_model.py` for more information on that topic.
aashell.update()

# `AASToJsonEncoder` from the `aas.adapter.json` module is a custom JSONEncoder class for serializing
# Asset Administration Shell data into the official JSON format according to
# 'Details of the Asset Administration Shell', chapter 5.5, using Python's built-in JSON library. When provided to the
# the `json.dump()` and `json.dumps()` methods, these methods are enabled to correctly handle AAS objects within the
# dumped data structure.
aashell_json_string = json.dumps(aashell, cls=aas.adapter.json.AASToJsonEncoder)

property_json_string = json.dumps(submodel.submodel_element.get_referable('ExampleProperty'),
                                  cls=aas.adapter.json.AASToJsonEncoder)

# Using this technique, we can also serialize Python dict and list data structures with nested AAS objects:
json_string = json.dumps({'the_submodel': submodel,
                          'the_aas': aashell
                          },
                         cls=aas.adapter.json.AASToJsonEncoder)


######################################################################
# Step 3: Parsing Single Objects or Custom Data Structures from JSON #
######################################################################

# JSON deserialization works in a similar way to JSON serialization: The `aas.adapter.json` module provides a
# JSONDecoder class, called `AASFromJSONDecoder` which can be passed to `json.load()` or `json.loads()` to ensure that
# AAS objects contained in the JSON data are transformed into their PyI40AAS Python object representation instead of
# simple Python dicts:
submodel_and_aas = json.loads(json_string, cls=aas.adapter.json.AASFromJsonDecoder)

# Alternatively, one can use the `StrictAASFromJsonDecoder` which works in just the same way, but enforces the format
# specification more strictly. While `AASFromJSONDecoder` will tolerate some semantic errors by simple skipping the
# broken object and issuing a log message, `StrictAASFromJsonDecoder` will raise an Exception in these cases.


#########################################################################################
# Step 4: Writing Multiple Identifiable Objects to a (Standard-compliant) JSON/XML File #
#########################################################################################

# step 4.1: creating an ObjectStore containing the objects to be serialized
# For more information, take a look into `tutorial_storage.py`
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
obj_store.add(asset)
obj_store.add(submodel)
obj_store.add(aashell)

# step 4.2: Again, make sure that the data is up to date
asset.update()
submodel.update()
aashell.update()

# step 4.3: writing the contents of the ObjectStore to a JSON file
# Heads up! It is important to open the file in text-mode with utf-8 encoding!
with open('data.json', 'w', encoding='utf-8') as json_file:
    aas.adapter.json.write_aas_json_file(json_file, obj_store)

# We can pass the additional keyword argument `indent=4` to `write_aas_json_file()` to format the JSON file in a more
# human-readable (but much more space-consuming) manner.

# step 4.4: writing the contents of the ObjectStore to an XML file
# Heads up! For writing XML files -- in contrast to writing JSON --, the file must be opened in binary mode! The XML
# writer will handle character encoding internally.
with open('data.xml', 'wb') as xml_file:
    aas.adapter.xml.write_aas_xml_file(xml_file, obj_store)


##################################################################
# Step 5: Reading the Serialized AAS Objects From JSON/XML Files #
##################################################################

# step 5.1: reading contents of the JSON file as an ObjectStore
# Heads up! It is important to open the file in text-mode with utf-8 encoding! Using 'utf-8-sig' is recommended to
# handle unicode Byte Order Marks (BOM) correctly.
with open('data.json', encoding='utf-8-sig') as json_file:
    json_file_data = aas.adapter.json.read_aas_json_file(json_file)

# By passing the `failsafe=False` argument to `read_aas_json_file()`, we can switch to the `StrictAASFromJsonDecoder`
# (see step 3) for a stricter error reporting.

# step 5.2: reading contents of the XML file as an ObjectStore
# Heads up! For reading XML files -- in contrast to reading JSON --, the file must be opened in binary mode! The XML
# writer will handle character encoding internally.
with open('data.xml', 'rb') as xml_file:
    xml_file_data = aas.adapter.xml.read_aas_xml_file(xml_file)

# Again, we can use `failsafe=False` for switching on stricter error reporting in the parser.

# step 5.3: Retrieving the objects from the ObjectStore
# For more information on the availiable techniques, see `tutorial_storage.py`.
submodel_from_xml = xml_file_data.get_identifiable(model.Identifier('https://acplt.org/Simple_Submodel',
                                                                    model.IdentifierType.IRI))
assert(isinstance(submodel_from_xml, model.Submodel))
