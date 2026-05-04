# Eclipse BaSyx Python SDK

[![CI](https://github.com/eclipse-basyx/basyx-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/eclipse-basyx/basyx-python-sdk/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/basyx-python-sdk)](https://pypi.org/project/basyx-python-sdk/)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/basyx-python-sdk)](https://anaconda.org/conda-forge/basyx-python-sdk)
[![PyPI Downloads](https://img.shields.io/pypi/dm/basyx-python-sdk)](https://pypi.org/project/basyx-python-sdk/)
[![Python Version](https://img.shields.io/pypi/pyversions/basyx-python-sdk)](https://pypi.org/project/basyx-python-sdk/)
[![License](https://img.shields.io/github/license/eclipse-basyx/basyx-python-sdk)](LICENSE)

The Eclipse BaSyx Python SDK is a Python implementation of the
[Asset Administration Shell (AAS)](https://industrialdigitaltwin.org/en/content-hub/aasspecifications)
for Industry 4.0 systems. It lets you model, serialize, validate, store, and serve AAS data
entirely in Python.

The project is part of the [Eclipse BaSyx](https://www.eclipse.org/basyx/) middleware
framework, developed under the umbrella of the Eclipse Foundation.

## Specification Compliance

> [!NOTE]
> The SDK version number is independent of the supported AAS specification versions.

These are the AAS specifications implemented by the
[current release](https://github.com/eclipse-basyx/basyx-python-sdk/releases/latest),
which can also be found on [PyPI](https://pypi.org/project/basyx-python-sdk/) and
[conda-forge](https://anaconda.org/conda-forge/basyx-python-sdk):

| Specification | Version |
|---|---|
| Part 1: Metamodel | [v3.0.1 (01001-3-0-1)](https://industrialdigitaltwin.org/wp-content/uploads/2024/06/IDTA-01001-3-0-1_SpecificationAssetAdministrationShell_Part1_Metamodel.pdf) |
| Schemata (JSONSchema, XSD) | [v3.0.8 (IDTA-01001-3-0-1_schemasV3.0.8)](https://github.com/admin-shell-io/aas-specs/releases/tag/IDTA-01001-3-0-1_schemasV3.0.8) |
| Part 2: API | [v3.0 (01002-3-0)](https://industrialdigitaltwin.org/en/wp-content/uploads/sites/2/2023/06/IDTA-01002-3-0_SpecificationAssetAdministrationShell_Part2_API_.pdf) |
| Part 3a: Data Specification IEC 61360 | [v3.0 (01003-a-3-0)](https://industrialdigitaltwin.org/wp-content/uploads/2023/04/IDTA-01003-a-3-0_SpecificationAssetAdministrationShell_Part3a_DataSpecification_IEC61360.pdf) |
| Part 5: Package File Format (AASX) | [v3.0 (01005-3-0)](https://industrialdigitaltwin.org/wp-content/uploads/2023/04/IDTA-01005-3-0_SpecificationAssetAdministrationShell_Part5_AASXPackageFileFormat.pdf) |

For older specification support, consult the [prior releases](https://github.com/eclipse-basyx/basyx-python-sdk/releases) —
each release has a similar table in its notes.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
- [Examples and Tutorials](#examples-and-tutorials)
- [FAQ](#faq)
- [Release Schedule](#release-schedule)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

This mono-repository contains three self-contained Python packages that cover different
aspects of working with Asset Administration Shells:

| Package | Purpose |
|---------|---------|
| **[SDK](./sdk)** | Core library — AAS metamodel, serialization, storage |
| **[Server](./server)** | Spec-compliant AAS HTTP/REST server (Docker) |
| **[Compliance Tool](./compliance_tool)** | CLI checker for AAS file compliance |

### SDK

The SDK (`basyx-python-sdk` on PyPI / conda-forge) is the core of this project. It provides:

- **AAS Metamodel** — full Python object model of the AAS metamodel (Part 1)
- **Serialization** — read and write AAS data as JSON, XML, or AASX package files
- **Backend Storage** — persist AAS objects in CouchDB or as local JSON files, with an
  extensible backend interface
- **Experimental RDF Support** — serialization to RDF is available on the
  [Experimental/Adapter/RDF](https://github.com/eclipse-basyx/basyx-python-sdk/tree/Experimental/Adapter/RDF/basyx/aas/adapter/rdf)
  branch (see [#308](https://github.com/eclipse-basyx/basyx-python-sdk/pull/308) for context)

### Server

A Docker image that exposes a specification-compliant HTTP/REST API (AAS Part 2), currently
implementing the following service interfaces:

- Asset Administration Shell Repository
- Submodel Repository
- AAS Registry
- AAS Discovery

It can serve AAS data from AASX, JSON, or XML files, optionally with persistent
storage via the Local-File Backend.

### Compliance Tool

A command-line utility for checking whether AAS JSON, XML, or AASX files conform to the
official schema. Useful for CI pipelines, data validation, and interoperability testing.

---

## Getting Started

Each package in this repository can be set up independently. Refer to the package-level
READMEs for detailed installation instructions, usage examples, and configuration options:

- **SDK** — [Getting Started with the SDK](./sdk/README.md#getting-started) (install from
  PyPI or conda-forge, quick code example, tutorials)
- **Server** — [Running the Server](./server/README.md#running) (Docker build & run,
  environment variables, persistence options)
- **Compliance Tool** — [Using the Compliance Tool](./compliance_tool/README.md)
  (install, command-line usage)

---

## Examples and Tutorials

### SDK Tutorials

The SDK ships with step-by-step tutorials in `sdk/basyx/aas/examples/`:

| Tutorial | What You Will Learn |
|---|---|
| [Create a Simple AAS](./sdk/basyx/aas/examples/tutorial_create_simple_aas.py) | Build an Asset Administration Shell with an Asset and a Submodel from scratch |
| [Navigate Submodels](./sdk/basyx/aas/examples/tutorial_navigate_aas.py) | Traverse AAS Submodels using IdShorts and IdShortPaths |
| [Object Storage](./sdk/basyx/aas/examples/tutorial_storage.py) | Manage many AAS objects with ObjectStores and resolve references |
| [Serialization & Deserialization](./sdk/basyx/aas/examples/tutorial_serialization_deserialization.py) | Read and write AAS data as JSON and XML |
| [AASX Packages](./sdk/basyx/aas/examples/tutorial_aasx.py) | Export AAS shells with related objects and auxiliary files to AASX packages |
| [CouchDB Backend](./sdk/basyx/aas/examples/tutorial_backend_couchdb.py) | Store and retrieve AAS objects in a CouchDB document database |

### Server Example Configurations

Ready-to-use Docker Compose configurations can be found in `server/example_configurations/`:

| Configuration | Description |
|---|---|
| [Repository Standalone](./server/example_configurations/repository_standalone) | Standalone AAS and Submodel repository server |
| [Registry Standalone](./server/example_configurations/registry_standalone) | Standalone AAS and Submodel registry service |
| [Discovery Standalone](./server/example_configurations/discovery_standalone) | Standalone AAS discovery service |

---

## FAQ

**I can't read a JSON/XML/AASX file from another tool with this SDK. What should I do?**

The SDK enforces strict compliance with the AAS specification. Files produced by other tools
may not fully conform. To diagnose the issue:

1. Check that the file targets the same AAS specification version supported by this SDK
   (see the [Specification Compliance](#specification-compliance) table above).
2. Run the [Compliance Tool](./compliance_tool/README.md) on the file to identify any
   schema violations.
3. If the file is spec-compliant and the SDK still rejects it, please
   [open an issue](https://github.com/eclipse-basyx/basyx-python-sdk/issues/new) with the
   error message and, if possible, a minimal example file.

**Can I run the server without Docker?**

Yes, for debugging purposes. See the
[Server README](./server/README.md#running-without-docker-debugging-only) for instructions.
This mode is not suitable for production.

---

## Release Schedule

The Eclipse BaSyx Python SDK team meets bi-monthly to evaluate whether the changes accumulated
on the `develop` branch warrant a new release. If so, `develop` is merged into `main` and a
new version is published to
[PyPI](https://pypi.org/project/basyx-python-sdk/) and
[conda-forge](https://anaconda.org/conda-forge/basyx-python-sdk)
using [semantic versioning](https://semver.org/). If not, the decision is deferred to the
next meeting. Security fixes may be released at any time.

---

## Contributing

We welcome contributions of all kinds — bug reports, feature requests, documentation
improvements, and code. Please read our [Contribution Guideline](./CONTRIBUTING.md) before
getting started.

### Eclipse Contributor Agreement

To contribute code, you must sign the
[Eclipse Contributor Agreement (ECA)](https://www.eclipse.org/legal/ECA.php).
Create an Eclipse account with the same email address you use for Git commits, then submit
the form at: https://accounts.eclipse.org/user/eca

---

## License

This project is licensed under the terms of the **MIT License**.

SPDX-License-Identifier: MIT

For details on third-party dependencies and their licenses, see the [NOTICE](./NOTICE) file.
