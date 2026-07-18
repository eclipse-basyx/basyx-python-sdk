# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
Integration tests that exercise the full compliance check pipeline without mocking AASDataChecker.
Each test creates a real file on disk and runs the compliance tool CLI against it.
"""
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from typing import cast
from unittest.mock import patch

from aas_compliance_tool.cli import main
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.adapter.json import write_aas_json_file
from basyx.aas.adapter.xml import write_aas_xml_file
from basyx.aas.examples.data.example_aas import create_full_example


class ComplianceToolIntegrationTest(unittest.TestCase):

    def _call_main(self, args) -> str:
        buf = StringIO()
        with patch('sys.argv', ['compliance_tool'] + args):
            with redirect_stdout(buf):
                main()
        return buf.getvalue()

    def _modified_example(self) -> model.DictIdentifiableStore:
        modified_example = create_full_example()
        submodel = cast(model.Submodel, modified_example.get_item("https://example.org/Test_Submodel"))
        submodel.submodel_element.remove(next(iter(submodel.submodel_element)))
        return modified_example

    # --- JSON ---

    def test_json_example_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            self._call_main(['c', tf.name, '--json'])
            output = self._call_main(['e', tf.name, '--json'])
        self.assertNotIn('FAILED:', output)

    def test_json_example_fail(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode='w', encoding='utf-8-sig') as tf:
            write_aas_json_file(tf, self._modified_example())
            tf.flush()
            output = self._call_main(['e', tf.name, '--json'])
        self.assertIn('FAILED:', output)

    def test_json_files_equivalence_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json") as tf1, \
             tempfile.NamedTemporaryFile(suffix=".json") as tf2:
            self._call_main(['c', tf1.name, '--json'])
            self._call_main(['c', tf2.name, '--json'])
            output = self._call_main(['f', tf1.name, tf2.name, '--json'])
        self.assertNotIn('FAILED:', output)

    def test_json_files_equivalence_fail(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json") as tf1, \
             tempfile.NamedTemporaryFile(suffix=".json", mode='w', encoding='utf-8-sig') as tf2:
            self._call_main(['c', tf1.name, '--json'])
            write_aas_json_file(tf2, self._modified_example())
            tf2.flush()
            output = self._call_main(['f', tf1.name, tf2.name, '--json'])
        self.assertIn('FAILED:', output)

    # --- XML ---

    def test_xml_example_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xml") as tf:
            self._call_main(['c', tf.name, '--xml'])
            output = self._call_main(['e', tf.name, '--xml'])
        self.assertNotIn('FAILED:', output)

    def test_xml_example_fail(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xml") as tf:
            write_aas_xml_file(tf, self._modified_example())
            tf.flush()
            output = self._call_main(['e', tf.name, '--xml'])
        self.assertIn('FAILED:', output)

    def test_xml_files_equivalence_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xml") as tf1, \
             tempfile.NamedTemporaryFile(suffix=".xml") as tf2:
            self._call_main(['c', tf1.name, '--xml'])
            self._call_main(['c', tf2.name, '--xml'])
            output = self._call_main(['f', tf1.name, tf2.name, '--xml'])
        self.assertNotIn('FAILED:', output)

    def test_xml_files_equivalence_fail(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xml") as tf1, \
             tempfile.NamedTemporaryFile(suffix=".xml") as tf2:
            self._call_main(['c', tf1.name, '--xml'])
            write_aas_xml_file(tf2, self._modified_example())
            tf2.flush()
            output = self._call_main(['f', tf1.name, tf2.name, '--xml'])
        self.assertIn('FAILED:', output)

    # --- AASX ---

    def test_aasx_example_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".aasx") as tf:
            self._call_main(['c', tf.name, '--xml', '--aasx'])
            output = self._call_main(['e', tf.name, '--xml', '--aasx'])
        self.assertNotIn('FAILED:', output)

    def test_aasx_files_equivalence_success(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".aasx") as tf1, \
             tempfile.NamedTemporaryFile(suffix=".aasx") as tf2:
            self._call_main(['c', tf1.name, '--xml', '--aasx'])
            self._call_main(['c', tf2.name, '--xml', '--aasx'])
            output = self._call_main(['f', tf1.name, tf2.name, '--xml', '--aasx'])
        self.assertNotIn('FAILED:', output)

    def test_aasx_files_equivalence_fail(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".aasx") as tf1, \
                tempfile.NamedTemporaryFile(suffix=".aasx") as tf2:
            self._call_main(['c', tf1.name, '--xml', '--aasx'])

            with aasx.AASXWriter(tf2.name) as writer:
                writer.write_aas([], model.DictIdentifiableStore(), aasx.DictSupplementaryFileContainer())

            output = self._call_main(['f', tf1.name, tf2.name, '--xml', '--aasx'])

        self.assertIn('FAILED:', output)
