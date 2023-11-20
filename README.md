# Eclipse BaSyx Python SDK

(formerly known as PyI40AAS – Python Industry 4.0 Asset Administration Shell)

The Eclipse BaSyx Python project focuses on providing a Python implementation of the Asset Administration Shell (AAS) 
for Industry 4.0 Systems. 
These are the currently implemented specifications:

| Specification                         | Version                                                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| Part 1: Metamodel                     | [v3.0 (01001-3-0)](https://industrialdigitaltwin.org/content-hub/aasspecifications/idta_01001-3-0_metamodel)                |
| Part 2: API                           | not implemented yet                                                                                                         |
| Part 3a: Data Specification IEC 61360 | [v3.0 (01003-a-3-0)](https://industrialdigitaltwin.org/content-hub/aasspecifications/idta_01003-a-3-0_data_specification)   |
| Part 5: Package File Format (AASX)    | [v3.0 (01005-3-0)](https://industrialdigitaltwin.org/content-hub/aasspecifications/idta-01005-3-0_package_file_format_aasx) |

## Features

* Modelling of AASs as Python objects
    * **except for**: *HasDataSpecification*
* Reading and writing of AASX package files
* (De-)serialization of AAS objects into/from JSON and XML
* Storing of AAS objects in CouchDB, Backend infrastructure for easy expansion 
* Compliance checking of AAS XML and JSON files


### Project Structure

The BaSyx Python SDK project provides the `basax.aas` Python package with 6 submodules:

* `basyx.aas.model`: The AAS metamodel implemented in python
* `basyx.aas.adapter`: Adapters for various file formats 
* `basyx.aas.backend`: Backend infrastructure for storing and retrieving AAS objects
* `basyx.aas.compliance_tool`: Compliance checker for AAS files
* `basyx.aas.util`: Provides utilities
* `basyx.aas.examples`: Example data and tutorials


## License

The BaSyx Python SDK project is licensed under the terms of the MIT License.

SPDX-License-Identifier: MIT

For more information, especially considering the licenses of included third-party works, please consult the `NOTICE`
file.


## Dependencies

The BaSyx Python SDK requires the following Python packages to be installed for production usage. These dependencies are listed in
`setup.py` to be fetched automatically when installing with `pip`:
* `lxml` (BSD 3-clause License, using `libxml2` under MIT License)
* `python-dateutil` (BSD 3-clause License)
* `pyecma376-2` (Apache License v2.0)
* `urllib3` (MIT License)

Optional production usage dependencies:
* For using the Compliance Tool to validate JSON files against the JSON Schema: `jsonschema` and its
dependencies (MIT License, Apache License, PSF License)

Development/testing/documentation/example dependencies (see `requirements.txt`):
* `jsonschema` and its dependencies (MIT License, Apache License, PSF License)
* `psutil` (BSD 3-clause License)
* `Sphinx` and its dependencies (multiple licenses)
* `sphinx-rtd-theme` and its dependencies
* `sphinx-argparse` (MIT License)

Dependencies for building the documentation:
* `Sphinx` and its dependencies (BSD 2-clause License, MIT License, Apache License)
* `sphinx-rtd-theme` and its dependencies (MIT License, PSF License)
* `sphinx-argparse` (MIT License)


## Getting Started

### Installation

Eclipse BaSyx Python SDK can be installed from PyPI, the Python Package Index, just as nearly every other Python package:
```bash
pip install basyx-python-sdk
``` 

For working with the current development version, you can also install the package directly from GitHub, using Pip's Git feature:
```bash
pip install git+https://github.com/eclipse-basyx/basyx-python-sdk.git@main
```

You may want to use a Python's `venv` or a similar tool to install BaSyx Python SDK and its dependencies only in a project-specific local environment. 


### Example

The following code example shows how to create a `Submodel` with a `Property` serialize it into an XML file using the
Eclipse BaSyx Python SDK:

Create a `Submodel`:
```python
from basyx.aas import model  # Import all BaSyx Python SDK classes from the model package

identifier = 'https://acplt.org/Simple_Submodel'
submodel = model.Submodel(identifier)
```

Create a `Property` and add it to the `Submodel`:
```python
# create an external reference to a semantic description of the property
semantic_reference = model.ExternalReference(
    (model.Key(
        type_=model.KeyTypes.GLOBAL_REFERENCE,
        value='http://acplt.org/Properties/SimpleProperty'
    ),)
)
property = model.Property(
    id_short='ExampleProperty',  # Identifying string of the element within the submodel namespace
    value_type=model.datatypes.String,  # Data type of the value
    value='exampleValue',  # Value of the property
    semantic_id=semantic_reference  # set the semantic reference
)
submodel.submodel_element.add(property)
```

Serialize the `Submodel` to XML:
```python
from basyx.aas.adapter import write_aas_xml_file

data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
data.add(submodel)
with open('Simple_Submodel.xml', 'w', encoding='utf-8') as f:
    write_aas_xml_file(file=f, data=data)
```


### Examples and Tutorials

For further examples and tutorials, check out the `basyx.aas.examples`-package. Here is a quick overview:

* [`tutorial_create_simple_aas`](./basyx/aas/examples/tutorial_create_simple_aas.py): Create an Asset Administration Shell, including an Asset object and a Submodel
* [`tutorial_storage`](./basyx/aas/examples/tutorial_storage.py): Manage a larger number of Asset Administration Shells in an ObjectStore and resolve references
* [`tutorial_serialization_deserialization`](./basyx/aas/examples/tutorial_serialization_deserialization.py): Use the JSON and XML serialization/deserialization for single objects or full standard-compliant files
* [`tutorial_aasx`](./basyx/aas/examples/tutorial_aasx.py): Export Asset Administration Shells with related objects and auxiliary files to AASX package files
* [`tutorial_backend_couchdb`](./basyx/aas/examples/tutorial_backend_couchdb.py): Use the *Backends* interface (`update()/commit()` methods) to manage and retrieve AAS objects in a CouchDB document database


### Documentation

A detailed, complete API documentation is available on Read the Docs: https://basyx-python-sdk.readthedocs.io

### Compliance Tool

The Eclipse BaSyx Python SDK project contains a compliance tool for testing xml and json files is provided in the 
`basyx.aas.compliance_tool`-package. Following functionalities are supported:

* create an xml or json file compliant to the official schema containing example Asset Administration Shell elements
* create an aasx file with xml or json files compliant to the official schema containing example Asset Administration 
Shell elements
* check if a given xml or json file is compliant to the official schema
* check if a given xml, json or aasx file is readable even if it is not compliant to the offical schema
* check if the data in a given xml, json or aasx file is the same as the example data
* check if two given xml, json or aasx files contain the same Asset Administration Shell elements in any order 

Invoking should work with either `python -m basyx.aas.compliance_tool.cli` or (when installed correctly and PATH is set 
correctly) with `aas-compliance-check` on the command line.

For further usage information consider the `basyx.aas.compliance_tool`-package or invoke with 
`python -m basyx.aas.compliance_tool.cli --help` respectively `aas-compliance-check --help`.

## Contributing

For contributing with issues and code, please see our [Contribution Guideline](CONTRIBUTING.md).

### Eclipse Contributor Agreement

To contribute code to this project you need to sign the [Eclipse Contributor Agreement (ECA)](https://www.eclipse.org/legal/ECA.php).
This is done by creating an Eclipse account for your git e-mail address and then submitting the following form: https://accounts.eclipse.org/user/eca
