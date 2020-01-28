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
Example for the creation of an simple asset administration shell object containing an asset reference step by step
"""

# to get all functions import model
from aas import model

# for creating an asset administration shell you need an asset for which you want to create an asset administration
# shell

# step 1: create an simple asset

# step 1.1: create an identifier for the asset
# chose the type of the identifier which are defined in the enumeration "IdentifierType", here we use an IRI
id_type = model.IdentifierType.IRI
# define the IRI of the asset
id_ = 'https://acplt.org/Simple_Asset'
# create the identifier
identifier = model.Identifier(id_, id_type)

# step 1.2: create the simple asset
asset = model.Asset(
    kind=model.AssetKind.INSTANCE,  # define that the asset is of kind instance
    identification=identifier,      # set identifier
)

# step 2: create a simple asset administration shell containing a reference to the asset containing zero submodels
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset),  # set the reference to the asset
)
