# Copyright (c) 2023 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import io
import os
import unittest

from rdflib import Graph, Namespace
from pyshacl import validate

from basyx.aas import model
from basyx.aas.adapter.rdf import write_aas_rdf_file

from basyx.aas.examples.data import example_submodel_template, example_aas_mandatory_attributes, \
    example_aas_missing_attributes, example_aas

RDF_ONTOLOGY_FILE = os.path.join(os.path.dirname(__file__), '../schemas/aasRDFOntology.ttl')
RDF_SHACL_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), '../schemas/aasRDFShaclSchema.ttl')


class RDFSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property("test_id_short", model.datatypes.String, category="PARAMETER",
                                     description=model.MultiLanguageTextType({"en-US": "Germany", "de": "Deutschland"}))
        # TODO: The serialization of a single object to rdf is currently not supported.

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert (submodel_identifier is not None)
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(model.AssetInformation(global_asset_id="Test"),
                                                  aas_identifier, submodel={submodel_reference})

        # TODO: The serialization of a single object to rdf is currently not supported.


def validate_graph(data_graph: io.BytesIO):
    # load schema
    data_graph.seek(0)
    shacl_graph = Graph()
    shacl_graph.parse(RDF_SHACL_SCHEMA_FILE, format="turtle")

    # TODO: We need to remove the Sparql constraints on Abstract classes because
    # it somehow fails when using pychacl as validator
    SH = Namespace("http://www.w3.org/ns/shacl#")
    shacl_graph.remove((None, SH.sparql, None))

    # load aas ontology
    aas_graph = Graph()
    aas_graph.parse(RDF_ONTOLOGY_FILE, format="turtle")

    # validate serialization against schema
    conforms, results_graph, results_text = validate(
        data_graph=data_graph,  # Passing the BytesIO object here
        shacl_graph=shacl_graph,  # The SHACL graph
        ont_graph=aas_graph,
        data_graph_format="turtle",  # Specify the format for the data graph (since it's serialized)
        inference='both',  # Optional: perform RDFS inference
        abort_on_first=True,  # Don't continue validation after finding an error
        allow_infos=True,  # Allow informational messages
        allow_warnings=True,  # Allow warnings
        advanced=True)
    # print("Conforms:", conforms)
    # print("Validation Results:\n", results_text)
    assert conforms is True


class RDFSerializationSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(RDF_SHACL_SCHEMA_FILE):
            raise unittest.SkipTest(f"Shacl Schema does not exist at {RDF_SHACL_SCHEMA_FILE}, skipping test")

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier,
                                  semantic_id=model.ExternalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE,
                                                                                 "http://acplt.org/TestSemanticId"),)))
        test_aas = model.AssetAdministrationShell(model.AssetInformation(global_asset_id="test"),
                                                  aas_identifier, submodel={submodel_reference})

        # serialize object to rdf
        test_data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        test_data.add(test_aas)
        test_data.add(submodel)

        test_file = io.BytesIO()
        write_aas_rdf_file(file=test_file, data=test_data)
        validate_graph(test_file)

    def test_full_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.BytesIO()
        write_aas_rdf_file(file=file, data=data)
        validate_graph(file)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.BytesIO()
        write_aas_rdf_file(file=file, data=data)
        validate_graph(file)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_rdf_file(file=file, data=data)
        validate_graph(file)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.BytesIO()
        write_aas_rdf_file(file=file, data=data)
        validate_graph(file)

    def test_concept_description(self) -> None:
        data: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        data.add(example_aas.create_example_concept_description())
        file = io.BytesIO()
        write_aas_rdf_file(file=file, data=data)
        validate_graph(file)
