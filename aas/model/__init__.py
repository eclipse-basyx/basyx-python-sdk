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
"""
This package contains a python implementation of the meta-model of the AssetAdministrationShell.
The model is divided into 5 modules, splitting it where it in sensible parts.

aas.py
    The main module, implementing high-level structures, such as AssetAdministrationShell, Asset and ConceptDictionary.

base.py
    Basic structures of the model, including all abstract classes and enumerations. This provides inheritance for the
    higher level structures.

registry.py
    Registries for the AAS, in order to enable resolving global identifiers; and mapping identifiers to identifiable
    objects.

security.py
    Security model of the AAS. Currently not existing.

submodel.py
    Meta-model of the submodels and events.
"""

from .aas import *
from .security import *
from .base import *
from .submodel import *
from .registry import *
