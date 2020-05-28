
# PyI40AAS – Python Industry 4.0 Asset Administration Shell

The PyI40AAS project aims to provide an implementation of the Asset Administration Shell (AAS) for Industry 4.0 Systems, compliant
with the meta model and interface specification provided in
[the document “Details of the Asset Administration Shell” (v2.0)](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details-of-the-Asset-Administration-Shell-Part1.html).


## Features

* Modelling of AASs as Python objects (according to DotAAS sec. 4)
* (De-)serialization of AAS objects into/from JSON and XML (according to DotAAS sec. 5) 
* Reading and writing of AASX package files (according to DotAAS sec. 7)
* Storing of AAS objects in CouchDB
* Compliance checking of AAS XML and JSON files


### Project Structure

The PyI40AAS project provides the `aas` Python package with 5 submodules:

* `aas.model`: The AAS metamodel implemented in python
* `aas.adapter`: Adapters for various file formats and storage backends
* `aas.compliance_tools`: Compliance checker for AAS files
* `aas.util`: Provides utilities
* `aas.examples`: Example data and tutorials


## License

The PyI40AAS project is provided under the terms of the Apache License (Version 2.0).

For more information, especially considering the licenses of included third-party works, please consult the `NOTICE`
file.


## Dependencies

PyI40AAS requires the following Python packages to be installed for production usage. These dependencies are listed in
`setup.py` to be fetched automatically when installing with `pip`:
* `python-dateutil` (BSD 3-clause License)
* `lxml` (BSD 3-clause License, using `libxml2` under MIT License)
* `pyecma376-2` (Apache License v2.0)

Optional production usage dependencies:
* For using the Compliance Tool to validate JSON files against the JSON Schema: `jsonschema` and its
dependencies (MIT License, Apache License, PSF License)

Development/testing/example dependencies (see `requirements.txt`):
* `jsonschema` and its dependencies (MIT License, Apache License, PSF License)
* `psutil` (BSD 3-clause License)


## Getting Started

### Installation

For production usage and building applications with PyI40AAS, we recommended installation from PyPI:

```python
pip install pyi40aas
```


### Example

The following code example shows how to create a `Submodel` with a `Property` serialize it into an XML file using PyI40AAS:

Create a `Submodel`:
```python
from aas import model  # Import all PYI40AAS classes from the model package

identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
submodel = model.Submodel(identification=identifier)
```

Create a `Property` and add it to the `Submodel`:
```python
# create a global reference to a semantic description of the property
semantic_reference = model.Reference(
    (model.Key(
        type_=model.KeyElements.GLOBAL_REFERENCE,
        local=False,
        value='http://acplt.org/Properties/SimpleProperty',
        id_type=model.KeyType.IRI
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
from aas.adapter.xml import write_aas_xml_file

data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
data.add(submodel)
with open('Simple_Submodel.xml', 'w', encoding='utf-8') as f:
    write_aas_xml_file(file=f, data=data)
```


### Examples and Tutorials

For further examples and tutorials, check out the `aas.examples`-package. Here is a quick overview:

* `aas.examples.tutorial_create_simple_aas`: Create an Asset Administration Shell, including an Asset object and a 
  Submodel
* `aas.examples.tutorial_storage`: Manage a larger number of Asset Administration Shells in an ObjectStore and resolve
  references
* `aas.examples.tutorial_serialization_deserialization`: Use the JSON and XML serialization/deserialization for
  single objects or full standard-compliant files 
* `aas.examples.tutorial_dynamic_model`: Create a submodel with elements that are dynamically updated from a custom data
  source


### Compliance Tool

The PyI40AAS project contains a compliance tool for testing xml and json files is provided in the 
`aas.compliance_tool`-package. Following functionalities are supported:

* create an xml or json file compliant to the official schema containing example Asset Administration Shell elements
* check if a given xml or json file is compliant to the official schema
* check if a given xml or json file is deserializable even if it is not compliant to the offical schema
* check if the data in a given xml or json file is the same as the example data
* check if two given xml or json file contain the same Asset Administration Shell elements in any order 

Invoking should work with either `python -m aas.compliance_tool.cli` or (when installed correctly and PATH is set 
correctly) with `aas_compliance_check` on the command line.

For further usage information consider the `aas.compliance_tool`-package or invoke with 
`python -m aas.compliance_tool.cli --help` respectively `aas_compliance_check --help`.

## Contributing

If you plan contributing code to the PyI40AAS project, please get in touch with us via E-Mail first: m.thies@plt.rwth-aachen.de


### Codestyle and Testing

Our code follows the [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).
Additionally, we use [PEP 484 -- Type Hints](https://www.python.org/dev/peps/pep-0484/) throughout the code to enable type checking the code.

Before submitting any changes, make sure to let `mypy` and `pycodestyle` check your code and run the unit tests with
Python's builtin `unittest`. To install the required tools, use:
```bash
pip install mypy pycodestyle
```

Running all checks:
```bash
mypy aas test
python -m pycodestyle --max-line-length 120 aas test
python -m unittest
```

We aim to cover our code with test by at least 80%. To check test coverage, you can use `coverage`:

```bash
pip install coverage
coverage run --source aas --branch -m unittest
coverage report -m
```


### Contribute Code/Patches

TBD
