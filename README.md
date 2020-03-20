
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


## Features

The `aas`-package provides the following features:

* modelling of Asset Administration Shells as python based classes
* implementation of Asset Administration Shells as python objects
* (de)-serialization of Asset Administration Shells from and to python objects 
(currently supported file/text formats: JSON, XML, CouchDB)
* Compliance Checks

### Project Structure

The `aas`-package is structured into 5 submodules, which will be explained in more detail further down. For an
overview, consider this project structure:

| Module/Package Name                                                                    | Explanation                              |
|----------------------------------------------------------------------------------------|------------------------------------------|
| [model](#package-model-the-aas-metamodel-implemented-in-python)                        | The AAS metamodel implemented in python  |
| [adapter](#package-adapter-adapter-to-various-file-formats)                            | Adapter to various file formats          |
| [compliance_tools](#package-compliance_tool-check-compliance-to-json-and-xml-schemas)  | Check compliance to JSON and XML Schemas |
| [util](#package-util-provide-utilities)                                                | Provide utilities                        |
| [examples](#package-examples-examples-and-tutorials)                                   | Examples and tutorials                   |



### Package `model`: The AAS Metamodel Implemented in Python

This package contains the class-based metamodel of the Asset Adminstration Shell, in accordance to the 
[the document “Details of the Asset Administration Shell” (v2.0)](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details-of-the-Asset-Administration-Shell-Part1.html).
The package is structured into 7 modules, each containing one aspect of the AAS meta-model.


#### Module `model.aas`

Contains top-level classes:

* `AssetAdministrationShell`
* `Asset`
* `View`


#### Module `model.base`

Contains basic structures and classes, including abstract classes needed for the implementation of higher level classes.


#### Module `model.concept`

Contains classes:

* `ConceptDescription`
* `ConceptDictionary`


#### Module `model.datatypes`

Defines native python types for all simple built-in XSD datatypes and functions used for XML (de)-serialization and for
direct use for data values in the context of Asset Administration Shells.


#### Module `model.provider`

Implements Registries for the Asset Administration Shell for resolving of global identifiers and mapping identifiers
to identifiable objects.


#### Module `model.security`

This module contains the security aspects of the AAS metamodel. Currently, the security model is not ready yet, so this
module doesn't do anything.


#### Module `model.submodel`

This module contains the classes needed for modelling Submodels.


### Package `util`: Provide Utilities

This package provides utilities for working with a python based AAS model. Currently, the only module it contains is
`util.identification`, which generates identifiers in accordance with the metamodel of the Asset Administration Shell.


### Package `adapter`: Adapter to Various File Formats

The `adapter`-module is used for (de)-serialization from and to JSON and XML. Furthermore, there is a couchdb-backend
for persistently storing AAS objects. The module is divided into the following sub-modules:

| Module/Package Name                         | Explanation                                                    |
|---------------------------------------------|----------------------------------------------------------------|
| [adapter.json](#package-adapterjson)         | JSON (de)-serialization                                        |
| [adapter.xml](#package-adapterxml)           | XML (de)-serialization                                         |
| [adapter.couchdb](#module-adaptercouchdb)   | CouchDB-backend for storing AAS objects                        |


#### Package `adapter.json`

Modules for serializing Asset Administration Shell data to the official JSON format.
Serialization of objects from `aas.model` to JSON is done with `adapter.json.json_serialization`.
Deserialization of JSON files or IO-objects to pyaas objects can be achieved with `adapter.json.json_deserialization`


#### Package `adapter.xml`

Modules for serializing Asset Administration Shell data to the official XML format.
Serialization of objects from `aas.model` to XML files or IO-objects is done with `adapter.xml.xml_serialization`. 
The other way around from XML to `aas.model`-objects is done with `adapter.xml.xml_deserialization`


#### Module `adapter.couchdb`

CouchDB backend for persistently storing AAS objects

This module provides the `CouchDBObjectStore` class, that implements the AbstractObjectStore interface for storing and
retrieving Identifiable PyI40AAS objects in/from a CouchDB server. The objects are serialized to JSON using the
aas.adapter.json package and transferred to the configured CouchDB database.


### Package `compliance_tool`: Check Compliance to JSON and XML Schemas

This package contains modules to check compliance of a given JSON or XML file to their respective schemas.
The compliance tool can be accessed via the module `compliance_tool.cli`.


### Package `examples`: Examples and Tutorials

The package `examples` contains a series of examples and tutorials inside respective modules. 
The tutorials can be found in modules `examples.tutorial_[tutorial name here]`, while the examples are found in
`examples.data.example_[example name here]`.


## Getting Started

### Example

## Contributing
