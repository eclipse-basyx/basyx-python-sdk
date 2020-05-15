# Copyright 2020 PyI40AAS Contributors
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
Tests for the tutorials

Functions to test if a tutorial is executable
"""
import os
import re
import tempfile
import unittest
from contextlib import contextmanager

from aas import model
from aas.adapter.json import read_aas_json_file


class TutorialTest(unittest.TestCase):
    def test_tutorial_create_simple_aas(self):
        from aas.examples import tutorial_create_simple_aas
        self.assertEqual(tutorial_create_simple_aas.submodel.get_referable('ExampleProperty').value, 'exampleValue')
        store = model.DictObjectStore({tutorial_create_simple_aas.submodel})
        next(iter(tutorial_create_simple_aas.aas.submodel)).resolve(store)

    def test_tutorial_storage(self):
        from aas.examples import tutorial_storage
        # The tutorial already includes assert statements for the relevant points. So no further checks are required.

    def test_tutorial_serialization_deserialization_json(self):
        with temporary_workingdirectory():
            from aas.examples import tutorial_serialization_deserialization
        # The tutorial already includes assert statements for the relevant points. So no further checks are required.

    def test_tutorial_dynamic_model(self) -> None:
        with temporary_workingdirectory():
            from aas.examples import tutorial_dynamic_model

            # After executing the tutorial, there should be an AAS JSON file in the temporary working directory,
            # containing a list of processes, which should at least contain one "python" process.
            with open('ComputerInformationTest.json') as f:
                objects = read_aas_json_file(f, failsafe=False)

        submodel = objects.get_identifiable(model.Identifier('https://acplt.org/ComputerInformationTest',
                                                             model.IdentifierType.IRI))
        assert(isinstance(submodel, model.Submodel))
        process_list = submodel.get_referable('processes')
        assert(isinstance(process_list, model.SubmodelElementCollection))
        processes = [(p.get_referable('pid').value,   # type: ignore
                      p.get_referable('name').value,   # type: ignore
                      p.get_referable('mem').value)   # type: ignore
                     for p in process_list.value]
        r = re.compile(r'[Pp]ython|coverage')  # When tests are run via `coverage`, there might not be a Python process
        python_processes = list(filter(lambda p: r.match(p[1]), processes))
        self.assertTrue(len(python_processes) > 0,
                        "'Python' not found in Process list {}".format([p[1] for p in processes]))
        self.assertGreater(python_processes[0][0], 0)
        self.assertGreater(python_processes[0][2], 0.0)


@contextmanager
def temporary_workingdirectory():
    """
    A helper contextmanager to temporarily change the current working directory of the Python process to a temporary
    directory.

    The temp directory is deleted with all its contents when leaving the with-context. This can be used to test Python
    scripts, which write files to the current working directory.
    """
    cwd = os.getcwd()
    tempdir = tempfile.TemporaryDirectory()
    os.chdir(tempdir.name)
    try:
        yield None
    finally:
        os.chdir(cwd)
        tempdir.cleanup()
