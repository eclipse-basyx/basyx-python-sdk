# Copyright 2021 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

"""
This test uses the schemathesis package to perform automated stateful testing on the implemented http api. Requests
are created automatically based on the json schemata given in the api specification, responses are also validated
against said schemata.

For data generation schemathesis uses hypothesis and hypothesis-jsonschema, hence the name. hypothesis is a library
for automated, property-based testing. It can generate test cases based on strategies. hypothesis-jsonschema is such
a strategy for generating data that matches a given JSON schema.

schemathesis allows stateful testing by generating a statemachine based on the OAS links contained in the specification.
This is applied here with the APIWorkflowAAS and APIWorkflowSubmodel classes. They inherit the respective state machine
and offer an automatically generated python unittest TestCase.
"""

# TODO: lookup schemathesis deps and add them to the readme
# TODO: implement official Plattform I4.0 HTTP API
# TODO: check required properties of schema
# TODO: add id_short format to schemata

import os
import random
import pathlib
import urllib.parse

import schemathesis
import hypothesis.strategies

from basyx.aas import model
from basyx.aas.adapter.http import WSGIApp
from basyx.aas.examples.data.example_aas import create_full_example

from typing import Set


def _encode_and_quote(identifier: model.Identifier) -> str:
    return urllib.parse.quote(urllib.parse.quote(identifier, safe=""), safe="")


def _check_transformed(response, case):
    """
    This helper function performs an additional checks on requests that have been *transformed*, i.e. requests, that
    resulted from schemathesis using an OpenAPI Spec link. It asserts, that requests that are performed after a link has
    been used, must be successful and result in a 2xx response. The exception are requests where hypothesis generates
    invalid data (data, that validates against the schema, but is still semantically invalid). Such requests would
    result in a 422 - Unprocessable Entity, which is why the 422 status code is ignored here.
    """
    if case.source is not None:
        assert 200 <= response.status_code < 300 or response.status_code == 422


# define some settings for hypothesis, used in both api test cases
HYPOTHESIS_SETTINGS = hypothesis.settings(
    max_examples=int(os.getenv("HYPOTHESIS_MAX_EXAMPLES", 10)),
    stateful_step_count=5,
    # disable the filter_too_much health check, which triggers if a strategy filters too much data, raising an error
    suppress_health_check=[hypothesis.HealthCheck.filter_too_much],
    # disable data generation deadlines, which would result in an error if data generation takes too much time
    deadline=None
)

BASE_URL = "/api/v1"
IDENTIFIER_AAS: Set[str] = set()
IDENTIFIER_SUBMODEL: Set[str] = set()

# register hypothesis strategy for generating valid idShorts
ID_SHORT_STRATEGY = hypothesis.strategies.from_regex(r"\A[A-Za-z_][0-9A-Za-z_]*\Z")
schemathesis.register_string_format("id_short", ID_SHORT_STRATEGY)

# store identifiers of available AAS and Submodels
for obj in create_full_example():
    if isinstance(obj, model.AssetAdministrationShell):
        IDENTIFIER_AAS.add(_encode_and_quote(obj.id))
    if isinstance(obj, model.Submodel):
        IDENTIFIER_SUBMODEL.add(_encode_and_quote(obj.id))

# load aas and submodel api specs
AAS_SCHEMA = schemathesis.from_path(pathlib.Path(__file__).parent / "http-api-oas-aas.yaml",
                                    app=WSGIApp(create_full_example()))

SUBMODEL_SCHEMA = schemathesis.from_path(pathlib.Path(__file__).parent / "http-api-oas-submodel.yaml",
                                         app=WSGIApp(create_full_example()))


class APIWorkflowAAS(AAS_SCHEMA.as_state_machine()):  # type: ignore
    def setup(self):
        self.schema.app.object_store = create_full_example()
        # select random identifier for each test scenario
        self.schema.base_url = BASE_URL + "/aas/" + random.choice(tuple(IDENTIFIER_AAS))

    def transform(self, result, direction, case):
        out = super().transform(result, direction, case)
        print("transformed")
        print(out)
        print(result.response, direction.name)
        return out

    def validate_response(self, response, case, additional_checks=()) -> None:
        super().validate_response(response, case, additional_checks + (_check_transformed,))


class APIWorkflowSubmodel(SUBMODEL_SCHEMA.as_state_machine()):  # type: ignore
    def setup(self):
        self.schema.app.object_store = create_full_example()
        self.schema.base_url = BASE_URL + "/submodels/" + random.choice(tuple(IDENTIFIER_SUBMODEL))

    def transform(self, result, direction, case):
        out = super().transform(result, direction, case)
        print("transformed")
        print(out)
        print(result.response, direction.name)
        return out

    def validate_response(self, response, case, additional_checks=()) -> None:
        super().validate_response(response, case, additional_checks + (_check_transformed,))


# APIWorkflow.TestCase is a standard python unittest.TestCase
# TODO: Fix HTTP API Tests
# ApiTestAAS = APIWorkflowAAS.TestCase
# ApiTestAAS.settings = HYPOTHESIS_SETTINGS

# ApiTestSubmodel = APIWorkflowSubmodel.TestCase
# ApiTestSubmodel.settings = HYPOTHESIS_SETTINGS
