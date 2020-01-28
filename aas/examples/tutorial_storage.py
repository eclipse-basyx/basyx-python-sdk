# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for storing asset administration shells, submodels and assets
"""

# to get all functions import model
from aas import model
from aas.model import Asset, AssetAdministrationShell, Submodel

# create asset, submodel and asset administration shell, for more details look at 'tutorial_create_simple_aas'


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

# Store the data in an object store for easier handling
# create an object store for identifiable objects (asset administration shell, asset and submodel)
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
# add asset to store
obj_store.add(asset)
# add submodel to store
obj_store.add(submodel)
# add asset administration shell to store
obj_store.add(aas)

# now it is possible to get the data out of the store by their identifier
tmp_submodel: Submodel = obj_store.get_identifiable(
    model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI))  # type: ignore

# add an property to the submodel
tmp_submodel.submodel_element.add(
    model.Property(
        id_short='ExampleProperty2',
        value_type=model.datatypes.String,
        value='exampleValue2',
        semantic_id=model.Reference(
            (model.Key(
                type_=model.KeyElements.GLOBAL_REFERENCE,
                local=False,
                value='http://acplt.org/Properties/SimpleProperty',
                id_type=model.KeyType.IRI
            ),)
        )
    )
)
