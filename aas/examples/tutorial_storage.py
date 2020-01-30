# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for storing asset administration shells, submodels and assets
"""

# Import all PyI40AAS classes from model package
from aas import model
from aas.model import Asset, AssetAdministrationShell, Submodel

# In this tutorial you get a step by step guide how to store an asset administration shell and its needed objects. For
# storing an asset administration shell including the asset and submodels you need an object store. In an object
# store you can store as many identifiable objects (assets, asset administration shells and submodels) as you want.
# First you will learn how to create an object store and how to add objects to it. After that you will learn how to get
# the objects out of the store using their identifier. At the end you learn how to resolve a reference using the object
# store.
# Step by step guide:
# step 1: create asset, submodel and asset administration shell, for more details look at
#         'tutorial_create_simple_aas.py'
# step 2: store the data in an object store for easier handling
# step 3: get data of objects out of the store using their identifier
# step 4: use the object store for resolving a reference

#########################################################################
# step 1: create example asset, submodel and asset administration shell #
#########################################################################
asset = Asset(
    kind=model.AssetKind.INSTANCE,
    identification=model.Identifier('https://acplt.org/Simple_Asset', model.IdentifierType.IRI)
)
submodel = Submodel(
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
        )}
)
aas = AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset=model.AASReference.from_referable(asset),
    submodel_={model.AASReference.from_referable(submodel)}
)

#################################################################
# step 2: store the data in an object store for easier handling #
#################################################################
# step 2.1: create an object store for identifiable objects (asset administration shell, asset and submodel)
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
# step 2.2: add asset, submodel and asset administration shell to store
obj_store.add(asset)
obj_store.add(submodel)
obj_store.add(aas)

#######################################################################
# step 3: get data of objects out of the store using their identifier #
#######################################################################
tmp_submodel: Submodel = obj_store.get_identifiable(  # type: ignore
    model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI))

assert(submodel == tmp_submodel)
##########################################################
# step 4: use the object store for resolving a reference #
##########################################################
# create a reference to the submodel
submodel_reference = model.AASReference(
    (model.Key(
        type_=model.KeyElements.SUBMODEL,
        local=True,
        value='https://acplt.org/Simple_Submodel',
        id_type=model.KeyType.IRI
    ),),
    type_=model.Submodel
)
tmp_submodel = submodel_reference.resolve(obj_store)
assert(submodel == tmp_submodel)

# create a reference to the property
property_reference = model.AASReference(
    (model.Key(
        type_=model.KeyElements.SUBMODEL,
        local=True,
        value='https://acplt.org/Simple_Submodel',
        id_type=model.KeyType.IRI
    ),
     model.Key(
         type_=model.KeyElements.PROPERTY,
         local=True,
         value='ExampleProperty',
         id_type=model.KeyType.IDSHORT
    ),),
    type_=model.Property
)
tmp_property = property_reference.resolve(obj_store)
