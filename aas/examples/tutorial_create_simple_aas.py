# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the creation of an simple asset administration shell containing a asset reference and a submodel
reference
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
    identification=identifier       # set identifier
)

########################################################################################################################
# step 2: create a simple submodel with zero submodel element
identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
submodel = model.Submodel(
    identification=identifier  # set identifier
)

########################################################################################################################
# step 3: create a simple asset administration shell containing a reference to the asset and add the submodel reference
# step 3.1: create the asset administration shell
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset)  # set the reference to the asset
)
# step 3.2: add the submodel reference
aas.submodel.add(model.AASReference.from_referable(submodel))
# both steps can also be done in one step
# identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
# aas = model.AssetAdministrationShell(
#     identification=identifier,  # set identifier
#     asset=model.AASReference.from_referable(asset),  # set the reference to the asset
#     submodel_={model.AASReference.from_referable(submodel)}
# )

########################################################################################################################
# step 4: create a simple property and add it to the submodel
# step 4.1: create a global reference to a semantic description of the property
# A global reference consist of one key which points to the address where the semantic description is stored
semantic_reference = model.Reference(
    (model.Key(
        type_=model.KeyElements.GLOBAL_REFERENCE,
        local=False,
        value='http://acplt.org/Properties/SimpleProperty',
        id_type=model.KeyType.IRI
    ),)
)
# step 4.2: create the simple property
property = model.Property(
        id_short='ExampleProperty',  # Identifying string of the element within the submodel namespace
        value_type=model.datatypes.String,  # Data type of the value
        value='exampleValue',  # Value of the property
        semantic_id=semantic_reference  # set the semantic reference
)
# step 4.3: add the property to the submodel
submodel.submodel_element.add(property)
