
# PyI40AAS – Python Industry 4.0 Asset Administration Shell

The PyI40AAS project aims to provide an implementation of the Asset Administration Shell for Industry 4.0 Systems, compliant
with the meta model and interface specification provided in
[the document “Details of the Asset Administration Shell” (v2.0)](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details-of-the-Asset-Administration-Shell-Part1.html).
The implementation will include the data model as well as interface adapters for serving, retrieving, importing and
exporting Asset Administration Shells.


## License

The PyI40AAS project is provided under the terms of the Apache License (Version 2.0).

For more information, especially considering the licenses of included third-party works, please consult the `NOTICE`
file. 

# test

## Features

### Project Structure

The `aas`-module is structured into 5 submodules, which will be explained in more detail further down. For an
overview, consider this project structure:

| Module Name                                                                           | Explanation                              |
|---------------------------------------------------------------------------------------|------------------------------------------|
| [model](#module-model-the-aas-metamodel-implemented-in-python)                        | The AAS metamodel implemented in python  |
| [util](#module-util-generate-identifiers)                                             | Generate identifiers                     |
| [adapter](#module-adapter-adapter-to-various-file-formats)                            | Adapter to various file formats          |
| [compliance_tools](#module-compliance_tool-check-compliance-to-json-and-xml-schemas)  | Check compliance to JSON and XML Schemas |
| [examples](#module-examples-examples-and-tutorials)                                   | Examples and tutorials                   |



### Module `model`: The AAS Metamodel Implemented in Python

### Module `util`: Generate Identifiers


### Module `adapter`: Adapter to Various File Formats

The `adapter`-module is used for (de)-serialization from and to JSON and XML. Furthermore, there is a couchdb-backend
for persistently storing AAS objects. The module is divided into the following sub-modules:

| Module Name                                 | Explanation                                                    |
|---------------------------------------------|----------------------------------------------------------------|
| [adapter.json](#module-adapterjson)         | JSON (de)-serialization                                        |
| [adapter.xml](#module-adapterxml)           | XML (de)-serialization                                         |
| [adapter.couchdb](#module-adaptercouchdb)   | CouchDB-backend for storing AAS objects                        |


#### Module `adapter.json`

Modules for serializing Asset Administration Shell data to the official JSON format.
Serialization of objects from `aas.model` to JSON is done with `adapter.json.json_serialization`.
Deserialization of JSON files or IO-objects to pyaas objects can be achieved with `adapter.json.json_deserialization`


#### Module `adapter.xml`

Modules for serializing Asset Administration Shell data to the official XML format.
Serialization of objects from `aas.model` to XML files or IO-objects is done with `adapter.xml.xml_serialization`. 
The other way around from XML to `aas.model`-objects is done with `adapter.xml.xml_deserialization`


#### Module `adapter.couchdb`

CouchDB backend for persistently storing AAS objects

This module provides the `CouchDBObjectStore` class, that implements the AbstractObjectStore interface for storing and
retrieving Identifiable PyI40AAS objects in/from a CouchDB server. The objects are serialized to JSON using the
aas.adapter.json package and transferred to the configured CouchDB database.


### Module `compliance_tool`: Check Compliance to JSON and XML Schemas

### Module `examples`: Examples and Tutorials


## Getting Started

### Example

## Contributing
