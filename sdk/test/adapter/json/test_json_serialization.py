# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import io
import json
import os
import unittest
from typing import Iterable, Set, Union

from basyx.aas import model
from basyx.aas.adapter.json import (
    AASToJsonEncoder,
    SortingAASToJsonEncoder,
    SortingStrippedAASToJsonEncoder,
    StrippedAASToJsonEncoder,
    object_store_to_json,
    write_aas_json_file,
)
from basyx.aas.examples.data import (
    create_example,
    example_aas,
    example_aas_mandatory_attributes,
    example_aas_missing_attributes,
    example_submodel_template,
)
from jsonschema import validate  # type: ignore

JSON_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "../schemas/aasJSONSchema.json"
)


class JsonSerializationTest(unittest.TestCase):
    def test_serialize_object(self) -> None:
        test_object = model.Property(
            "test_id_short",
            model.datatypes.String,
            category="PARAMETER",
            description=model.MultiLanguageTextType(
                {"en-US": "Germany", "de": "Deutschland"}
            ),
        )
        json.dumps(test_object, cls=AASToJsonEncoder)

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        submodel = model.Submodel(submodel_identifier)
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="test"),
            aas_identifier,
            submodel={submodel_reference},
        )

        # serialize object to json
        json_data = json.dumps(
            {
                "assetAdministrationShells": [test_aas],
                "submodels": [submodel],
                "assets": [],
                "conceptDescriptions": [],
            },
            cls=AASToJsonEncoder,
        )
        json.loads(json_data)


class JsonSerializationSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(JSON_SCHEMA_FILE):
            raise unittest.SkipTest(
                f"JSON Schema does not exist at {JSON_SCHEMA_FILE}, skipping test"
            )

    def test_random_object_serialization(self) -> None:
        aas_identifier = "AAS1"
        submodel_key = (model.Key(model.KeyTypes.SUBMODEL, "SM1"),)
        submodel_identifier = submodel_key[0].get_identifier()
        assert submodel_identifier is not None
        submodel_reference = model.ModelReference(submodel_key, model.Submodel)
        # The JSONSchema expects every object with HasSemnatics (like Submodels) to have a `semanticId` Reference, which
        # must be a Reference. (This seems to be a bug in the JSONSchema.)
        submodel = model.Submodel(
            submodel_identifier,
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        model.KeyTypes.GLOBAL_REFERENCE,
                        "http://example.org/TestSemanticId",
                    ),
                )
            ),
        )
        test_aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="test"),
            aas_identifier,
            submodel={submodel_reference},
        )

        # serialize object to json
        json_data = json.dumps(
            {"assetAdministrationShells": [test_aas], "submodels": [submodel]},
            cls=AASToJsonEncoder,
        )
        json_data_new = json.loads(json_data)

        # load schema
        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_schema = json.load(json_file)

        # validate serialization against schema
        validate(instance=json_data_new, schema=aas_schema)

    def test_aas_example_serialization(self) -> None:
        data = example_aas.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_submodel_template_serialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_submodel_template.create_example_submodel_template())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_empty_example_serialization(self) -> None:
        data = example_aas_mandatory_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_missing_serialization(self) -> None:
        data = example_aas_missing_attributes.create_full_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_concept_description_serialization(self) -> None:
        data: model.DictIdentifiableStore[model.Identifiable] = (
            model.DictIdentifiableStore()
        )
        data.add(example_aas.create_example_concept_description())
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)

    def test_full_example_serialization(self) -> None:
        data = create_example()
        file = io.StringIO()
        write_aas_json_file(file=file, data=data)

        with open(JSON_SCHEMA_FILE, "r") as json_file:
            aas_json_schema = json.load(json_file)

        file.seek(0)
        json_data = json.load(file)

        # validate serialization against schema
        validate(instance=json_data, schema=aas_json_schema)


