# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
import datetime
import hashlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch, ANY

from aas_compliance_tool.cli import main, parse_cli_arguments
from basyx.aas import model
from basyx.aas.adapter import aasx
from basyx.aas.adapter.json import read_aas_json_file
from basyx.aas.adapter.xml import read_aas_xml_file
from basyx.aas.examples.data import create_example
from basyx.aas.examples.data._helper import AASDataChecker


class ComplianceToolParserTest(unittest.TestCase):
    def test_json_xml_mutually_exclusive(self):
        parser = parse_cli_arguments()
        with self.assertRaises(SystemExit) as cm:
            with redirect_stderr(StringIO()):
                parser.parse_args(["d", "f.json", "--json", "--xml"])
        self.assertEqual(2, cm.exception.code)


class ComplianceToolActionTest(unittest.TestCase):
    def setUp(self):
        self._json_patcher = patch('aas_compliance_tool.cli.compliance_tool_json')
        self._xml_patcher = patch('aas_compliance_tool.cli.compliance_tool_xml')
        self._aasx_patcher = patch('aas_compliance_tool.cli.compliance_tool_aasx')
        self.mock_json = self._json_patcher.start()
        self.mock_xml = self._xml_patcher.start()
        self.mock_aasx = self._aasx_patcher.start()

    def tearDown(self):
        self._json_patcher.stop()
        self._xml_patcher.stop()
        self._aasx_patcher.stop()

    def _call_main(self, args):
        with patch('sys.argv', ['compliance_tool'] + args):
            with redirect_stdout(StringIO()):
                main()

    def test_route_d_json(self):
        self._call_main(['d', 'f.json', '--json'])
        self.mock_json.check_deserialization.assert_called_once_with('f.json', ANY)

    def test_route_d_xml(self):
        self._call_main(['d', 'f.xml', '--xml'])
        self.mock_xml.check_deserialization.assert_called_once_with('f.xml', ANY)

    def test_route_d_aasx(self):
        self._call_main(['d', 'f.aasx', '--json', '--aasx'])
        self.mock_aasx.check_deserialization.assert_called_once_with('f.aasx', ANY)

    def test_route_e_json(self):
        self._call_main(['e', 'f.json', '--json'])
        self.mock_json.check_aas_example.assert_called_once_with('f.json', ANY, check_extensions=True)

    def test_route_e_xml(self):
        self._call_main(['e', 'f.xml', '--xml'])
        self.mock_xml.check_aas_example.assert_called_once_with('f.xml', ANY, check_extensions=True)

    def test_route_e_aasx(self):
        self._call_main(['e', 'f.aasx', '--json', '--aasx'])
        self.mock_aasx.check_aas_example.assert_called_once_with('f.aasx', ANY, check_extensions=True)

    def test_route_f_json(self):
        self._call_main(['f', 'a.json', 'b.json', '--json'])
        self.mock_json.check_json_files_equivalence.assert_called_once_with('a.json', 'b.json', ANY,
                                                                            check_extensions=True)

    def test_route_f_xml(self):
        self._call_main(['f', 'a.xml', 'b.xml', '--xml'])
        self.mock_xml.check_xml_files_equivalence.assert_called_once_with('a.xml', 'b.xml', ANY,
                                                                          check_extensions=True)

    def test_route_f_aasx(self):
        self._call_main(['f', 'a.aasx', 'b.aasx', '--json', '--aasx'])
        self.mock_aasx.check_aasx_files_equivalence.assert_called_once_with('a.aasx', 'b.aasx', ANY,
                                                                            check_extensions=True)

    def test_route_f_missing_file2(self):
        with self.assertRaises(SystemExit) as cm:
            with redirect_stderr(StringIO()):
                self._call_main(['f', 'f.json', '--json'])

        self.assertEqual(2, cm.exception.code)


class ComplianceToolCreateTests(unittest.TestCase):
    def _call_main(self, args) -> str:
        buf = StringIO()
        with patch('sys.argv', ['compliance_tool'] + args):
            with redirect_stdout(buf):
                main()
        return buf.getvalue()

    def test_create_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:

            output = self._call_main(['c', tf.name, '--json'])

            self.assertIn('SUCCESS:      Create example data', output)
            self.assertIn('SUCCESS:      Open file', output)
            self.assertIn('SUCCESS:      Write data to file', output)

            json_store = read_aas_json_file(tf, failsafe=False)
            checker = AASDataChecker(raise_immediately=True)
            checker.check_identifiable_store(json_store, create_example())

    def test_create_xml(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            output = self._call_main(['c', tf.name, '--xml'])

            self.assertIn('SUCCESS:      Create example data', output)
            self.assertIn('SUCCESS:      Open file', output)
            self.assertIn('SUCCESS:      Write data to file', output)
            xml_store = read_aas_xml_file(tf, failsafe=False)
            checker = AASDataChecker(raise_immediately=True)
            checker.check_identifiable_store(xml_store, create_example())

    def test_create_aasx_xml(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            output = self._call_main(['c', tf.name, '--xml', '--aasx'])

            self.assertIn('SUCCESS:      Create example data', output)
            self.assertIn('SUCCESS:      Open file', output)
            self.assertIn('SUCCESS:      Write data to file', output)

            new_data: model.DictIdentifiableStore = model.DictIdentifiableStore()
            new_files = aasx.DictSupplementaryFileContainer()
            with aasx.AASXReader(tf) as reader:
                reader.read_into(new_data, new_files)
                new_cp = reader.get_core_properties()

        self.assertIsInstance(new_cp.created, datetime.datetime)
        self.assertAlmostEqual(new_cp.created, datetime.datetime(2020, 1, 1, 0, 0, 0),
                               delta=datetime.timedelta(milliseconds=20))
        self.assertEqual(new_cp.creator, "Eclipse BaSyx Python Testing Framework")
        self.assertEqual(new_cp.description, "Test_Description")
        self.assertEqual(new_cp.lastModifiedBy, "Eclipse BaSyx Python Testing Framework Compliance Tool")
        self.assertIsInstance(new_cp.modified, datetime.datetime)
        self.assertAlmostEqual(new_cp.modified, datetime.datetime(2020, 1, 1, 0, 0, 1),
                               delta=datetime.timedelta(milliseconds=20))
        self.assertEqual(new_cp.revision, "1.0")
        self.assertEqual(new_cp.version, "2.0.1")
        self.assertEqual(new_cp.title, "Test Title")
        self.assertEqual(new_files.get_content_type("/TestFile.pdf"), "application/pdf")
        file_content = io.BytesIO()
        new_files.write_file("/TestFile.pdf", file_content)
        self.assertEqual(hashlib.sha1(file_content.getvalue()).hexdigest(),
                         "78450a66f59d74c073bf6858db340090ea72a8b1")

    def test_logfile(self):
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            with tempfile.NamedTemporaryFile("w+", encoding='utf-8-sig', suffix=".log") as lf:

                output = self._call_main(['c', tf.name, '--json', '-l', lf.name])

                logfile_content = lf.read()
        # print() appends a newline that file.write() does not
        self.assertEqual(logfile_content, output.rstrip('\n'))
