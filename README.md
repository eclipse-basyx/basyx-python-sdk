
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

Following `examples.tutorial_create_simple_ass`, these are the steps to take to set up an exemplary 
Asset Administration Shell with PyI40AAS:

First, we create an `Asset`, for which we need an `Identifier`:
```python
from aas import model  # Import all PYI40AAS classes from the model package

id_type = model.IdentifierType.IRI
id_ = 'https://acplt.org/Simple_Asset'
identifier = model.Identifier(id_, id_type)
asset = model.Asset(
    kind=model.AssetKind.INSTANCE,  # define that the asset is of kind instance
    identification=identifier  # set identifier
)
```
Now, we can create the `AssetAdministrationShell`, which needs an `Identifier` as well. The method 
`model.AASReference.from_referable()` lets us create a `Reference` to the `Asset` we just created from the asset itself,
in order to add it to our `AssetAdministrationShell`.
```python
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset)
)
```
Congratulations: Now you have created your first `AssetAdministrationShell` with PyI40AAS. From here, you can continue
by creating submodels (`model.Submodel`) and submodel elements like properties (`model.Property`). 

Alternatively you can look into storing the information your `AssetAdministrationShell` contains, either with JSON, XML 
or CouchDB.


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

The tests for the `unittest` are located in the `test`-package, which has the same structure as the `aas`-package. We use
the `unittest`-package for writing the test and expect at least 80% coverage.

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
