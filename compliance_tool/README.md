# AAS Compliance Tool
An AAS compliance checker based on the [Eclipse BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk) for testing XML and JSON files.
Following functionalities are supported:

* create an xml or json file compliant to the official schema containing example Asset Administration Shell elements
* create an aasx file with xml or json files compliant to the official schema containing example Asset Administration 
Shell elements
* check if a given xml or json file is compliant to the official schema
* check if a given xml, json or aasx file is readable even if it is not compliant to the official schema
* check if the data in a given xml, json or aasx file is the same as the example data
* check if two given xml, json or aasx files contain the same Asset Administration Shell elements in any order 

## Installation

### Default installation
Install the latest release from PyPI:

```bash
pip install basyx-compliance-tool
```

### Developer installation
When working from a checkout of this repository, install the sibling SDK from the source tree *first*, then the 
compliance tool:

```bash
pip install ./sdk
pip install ./compliance_tool
```

Installing the local SDK first is what lets the tool check against your in-development metamodel: `pip` keeps the 
already-installed local SDK instead of pulling a release from PyPI.

> [!IMPORTANT]
> The compliance checks are only as current as the installed `basyx-python-sdk` — the tool reports compliance against 
> whatever metamodel version that SDK implements, not against the version named in this README. Because the dependency 
> is currently declared loosely (`basyx-python-sdk>=1.0.0`), `pip` will **not** replace an SDK that is already installed 
> and satisfies that constraint, even if it is older than the one you intend to test against. This happens silently, with 
> no error. To be sure you are checking against the intended metamodel, install or upgrade the SDK explicitly, e.g. the 
> local source tree with `pip install ./sdk` or a specific release with `pip install --upgrade "basyx-python-sdk==2.1.0"`.
>
> This manual version matching is a temporary workaround; see #592.

## Usage
Invoking should work with either `python -m aas_compliance_tool.cli` or (when installed correctly and PATH is set 
correctly) with `aas-compliance-check` on the command line.

For further usage information consider the `aas_compliance_tool`-package or invoke with 
`python -m aas_compliance_tool.cli --help` respectively `aas-compliance-check --help`.
