
# PyI40AAS – Python Industry 4.0 Asset Administration Shell

The PyI40AAS project aims to provide an implementation of the Asset Administration Shell for Industry 4.0 Systems, compliant
with the meta model and interface specification provided in
[the document “Details of the Asset Administration Shell” (v2.0)](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details-of-the-Asset-Administration-Shell-Part1.html).
The implementation will include the data model as well as interface adapters for serving, retrieving, importing and
exporting Asset Administration Shells.


## Features

The `aas`-package provides the following features:

* Modelling of Asset Administration Shells as Python objects
* (de)-serialization of Asset Administration Shells from and to python objects 
(currently supported file/text formats: `JSON`, `XML`)
* `CouchDB`-storage backend
* Compliance Checks to `JSON` and `XML` schemas

### Project Structure

The `aas`-package is structured into 5 submodules. For an overview, consider this project structure:

* `aas.model`: The AAS metamodel implemented in python
* `aas.adapter`: Adapter to various file formats
* `aas.compliance_tools`: Check compliance to `JSON` and `XML` schemas
* `aas.util`: Provides utilities
* `aas.examples`: Examples and tutorials


## Getting Started

### Installation

For most users, the recommended method to install is via pip:

```python
pip install pyi40aas
```


### Example

Creation of a `Submodel` with a `Propery` and serialization of said `Submodel` to `XML`:

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

Serialize the `Submodel` to `XML`:
```python
import aas.adapter.xml.xml_serialization

data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
data.add(submodel)
file = io.BytesIO()
aas.adapter.xml.xml_serialization.write_aas_xml_file(file=file, data=data)
```


### Examples and Tutorials

For further examples and tutorials, check out the `aas.examples`-package. Here is a quick overview:

* `examples.tutorial_create_simple_aas`: Create an Asset Administration Shell, containing an asset reference and a 
submodel reference
* `examples.tutorial_serialization_deserialization_json`: Tutorial for the serialization and deserialization of asset 
administration shells, submodels and assets
* `examples.tutorial_storage`: Tutorial for storing asset administration shells, submodels and assets
* `examples.data`: Package containing simple creator functions for various example objects for testing purposes 


## Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.


### Codestyle and Testing

Our code follows the [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/) and especially
the in [PEP 484 -- Type Hints](https://www.python.org/dev/peps/pep-0484/) introduced type hints in the form:
```python
def function(variable: type) -> type:
    """
    This line is a short description of the function
    
    In this optional line(s) you can have a long description, or annotations for using this function

    :param variable: Here the variable is explained
    :return: Here the return of the function is explained
    """
    do something
    return object
```
Before pushing anything to the repository, make sure that you test your changes with `mypy`, `pycodestyle` and 
`unittest`. To install those, use:
```
pip install mypy
pip install pycodestyle
```

The tests for the `unittest` are located in the `test`-package, which has the same structure as the `aas`-package. We
expect at least 80% coverage per module.

Please make sure that running:
```
mypy aas test
python -m pycodestyle --max-line-length 120 aas test
python -m unittest
```
does not result in any error, before pushing.


### Contribute Code/Patches



## License

The PyI40AAS project is provided under the terms of the Apache License (Version 2.0).

For more information, especially considering the licenses of included third-party works, please consult the `NOTICE`
file. 
