"""
This package contains functions for the creation of different example AAS objects.

example_ass.py
    Module for the creation of example asset administration shell, example submodels and a concept
    dictionary containing an example concept description

example_aas_mandatory_attributes.py
    Module for the creation of an example asset administration shell, example submodels and a concept
    dictionary containing an example concept description. All objects only contain mandatory attributes.

example_aas_missing_attributes.py
    Module for the creation of an example asset administration shell, example submodels and a concept
    dictionary containing an example concept description. All objects contain missing object attribute combination.

example_submodel_template.py
    Module for the creation of an example submodel template containing all kind of submodel elements where the kind is
    always TEMPLATE.
"""
import os

from basyx.aas import model
from basyx.aas.examples.data import example_aas_missing_attributes, example_aas, \
    example_aas_mandatory_attributes, example_submodel_template

TEST_PDF_FILE = os.path.join(os.path.dirname(__file__), 'TestFile.pdf')


def create_example() -> model.DictIdentifiableStore:
    """
    creates an object store which is filled with example assets, submodels, concept descriptions and asset
    administration shells using the functionality of this package

    :return: object store
    """
    identifiable_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
    identifiable_store.update(example_aas.create_full_example())
    identifiable_store.update(example_aas_mandatory_attributes.create_full_example())
    identifiable_store.update(example_aas_missing_attributes.create_full_example())
    identifiable_store.add(example_submodel_template.create_example_submodel_template())
    return identifiable_store


def create_example_aas_binding() -> model.DictIdentifiableStore:
    """
    creates an object store which is filled with example assets, submodels, concept descriptions and asset
    administration shells using the functionality of this package where each submodel and concept description is
    at least referred by one asset administration shell

    :return: object store
    """
    identifiable_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
    identifiable_store.update(example_aas.create_full_example())
    identifiable_store.update(example_aas_mandatory_attributes.create_full_example())
    identifiable_store.update(example_aas_missing_attributes.create_full_example())
    identifiable_store.add(example_submodel_template.create_example_submodel_template())

    aas = identifiable_store.get_item('https://example.org/Test_AssetAdministrationShell')
    sm = identifiable_store.get_item('https://example.org/Test_Submodel_Template')
    assert (isinstance(aas, model.aas.AssetAdministrationShell))  # make mypy happy
    assert (isinstance(sm, model.submodel.Submodel))  # make mypy happy
    aas.submodel.add(model.ModelReference.from_referable(sm))

    cd = identifiable_store.get_item('https://example.org/Test_ConceptDescription_Mandatory')
    assert (isinstance(cd, model.concept.ConceptDescription))  # make mypy happy
    return identifiable_store
