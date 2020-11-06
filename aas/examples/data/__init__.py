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
import os

from aas import model
from aas.examples.data import example_aas, example_aas_mandatory_attributes, example_aas_missing_attributes, \
    example_submodel_template, example_concept_description

TEST_PDF_FILE = os.path.join(os.path.dirname(__file__), 'TestFile.pdf')


def create_example() -> model.DictObjectStore:
    """
    creates an object store which is filled with example assets, submodels, concept descriptions and asset
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


def create_example_aas_binding() -> model.DictObjectStore:
    """
    creates an object store which is filled with example assets, submodels, concept descriptions and asset
    administration shells using the functionality of this package where each asset, submodel and concept description is
    at least referred by one asset administration shell

    :return: object store
    """
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.update(example_aas.create_full_example())
    obj_store.update(example_aas_mandatory_attributes.create_full_example())
    obj_store.update(example_aas_missing_attributes.create_full_example())
    obj_store.add(example_submodel_template.create_example_submodel_template())

    aas = obj_store.get_identifiable(model.Identifier('https://acplt.org/Test_AssetAdministrationShell',
                                                      model.IdentifierType.IRI))
    sm = obj_store.get_identifiable(model.Identifier('https://acplt.org/Test_Submodel_Template',
                                                     model.IdentifierType.IRI))
    assert (isinstance(aas, model.aas.AssetAdministrationShell))  # make mypy happy
    assert (isinstance(sm, model.submodel.Submodel))  # make mypy happy
    aas.submodel.add(model.AASReference.from_referable(sm))

    obj_store.add(example_concept_description.create_iec61360_concept_description())
    cd = obj_store.get_identifiable(model.Identifier('http://acplt.org/DataSpecifciations/Example/Identification',
                                                     model.IdentifierType.IRI))
    assert (isinstance(cd, model.concept.IEC61360ConceptDescription))  # make mypy happy
    cdict = aas.concept_dictionary.get_referable("TestConceptDictionary")
    cdict.concept_description.add(model.AASReference.from_referable(cd))
    cd2 = obj_store.get_identifiable(model.Identifier('https://acplt.org/Test_ConceptDescription_Mandatory',
                                                      model.IdentifierType.IRI))
    assert (isinstance(cd2, model.concept.ConceptDescription))  # make mypy happy
    cdict.concept_description.add(model.AASReference.from_referable(cd2))
    return obj_store
