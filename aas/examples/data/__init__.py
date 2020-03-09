"""
This package contains functions for the creation of different example AAS objects.

example_ass.py
    Module for the creation of example asset administration shell, related asset, example submodels and a concept
    dictionary containing an example concept description

example_aas_mandatory_attributes.py
    Module for the creation of an example asset administration shell, related asset, example submodels and a concept
    dictionary containing an example concept description. All objects only contain mandatory attributes.

example_aas_missing_attributes.py
    Module for the creation of an example asset administration shell, related asset, example submodels and a concept
    dictionary containing an example concept description. All objects contain missing object attribute combination.

example_concept_description.py
    Module for creation of an example concept description.

example_submodel_template.py
    Module for the creation of an example submodel template containing all kind of submodel elements where the kind is
    always TEMPLATE.
"""
from aas import model
from aas.examples.data import example_aas, example_aas_mandatory_attributes, example_aas_missing_attributes, \
    example_submodel_template, example_concept_description


def create_example() -> model.DictObjectStore:
    """
    creates an object store which is filled with a example assets, submodels, concept descriptions and asset
    administration shells using the functionality of this package

    :return: object store
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.update(example_aas.create_full_example())
    obj_store.update(example_aas_mandatory_attributes.create_full_example())
    obj_store.update(example_aas_missing_attributes.create_full_example())
    obj_store.add(example_submodel_template.create_example_submodel_template())
    obj_store.add(example_concept_description.create_iec61360_concept_description())
    return obj_store
