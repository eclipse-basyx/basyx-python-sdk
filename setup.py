#!/usr/bin/env python3
# Copyright (c) 2019-2021 PyI40AAS Contributors
#
# This program and the accompanying materials are made available under the terms of the Eclipse Public License v. 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0 which is available
# at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0

import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyi40aas",
    version="0.2.2",
    author="Chair of Process Control Engineering, RWTH Aachen",
    author_email="m.thies@plt.rwth-aachen.de",
    description="An implementation of the Asset Administration Shell for Industry 4.0 systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.rwth-aachen.de/acplt/pyi40aas",
    packages=setuptools.find_packages(exclude=["test", "test.*"]),
    zip_safe=False,
    package_data={
        "aas": ["py.typed"],
        "aas.adapter.json": ["aasJSONSchema.json"],
        "aas.adapter.xml": ["AAS.xsd", "AAS_ABAC.xsd", "IEC61360.xsd"],
        "aas.examples.data": ["TestFile.pdf"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    entry_points={
        'console_scripts': [
            "aas_compliance_check = aas.compliance_tool.cli:main"
        ]
    },
    python_requires='>=3.6',
    install_requires=[
        'python-dateutil>=2.8,<3',
        'lxml>=4.2,<5',
        'urllib3>=1.26<2.0',
        'pyecma376-2>=0.2.4',
    ]
)