class JsonSerializationStrippedObjectsTest(unittest.TestCase):
    def _checkNormalAndStripped(
        self, attributes: Union[Set[str], str], obj: object
    ) -> None:
        if isinstance(attributes, str):
            attributes = {attributes}

        # attributes should be present when using the normal encoder,
        # but must not be present when using the stripped encoder
        for cls, assert_fn in (
            (AASToJsonEncoder, self.assertIn),
            (StrippedAASToJsonEncoder, self.assertNotIn),
        ):
            data = json.loads(json.dumps(obj, cls=cls))
            for attr in attributes:
                assert_fn(attr, data)

    def test_stripped_qualifiable(self) -> None:
        qualifier = model.Qualifier("test_qualifier", str)
        qualifier2 = model.Qualifier("test_qualifier2", str)
        operation = model.Operation("test_operation", qualifier={qualifier})
        submodel = model.Submodel(
            "http://example.org/test_submodel",
            submodel_element=[operation],
            qualifier={qualifier2},
        )

        self._checkNormalAndStripped({"submodelElements", "qualifiers"}, submodel)
        self._checkNormalAndStripped("qualifiers", operation)

    def test_stripped_annotated_relationship_element(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "http://example.org/test_ref"),),
            model.Submodel,
        )
        are = model.AnnotatedRelationshipElement(
            "test_annotated_relationship_element", ref, ref, annotation=[mlp]
        )

        self._checkNormalAndStripped("annotations", are)

    def test_relationship_element_omits_none_first_second(self) -> None:
        re = model.RelationshipElement("test_re")
        data = json.loads(json.dumps(re, cls=AASToJsonEncoder))
        self.assertNotIn("first", data)
        self.assertNotIn("second", data)

    def test_stripped_entity(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        entity = model.Entity(
            "test_entity", model.EntityType.CO_MANAGED_ENTITY, statement=[mlp]
        )

        self._checkNormalAndStripped("statements", entity)

    def test_stripped_submodel_element_collection(self) -> None:
        mlp = model.MultiLanguageProperty(
            "test_multi_language_property", category="PARAMETER"
        )
        sec = model.SubmodelElementCollection(
            "test_submodel_element_collection", value=[mlp]
        )

        self._checkNormalAndStripped("value", sec)

    def test_stripped_asset_administration_shell(self) -> None:
        submodel_ref = model.ModelReference(
            (model.Key(model.KeyTypes.SUBMODEL, "http://example.org/test_ref"),),
            model.Submodel,
        )
        aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/test_ref"),
            "http://example.org/test_aas",
            submodel={submodel_ref},
        )

        self._checkNormalAndStripped({"submodels"}, aas)


