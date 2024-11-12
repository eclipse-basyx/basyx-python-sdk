# Eclipse BaSyx Python SDK

(formerly known as PyI40AAS – Python Industry 4.0 Asset Administration Shell)

The Eclipse BaSyx Python project focuses on providing a Python implementation of the Asset Administration Shell (AAS) 
for Industry 4.0 Systems. 
These are the currently implemented specifications:

| Specification                         | Version                                                                                                                                                                        |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Part 1: Metamodel                     | [v3.0 (01001-3-0)](https://industrialdigitaltwin.org/wp-content/uploads/2023/06/IDTA-01001-3-0_SpecificationAssetAdministrationShell_Part1_Metamodel.pdf)                      |
| Part 2: API                           | [v3.0 (01002-3-0)](https://industrialdigitaltwin.org/en/wp-content/uploads/sites/2/2023/06/IDTA-01002-3-0_SpecificationAssetAdministrationShell_Part2_API_.pdf)                |
| Part 3a: Data Specification IEC 61360 | [v3.0 (01003-a-3-0)](https://industrialdigitaltwin.org/wp-content/uploads/2023/04/IDTA-01003-a-3-0_SpecificationAssetAdministrationShell_Part3a_DataSpecification_IEC61360.pdf) |
| Part 5: Package File Format (AASX)    | [v3.0 (01005-3-0)](https://industrialdigitaltwin.org/wp-content/uploads/2023/04/IDTA-01005-3-0_SpecificationAssetAdministrationShell_Part5_AASXPackageFileFormat.pdf)          |

## Features
This repository is structured into separate packages. 
The `sdk` directory provides the AAS metamodel as Python objects and fundamental functionalities to handle AAS.
The `server` is to be determined.
The `compliance_tool` is to be determined.

* SDK
  * Modelling of AASs as Python objects
      * **except for**: *HasDataSpecification*
  * Reading and writing of AASX package files
  * (De-)serialization of AAS objects into/from JSON and XML
  * Storing of AAS objects in CouchDB, Backend infrastructure for easy expansion 
  * Compliance checking of AAS XML and JSON files
* Server (tbd)
* Compliance Tool (tbd)

## License

The BaSyx Python SDK project is licensed under the terms of the MIT License.

SPDX-License-Identifier: MIT

For more information, especially considering the licenses of included third-party works, please consult the `NOTICE`
file.

## Release Schedule

The Eclipse BaSyx-Python SDK Team evaluates bi-monthly the newly added commits to the main branch towards the need 
of releasing a new version.
If decided the changes warrant a release, it is initiated, using semantic versioning for the new release number.
If the changes do not warrant a release, the decision is postponed to the next meeting.

Additionally, security fixes may be released at any point.

## Contributing

For contributing with issues and code, please see our [Contribution Guideline](./CONTRIBUTING.md).

### Eclipse Contributor Agreement

To contribute code to this project you need to sign the [Eclipse Contributor Agreement (ECA)](https://www.eclipse.org/legal/ECA.php).
This is done by creating an Eclipse account for your git e-mail address and then submitting the following form: https://accounts.eclipse.org/user/eca
