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
Example for the creation of an simple asset administration shell object containing an asset reference and a submodel
reference step by step
"""

# to get all functions import model
from aas import model

# step 1: create an simple asset, for detailed information look at 'example_create_simple_aas.py'
asset = model.Asset(
    kind=model.AssetKind.INSTANCE,
    identification=model.Identifier('https://acplt.org/Simple_Asset', model.IdentifierType.IRI),
)

# step 2: create a simple submodel with zero submodel element
identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
submodel = model.Submodel(
    identification=identifier,  # set identifier
)

# step 3: create a simple property and add it to the submodel
# step 3.1: create a global reference to a semantic description of the property
# A global reference consist of one key which points to the address where the semantic description is stored
reference = model.Reference(
    (model.Key(
        type_=model.KeyElements.GLOBAL_REFERENCE,
        local=False,
        value='http://acplt.org/Properties/SimpleProperty',
        id_type=model.KeyType.IRI
    ),)
)
# step 3.2: create the simple property
property = model.Property(
        id_short='ExampleProperty',  # Identifying string of the element within the submodel namespace
        value_type=model.datatypes.String,  # Data type of the value
        value='exampleValue',  # Value of the property
        semantic_id=reference  # set the semantic reference
)
# step 3.3: add the property to the submodel
submodel.submodel_element.add(property)

# step 4: create a simple asset administration shell containing a reference to the asset and add the submodel reference
# step 4.1: create the asset administration shell
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset),  # set the reference to the asset
)
# step 4.2: add the submodel reference
aas.submodel.add(model.AASReference.from_referable(submodel))

# both steps can also be done in one step
# identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
# aas = model.AssetAdministrationShell(
#     identification=identifier,  # set identifier
#     asset=model.AASReference.from_referable(asset),  # set the reference to the asset
#     submodel_={model.AASReference.from_referable(submodel)}
# )