class JsonSerializationDeterministicOrderTest(unittest.TestCase):
    """
    Tests for the opt-in ``sort_arrays`` serialization option, which makes JSON arrays originating from unordered
    Python sets deterministic. The assertions check for the *sorted* result, which is fully deterministic and does
    not rely on (non-reproducible) set iteration order.
    """

    @staticmethod
    def _submodel_store(ids: Iterable[str]) -> model.DictIdentifiableStore[model.Identifiable]:
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        for id_ in ids:
            store.add(model.Submodel(id_))
        return store

    def test_top_level_arrays_sorted(self) -> None:
        # the top-level object lists are backed by an unordered AbstractObjectStore
        ids = ["http://example.org/sm_c", "http://example.org/sm_a", "http://example.org/sm_b"]
        data = json.loads(object_store_to_json(self._submodel_store(ids), sort_arrays=True))
        serialized_ids = [sm["id"] for sm in data["submodels"]]
        self.assertEqual(serialized_ids, sorted(ids))

    def test_order_independent_of_insertion_order(self) -> None:
        ids = ["http://example.org/sm_c", "http://example.org/sm_a", "http://example.org/sm_b"]
        out1 = object_store_to_json(self._submodel_store(ids), sort_arrays=True)
        out2 = object_store_to_json(self._submodel_store(list(reversed(ids))), sort_arrays=True)
        self.assertEqual(out1, out2)

    def test_set_valued_attribute_sorted(self) -> None:
        # the submodel references of an AssetAdministrationShell are stored in an unordered set
        refs = {model.ModelReference((model.Key(model.KeyTypes.SUBMODEL, v),), model.Submodel)
                for v in ("SM_C", "SM_A", "SM_B")}
        aas = model.AssetAdministrationShell(
            model.AssetInformation(global_asset_id="http://example.org/asset"),
            "http://example.org/aas", submodel=refs)
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        store.add(aas)
        data = json.loads(object_store_to_json(store, sort_arrays=True))
        values = [ref["keys"][0]["value"] for ref in data["assetAdministrationShells"][0]["submodels"]]
        self.assertEqual(values, ["SM_A", "SM_B", "SM_C"])

    def test_is_case_of_sorted(self) -> None:
        # the isCaseOf references of a ConceptDescription are stored in an unordered set
        refs: Set[model.Reference] = {
            model.ExternalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, v),))
            for v in ("http://example.org/c", "http://example.org/a", "http://example.org/b")}
        cd = model.ConceptDescription("http://example.org/cd", is_case_of=refs)
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        store.add(cd)
        data = json.loads(object_store_to_json(store, sort_arrays=True))
        values = [ref["keys"][0]["value"] for ref in data["conceptDescriptions"][0]["isCaseOf"]]
        self.assertEqual(values, ["http://example.org/a", "http://example.org/b", "http://example.org/c"])

    def test_sort_arrays_independent_of_sort_keys(self) -> None:
        # sort_keys only orders dict keys; it must not implicitly sort arrays. Passing it must not raise and must
        # still produce schema-shaped output.
        ids = ["http://example.org/sm_c", "http://example.org/sm_a"]
        data = json.loads(object_store_to_json(self._submodel_store(ids), sort_keys=True))
        self.assertEqual({sm["id"] for sm in data["submodels"]}, set(ids))

    def test_sorting_encoder_classes(self) -> None:
        # the sorting encoders can also be passed explicitly, in which case sort_arrays is not needed
        ids = ["http://example.org/sm_c", "http://example.org/sm_a", "http://example.org/sm_b"]
        for encoder in (SortingAASToJsonEncoder, SortingStrippedAASToJsonEncoder):
            with self.subTest(encoder=encoder.__name__):
                data = json.loads(object_store_to_json(self._submodel_store(ids), encoder=encoder))
                self.assertEqual([sm["id"] for sm in data["submodels"]], sorted(ids))

    def test_references_differing_only_in_referred_semantic_id(self) -> None:
        # Reference.__hash__ ignores referred_semantic_id while __eq__ considers it, so these references are
        # distinct set members that share a key chain. The sort key must not tie on them.
        refs: Set[model.Reference] = {
            model.ExternalReference(
                (model.Key(model.KeyTypes.GLOBAL_REFERENCE, "http://example.org/ref"),),
                referred_semantic_id=model.ExternalReference(
                    (model.Key(model.KeyTypes.GLOBAL_REFERENCE, v),)),
            )
            for v in ("http://example.org/s_c", "http://example.org/s_a", "http://example.org/s_b")}
        self.assertEqual(len(refs), 3)
        cd = model.ConceptDescription("http://example.org/cd", is_case_of=refs)
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        store.add(cd)
        data = json.loads(object_store_to_json(store, sort_arrays=True))
        values = [ref["referredSemanticId"]["keys"][0]["value"]
                  for ref in data["conceptDescriptions"][0]["isCaseOf"]]
        self.assertEqual(values, ["http://example.org/s_a", "http://example.org/s_b", "http://example.org/s_c"])

    def test_refers_to_sorted(self) -> None:
        # the refersTo references of an Extension are stored in an unordered set
        refs = {model.ModelReference((model.Key(model.KeyTypes.SUBMODEL, v),), model.Submodel)
                for v in ("SM_C", "SM_A", "SM_B")}
        sm = model.Submodel("http://example.org/sm",
                            extension=(model.Extension("test", refers_to=refs),))
        store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
        store.add(sm)
        data = json.loads(object_store_to_json(store, sort_arrays=True))
        values = [ref["keys"][0]["value"]
                  for ref in data["submodels"][0]["extensions"][0]["refersTo"]]
        self.assertEqual(values, ["SM_A", "SM_B", "SM_C"])

    def test_stripped_and_sort_arrays(self) -> None:
        ids = ["http://example.org/sm_c", "http://example.org/sm_a", "http://example.org/sm_b"]
        data = json.loads(object_store_to_json(self._submodel_store(ids), stripped=True, sort_arrays=True))
        self.assertEqual([sm["id"] for sm in data["submodels"]], sorted(ids))

    def test_sort_arrays_ignored_if_encoder_given(self) -> None:
        # documented contract: like `stripped`, `sort_arrays` is ignored when an encoder class is specified
        store = self._submodel_store(["http://example.org/sm_a"])
        object_store_to_json(store, encoder=AASToJsonEncoder, sort_arrays=True)
        self.assertFalse(AASToJsonEncoder.sort_arrays)

    def test_write_aas_json_file_sort_arrays(self) -> None:
        ids = ["http://example.org/sm_c", "http://example.org/sm_a", "http://example.org/sm_b"]
        file = io.StringIO()
        write_aas_json_file(file=file, data=self._submodel_store(ids), sort_arrays=True)
        file.seek(0)
        data = json.load(file)
        self.assertEqual([sm["id"] for sm in data["submodels"]], sorted(ids))
