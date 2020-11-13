#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for storing Asset Administration Shells, Submodels and Assets in an ObjectStore and using it for fetching these
objects by identification and resolving references.
"""

# For managing a larger number of Identifiable AAS objects (AssetAdministrationShells, Assets, Submodels,
# ConceptDescriptions), the PyI40AAS library provides the `ObjectStore` functionality. This tutorial shows the basic
# features of an ObjectStore and how to use them. This includes usage of the built-in `resolve()` method of Reference
# objects, which can be used to easily get the Submodel objects, which are referenced by the
# `AssetAdministrationShell.submodel` set, etc.
#
# Step by Step Guide:
# step 1: creating Asset, Submodel and Asset Administration Shell objects
# step 2: storing the data in an ObjectStore for easier handling
# step 3: retrieving objects from the store by their identifier
# step 4: using the ObjectStore to resolve a reference


from aas import model
from aas.model import Asset, AssetAdministrationShell, Submodel


###########################################################################
# Step 1: Creating Asset, Submodel and Asset Administration Shell objects #
###########################################################################

# For more details, take a look at `tutorial_create_simple_aas.py`

asset = Asset(
    kind=model.AssetKind.INSTANCE,
    identification=model.Identifier('https://acplt.org/Simple_Asset', model.IdentifierType.IRI)
)
prop = model.Property(
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
submodel = Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI),
    submodel_element={prop}
)
aas = AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset=model.AASReference.from_referable(asset),
    submodel={model.AASReference.from_referable(submodel)}
)


##################################################################
# step 2: Storing the Data in an ObjectStore for Easier Handling #
##################################################################

# step 2.1: create an ObjectStore for identifiable objects
#
# In this tutorial, we use a `DictObjectStore`, which is a simple in-memory store: It just keeps track of the Python
# objects using a dict.
# This may not be a suitable solution, if you need to manage large numbers of objects or objects must kept in a
# persistent memory (i.e. on hard disk). In this case, you may chose the `CouchDBObjectStore` from
# `aas.adapter.couchdb` to use a CouchDB database server as persistent storage. Both ObjectStore implementations provide
# the same interface. Therefore, all the methods shown in this tutorial, can be realized with a CouchDBObjectStore as
# well.
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()

# step 2.2: add asset, submodel and asset administration shell to store
obj_store.add(asset)
obj_store.add(submodel)
obj_store.add(aas)


#################################################################
# step 3: Retrieving Objects From the Store by Their Identifier #
#################################################################

tmp_submodel = obj_store.get_identifiable(
    model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI))

assert(submodel is tmp_submodel)


########################################################
# step 4: Using the ObjectStore to Resolve a Reference #
########################################################

# The `aas` object already contains a reference to the submodel.
# Let's create a list of all submodels, to which the AAS has references, by resolving each of the submodel references:
submodels = [reference.resolve(obj_store)
             for reference in aas.submodel]

# The first (and only) element of this list should be our example submodel:
assert(submodel is tmp_submodel)

# Now, let's manually create a reference to the Property within the submodel. The reference uses two keys, the first one
# identifying the submodel by its identification, the second one resolving to the Property within the submodel by its
# idShort.
property_reference = model.AASReference(
    (model.Key(
        type_=model.KeyElements.SUBMODEL,
        local=True,
        value='https://acplt.org/Simple_Submodel',
        id_type=model.KeyType.IRI),
     model.Key(
         type_=model.KeyElements.PROPERTY,
         local=True,
         value='ExampleProperty',
         id_type=model.KeyType.IDSHORT),
     ),
    type_=model.Property
)

# Now, we can resolve this new reference.
# The `resolve()` method will fetch the Submodel object from the ObjectStore, traverse down to the included Property
# object and return this object.
tmp_property = property_reference.resolve(obj_store)
assert(prop is tmp_property)
