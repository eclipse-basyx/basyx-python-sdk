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
            # from aas.examples import tutorial_serialization_deserialization  # todo add this back in
            pass
        # The tutorial already includes assert statements for the relevant points. So no further checks are required.


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
