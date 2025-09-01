#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for navigating a Submodel's hierarchy using IdShorts and IdShortPaths.
"""

from basyx.aas import model
from typing import cast

# In this tutorial, you will learn how to create a Submodel with different kinds of SubmodelElements and how to navigate
# through them using IdShorts and IdShortPaths.
#
# Step-by-Step Guide:
# Step 1: Create a Submodel with a Property, a Property Collection, a Property List and a Collection List
# Step 2: Navigate through the Submodel using IdShorts and IdShortPaths


########################################################################
# Step 1: Create a Submodel with a navigable SubmodelElement hierarchy #
########################################################################

# Step 1.1: Create a Submodel
submodel = model.Submodel(id_="https://iat.rwth-aachen.de/Simple_Submodel")

# Step 1.2: Add a single Property to the Submodel
my_property = model.Property(
    id_short="MyProperty",
    value_type=model.datatypes.String,
    value="I am a simple Property"
)
submodel.submodel_element.add(my_property)

# Step 1.3: Add a Property Collection to the Submodel
my_property_collection = model.SubmodelElementCollection(
    id_short="MyPropertyCollection",
    value={
        model.Property(
            id_short="MyProperty0",
            value_type=model.datatypes.String,
            value="I am the first of two Properties within a Property Collection"
        ),
        model.Property(
            id_short="MyProperty1",
            value_type=model.datatypes.String,
            value="I am the second of two Properties within a Property Collection"
        )
    }
)
submodel.submodel_element.add(my_property_collection)

# Step 1.4: Add a Property List to the Submodel
my_property_list = model.SubmodelElementList(
    id_short="MyPropertyList",
    type_value_list_element=model.Property,
    value_type_list_element=model.datatypes.String,
    order_relevant=True,
    value=[
        model.Property(
            id_short=None,
            value_type=model.datatypes.String,
            value="I am Property 0 within a Property List"
        ),
        model.Property(
            id_short=None,
            value_type=model.datatypes.String,
            value="I am Property 1 within a Property List"
        )
    ]
)
submodel.submodel_element.add(my_property_list)

# Step 1.5: Add a Collection List to the Submodel
my_property_collection_0 = model.SubmodelElementCollection(
    id_short=None,
    value={model.Property(
        id_short="MyProperty",
        value_type=model.datatypes.String,
        value="I am a simple Property within Property Collection 0"
    )}
)
my_property_collection_1 = model.SubmodelElementCollection(
    id_short=None,
    value={model.Property(
        id_short="MyProperty",
        value_type=model.datatypes.String,
        value="I am a simple Property within Property Collection 1"
    )}
)
my_property_collection_2 = model.SubmodelElementCollection(
    id_short=None,
    value={model.Property(
        id_short="MyProperty",
        value_type=model.datatypes.String,
        value="I am a simple Property within Property Collection 2"
    )}
)
my_collection_list = model.SubmodelElementList(
    id_short="MyCollectionList",
    type_value_list_element=model.SubmodelElementCollection,
    order_relevant=True,
    value=[my_property_collection_0, my_property_collection_1, my_property_collection_2]
)
submodel.submodel_element.add(my_collection_list)


#########################################################################
# Step 2: Navigate through the Submodel using IdShorts and IdShortPaths #
#########################################################################

# Step 2.1: Access a single Property via its IdShort
my_property = cast(model.Property, submodel.get_referable("MyProperty"))
print(f"my_property: id_short = {my_property.id_short}, value = {my_property.value}\n")

# Step 2.2.1: Access a Property within a Property Collection step by step via its IdShort
my_property_collection = cast(model.SubmodelElementCollection, submodel.get_referable("MyPropertyCollection"))
my_property_collection_property_0 = cast(model.Property, my_property_collection.get_referable("MyProperty0"))
print(
    f"my_property_collection_property_0: "
    f"id_short = {my_property_collection_property_0}, "
    f"value = {my_property_collection_property_0.value}"
)

# Step 2.2.2: Access a Property within a Property Collection via its IdShortPath
my_property_collection_property_1 = cast(
    model.Property,
    submodel.get_referable(["MyPropertyCollection", "MyProperty1"])
)
print(
    f"my_property_collection_property_1: "
    f"id_short = {my_property_collection_property_1}, "
    f"value = {my_property_collection_property_1.value}\n"
)

# Step 2.3.1: Access a Property within a Property List step by step via its index
my_property_list = cast(model.SubmodelElementList, submodel.get_referable("MyPropertyList"))
my_property_list_property_0 = cast(model.Property, my_property_list.get_referable("0"))
print(
    f"my_property_list_property_0: "
    f"id_short = {my_property_list_property_0}, "
    f"value = {my_property_list_property_0.value}"
)

# Step 2.3.2: Access a Property within a Property List via its IdShortPath
my_property_list_property_1 = cast(model.Property, submodel.get_referable(["MyPropertyList", "1"]))
print(
    f"my_property_list_property_1: "
    f"id_short = {my_property_list_property_1}, "
    f"value = {my_property_list_property_1.value}\n"
)

# Step 2.4.1: Access a Property within a Collection List step by step via its index and IdShort
my_collection_list = cast(model.SubmodelElementList, submodel.get_referable("MyCollectionList"))
my_collection_list_collection_0 = cast(model.SubmodelElementCollection, my_collection_list.get_referable("0"))
my_collection_list_collection_0_property_0 = cast(
    model.Property,
    my_collection_list_collection_0.get_referable("MyProperty")
)
print(
    f"my_collection_list_collection_0_property_0: "
    f"id_short = {my_collection_list_collection_0_property_0}, "
    f"value = {my_collection_list_collection_0_property_0.value}"
)

# Step 2.4.2: Access a Property within a Collection List via its IdShortPath
my_collection_list_collection_2_property_0 = cast(
    model.Property,
    submodel.get_referable(["MyCollectionList", "2", "MyProperty"])
)
print(
    f"my_collection_list_collection_2_property_0: "
    f"id_short = {my_collection_list_collection_2_property_0}, "
    f"value = {my_collection_list_collection_2_property_0.value}"
)
