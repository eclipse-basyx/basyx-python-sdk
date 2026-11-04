# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Shared fixture builders for testing the server's ``run_*`` start-up scripts.
"""

import importlib
import json
import os
from contextlib import contextmanager
from types import ModuleType
from typing import Iterator, Mapping, Set
from unittest import mock

from app.adapter import ServerAASToJsonEncoder
from basyx.aas.adapter.json import write_aas_json_file
from basyx.aas.adapter.xml import write_aas_xml_file
from basyx.aas.examples.data.example_aas_missing_attributes import (
    create_example_asset_administration_shell,
    create_example_submodel,
)
from basyx.aas.model import Identifier
from basyx.aas.model.provider import DictIdentifiableStore

from ..adapter.descriptor_utils import example_aas_descriptor, example_submodel_descriptor


def write_repository_input(directory: str) -> Set[Identifier]:
    """
    Write one shell (JSON) and one submodel (XML) into ``directory``, exercising both loaders
    used by :func:`~basyx.aas.adapter.load_directory`.

    :return: The set of ids that were written
    """
    shell = create_example_asset_administration_shell()
    submodel = create_example_submodel()

    shell_store: DictIdentifiableStore = DictIdentifiableStore()
    shell_store.add(shell)
    write_aas_json_file(os.path.join(directory, "data.json"), shell_store)

    submodel_store: DictIdentifiableStore = DictIdentifiableStore()
    submodel_store.add(submodel)
    write_aas_xml_file(os.path.join(directory, "data.xml"), submodel_store)

    return {shell.id, submodel.id}

def write_registry_input(directory: str) -> Set[Identifier]:
    """
    Write one shell descriptor and one submodel descriptor into ``directory``.

    :return: The set of ids that were written
    """
    aasd = example_aas_descriptor("https://example.org/AASDescriptor")
    sd = example_submodel_descriptor("https://example.org/SubmodelDescriptor")

    data = {
        "assetAdministrationShellDescriptors": [aasd],
        "submodelDescriptors": [sd]
    }

    # Hack in the "modelType" to deserialize into the right classes
    json_save = json.loads(json.dumps(data, cls=ServerAASToJsonEncoder))
    for aas in json_save["assetAdministrationShellDescriptors"]:
        aas["modelType"] = "AssetAdministrationShellDescriptor"
    for aas in json_save["submodelDescriptors"]:
        aas["modelType"] = "SubmodelDescriptor"

    with open(os.path.join(directory, "data.json"), "w") as f:
        json.dump(json_save, f)

    return {aasd.id, sd.id}


@contextmanager
def run_module(module_name: str, env: Mapping[str, str]) -> Iterator[ModuleType]:
    """
    Helper to import (and thereby run) the `app.services.run_*.py` files under different environments.

    :param module_name: Fully-qualified name of the module to reload, e.g. ``"app.services.run_repository"``
    :param env: Environment variables to apply for the duration of the ``with`` block
    :return: The imported module
    """
    module = importlib.import_module(module_name)
    with mock.patch.dict(os.environ, env, clear=False):
        importlib.reload(module)
        yield module
