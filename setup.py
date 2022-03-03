#!/usr/bin/env python3
# Copyright (c) 2019-2021 the Eclipse BaSyx Authors
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
    name="basyx-python-sdk",
    version="0.2.2",
    author="The Eclipse BaSyx Authors",
    description="The Eclipse BaSyx Python SDK, an implementation of the Asset Administration Shell for Industry 4.0 "
                "systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eclipse-basyx/basyx-python-sdk",
    packages=setuptools.find_packages(exclude=["test", "test.*"]),
    zip_safe=False,
    package_data={
        "basyx": ["py.typed"],
        "basyx.aas.adapter.json": ["aasJSONSchema.json"],
        "basyx.aas.adapter.xml": ["AAS.xsd", "AAS_ABAC.xsd", "IEC61360.xsd"],
        "basyx.aas.examples.data": ["TestFile.pdf"],
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
            "aas-compliance-check = basyx.aas.compliance_tool.cli:main"
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
