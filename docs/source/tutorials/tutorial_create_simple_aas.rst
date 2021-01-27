Tutorial: Create a Simple AAS
=============================

.. _tutorial_create_simple_aas:

Tutorial for the creation of an simple Asset Administration Shell, containing an Asset reference and a Submodel
reference

To begin, import all PyI40AAS classes from model package

.. code-block:: python

    from aas import model

In this tutorial, you'll get a step by step guide on how to create an :class:`~aas.model.aas.AssetAdministrationShell`
(AAS) and all
required objects within. First, you need an :class:`~aas.model.aas.Asset` for which you want to create an AAS,
represented by an :class:`~aas.model.aas.Asset` object.
After that, an :class:`~aas.model.aas.AssetAdministrationShell` can be created, containing a reference to that
:class:`~aas.model.aas.Asset`.
Then, it's possible to
add :class:`Submodels <aas.model.submodel.Submodel>` to the AAS. The Submodels can contain
:class:`SubmodelElements <aas.model.submodel.SubmodelElement>`.

Step by Step Guide:

    - Step 1: create a simple Asset Administration Shell, containing a reference to the Asset
    - Step 2: create a simple Submodel
    - Step 3: create a simple Property and add it to the Submodel


**Step 1: Create a Simple Asset Administration Shell Containing a Reference to the Asset**

Step 1.1: create the AssetInformation object

.. code-block:: python

    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.INSTANCE,
        global_asset_id=model.Reference(
            (model.Key(
                type_=model.KeyElements.GLOBAL_REFERENCE,
                value='http://acplt.org/Simple_Asset',
                id_type=model.KeyType.IRI
            ),)
        )
    )

Step 1.2: create the Asset Administration Shell

.. code-block:: python

    identifier = model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI)
    aas = model.AssetAdministrationShell(
        identification=identifier,  # set identifier
        asset_information=asset_information
    )

**Step 2: Create a Simple Submodel Without SubmodelElements**

Step 2.1: create the Submodel object

.. code-block:: python

    identifier = model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
    submodel = model.Submodel(
        identification=identifier
    )

Step 2.2: create a reference to that Submodel and add it to the Asset Administration Shell's `submodel` set

.. code-block:: python

    aas.submodel.add(model.AASReference.from_referable(submodel))

**ALTERNATIVE: step 1 and 2 can alternatively be done in one step**
In this version, the Submodel reference is passed to the Asset Administration Shell's constructor.


.. code-block:: python

    submodel = model.Submodel(
        identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
    )
    aas = model.AssetAdministrationShell(
        identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
        asset_information=asset_information,
        submodel={model.AASReference.from_referable(submodel)}
    )

**Step 3: Create a Simple Property and Add it to the Submodel**

Step 3.1: create a global reference to a semantic description of the Property
A global reference consist of one key which points to the address where the semantic description is stored

.. code-block:: python

    semantic_reference = model.Reference(
        (model.Key(
            type_=model.KeyElements.GLOBAL_REFERENCE,
            value='http://acplt.org/Properties/SimpleProperty',
            id_type=model.KeyType.IRI
        ),)
    )

Step 3.2: create the simple Property

.. code-block:: python

    property_ = model.Property(
        id_short='ExampleProperty',  # Identifying string of the element within the Submodel namespace
        value_type=model.datatypes.String,  # Data type of the value
        value='exampleValue',  # Value of the Property
        semantic_id=semantic_reference  # set the semantic reference
    )

Step 3.3: add the Property to the Submodel

.. code-block:: python

    submodel.submodel_element.add(property_)

**Alternative: step 2 and 3 can also be combined in a single statement:**
Again, we pass the Property to the Submodel's constructor instead of adding it afterwards.

.. code-block:: python

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
                        value='http://acplt.org/Properties/SimpleProperty',
                        id_type=model.KeyType.IRI
                    ),)
                )
            )
        }
    )