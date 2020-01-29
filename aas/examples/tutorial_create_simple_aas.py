# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the creation of an simple asset administration shell containing a asset reference and a submodel
reference
"""

# to get all functions import model
from aas import model

# In this tutorial you get a step by step guide how to create an asset administration shell and its needed objects.
# First you need an asset for which you want to create an asset administration shell. So first you will learn how to
# create an asset. After that you learn how to create an asset administration shell containing a reference to the
# asset. Now it is possible, to add submodels to the asset administration shell. Therefore, you learn how to create a
# submodel and how to add the reference to it to the asset administration shell. The submodel can contain submodel
# elements. Therefore, you will also learn how to create a submodel element and how to add it to the submodel.
# Step by step guide:
# step 1: create a simple asset
# step 2: create a simple asset administration shell containing a reference to the asset
# step 3: create a simple submodel
# step 4: create a simple property and add it to the submodel

##################################
# step 1: create a simple asset #
##################################
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
    identification=identifier  # set identifier
)

##########################################################################################
# step 2: create a simple asset administration shell containing a reference to the asset #
##########################################################################################
# step 2.1: create the asset administration shell
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset)  # set the reference to the asset
)

###############################################################
# step 3: create a simple submodel with zero submodel element #
###############################################################
# step 3.1 create the identifier of the submodel
identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
submodel = model.Submodel(
    identification=identifier  # set identifier
)
# step 3.2: add the submodel reference to the asset administration shell
aas.submodel.add(model.AASReference.from_referable(submodel))

# step 2 and 3 can also be done in one step
# identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
# aas = model.AssetAdministrationShell(
#     identification=identifier,
#     asset=model.AASReference.from_referable(asset),
#     submodel_={model.AASReference.from_referable(submodel)}
# )

###############################################################
# step 4: create a simple property and add it to the submodel #
###############################################################
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

# step 3 and 4 can also be done in one step
# submodel = model.Submodel(
#     identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI),
#     submodel_element={
#         model.Property(
#             id_short='ExampleProperty',
#             value_type=model.datatypes.String,
#             value='exampleValue',
#             semantic_id=model.Reference(
#                 (model.Key(
#                     type_=model.KeyElements.GLOBAL_REFERENCE,
#                     local=False,
#                     value='http://acplt.org/Properties/SimpleProperty',
#                     id_type=model.KeyType.IRI
#                 ),)
#             )
#         )
#     }
# )
