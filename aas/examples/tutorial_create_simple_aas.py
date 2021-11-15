#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the creation of an simple Asset Administration Shell, containing an Asset reference and a Submodel
reference
"""

# Import all Eclipse BaSyx Python SDK classes from model package
from aas import model

# In this tutorial, you'll get a step by step guide on how to create an Asset Administration Shell (AAS) and all
# required objects within. First, you need an asset for which you want to create an AAS, represented by an Asset object.
# After that, an Asset Administration Shell can be created, containing a reference to that Asset. Then, it's possible to
# add Submodels to the AAS. The Submodels can contain SubmodelElements.
#
# Step by Step Guide:
# step 1: create a simple Asset object
# step 2: create a simple Asset Administration Shell, containing a reference to the Asset
# step 3: create a simple Submodel
# step 4: create a simple Property and add it to the Submodel


#################################
# Step 1: Create a Simple Asset #
#################################

# step 1.1: create an identifier for the Asset
# Here we use an IRI identifier
identifier = model.Identifier(id_='https://acplt.org/Simple_Asset',
                              id_type=model.IdentifierType.IRI)

# step 1.2: create the Asset object
asset = model.Asset(
    kind=model.AssetKind.INSTANCE,  # define that the Asset is of kind instance
    identification=identifier  # set identifier
)


##########################################################################################
# Step 2: Create a Simple Asset Administration Shell Containing a Reference to the Asset #
##########################################################################################

# step 2.1: create the Asset Administration Shell
identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
aas = model.AssetAdministrationShell(
    identification=identifier,  # set identifier
    asset=model.AASReference.from_referable(asset)  # generate a Reference object to the Asset (using its identifier)
)


#############################################################
# step 3: Create a Simple Submodel Without SubmodelElements #
#############################################################

# step 3.1: create the Submodel object
identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
submodel = model.Submodel(
    identification=identifier
)

# step 3.2: create a reference to that Submodel and add it to the Asset Administration Shell's `submodel` set
aas.submodel.add(model.AASReference.from_referable(submodel))


# ===============================================================
# ALTERNATIVE: step 2 and 3 can alternatively be done in one step
# In this version, the Submodel reference is passed to the Asset Administration Shell's constructor.
submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
)
aas = model.AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset=model.AASReference.from_referable(asset),
    submodel={model.AASReference.from_referable(submodel)}
)


###############################################################
# step 4: Create a Simple Property and Add it to the Submodel #
###############################################################

# step 4.1: create a global reference to a semantic description of the Property
# A global reference consist of one key which points to the address where the semantic description is stored
semantic_reference = model.Reference(
    (model.Key(
        type_=model.KeyElements.GLOBAL_REFERENCE,
        local=False,
        value='http://acplt.org/Properties/SimpleProperty',
        id_type=model.KeyType.IRI
    ),)
)

# step 4.2: create the simple Property
property_ = model.Property(
    id_short='ExampleProperty',  # Identifying string of the element within the Submodel namespace
    value_type=model.datatypes.String,  # Data type of the value
    value='exampleValue',  # Value of the Property
    semantic_id=semantic_reference  # set the semantic reference
)

# step 4.3: add the Property to the Submodel
submodel.submodel_element.add(property_)


# =====================================================================
# ALTERNATIVE: step 3 and 4 can also be combined in a single statement:
# Again, we pass the Property to the Submodel's constructor instead of adding it afterwards.
submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI),
    submodel_element={
        model.Property(
            id_short='ExampleProperty',
            value_type=model.datatypes.String,
            value='exampleValue',
            semantic_id=model.Reference(
                (model.Key(
                    type_=model.KeyElements.GLOBAL_REFERENCE,
                    local=False,
                    value='http://acplt.org/Properties/SimpleProperty',
                    id_type=model.KeyType.IRI
                ),)
            )
        )
    }
)
