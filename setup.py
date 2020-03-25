#!/usr/bin/env python3
# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyi40aas",
    version="0.0.1",
    author="Chair of Process Control Engineering, RWTH Aachen",
    author_email="m.thies@plt.rwth-aachen.de",
    description="An implementation of the Asset Administration Shell for Industry 4.0 systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.rwth-aachen.de/acplt/pyaas",
    packages=setuptools.find_packages(),
    zip_safe=False,
    package_data={"aas": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
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
        'pyecma376-2>=0.2',
    ]
)
