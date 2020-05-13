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

import io
import logging
import unittest

from aas import model
from aas.adapter.xml import read_aas_xml_file
from lxml import etree  # type: ignore
from typing import Iterable, Type, Union


def _xml_wrap(xml: str) -> str:
    return \
        """<?xml version="1.0" encoding="utf-8" ?>""" \
        """<aas:aasenv xmlns:aas="http://www.admin-shell.io/aas/2/0" """ \
        """xmlns:IEC61360="http://www.admin-shell.io/IEC61360/2/0" """ \
        """xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" """ \
        """xsi:schemaLocation="http://www.admin-shell.io/aas/2/0 AAS.xsd """ \
        """http://www.admin-shell.io/IEC61360/2/0 IEC61360.xsd">""" \
        + xml + """</aas:aasenv>"""


def _root_cause(exception: BaseException) -> BaseException:
    while exception.__cause__ is not None:
        exception = exception.__cause__
    return exception


class XMLDeserializationTest(unittest.TestCase):
    def _assertInExceptionAndLog(self, xml: str, strings: Union[Iterable[str], str], error_type: Type[BaseException],
                                 log_level: int) -> None:
        """
        Runs read_xml_aas_file in failsafe mode and checks if each string is contained in the first message logged.
        Then runs it in non-failsafe mode and checks if each string is contained in the first error raised.

        :param xml: The xml document to parse.
        :param strings: One or more strings to match.
        :param error_type: The expected error type.
        :param log_level: The log level on which the string is expected.
        """
        if isinstance(strings, str):
            strings = [strings]
        bytes_io = io.BytesIO(xml.encode("utf-8"))
        with self.assertLogs(logging.getLogger(), level=log_level) as log_ctx:
            read_aas_xml_file(bytes_io, True)
        for s in strings:
            self.assertIn(s, log_ctx.output[0])
        with self.assertRaises(error_type) as err_ctx:
            read_aas_xml_file(bytes_io, False)
        cause = _root_cause(err_ctx.exception)
        for s in strings:
            self.assertIn(s, str(cause))

    def test_malformed_xml(self) -> None:
        xml = (
            "invalid xml",
            _xml_wrap("<<>>><<<<<"),
            _xml_wrap("<aas:submodels><aas:submodel/>")
        )
        for s in xml:
            bytes_io = io.BytesIO(s.encode("utf-8"))
            with self.assertRaises(etree.XMLSyntaxError):
                read_aas_xml_file(bytes_io, False)
            with self.assertLogs(logging.getLogger(), level=logging.ERROR):
                read_aas_xml_file(bytes_io, True)

    def test_invalid_list_name(self) -> None:
        xml = _xml_wrap("<aas:invalidList></aas:invalidList>")
        self._assertInExceptionAndLog(xml, "aas:invalidList", TypeError, logging.WARNING)

    def test_invalid_element_in_list(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:invalidElement/>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, ["aas:invalidElement", "aas:assets"], KeyError, logging.WARNING)

    def test_missing_identification_attribute(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:asset>
                <aas:identification>http://acplt.org/test_asset</aas:identification>
                <aas:kind>Instance</aas:kind>
            </aas:asset>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, "idType", KeyError, logging.ERROR)

    def test_invalid_identification_attribute_value(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:asset>
                <aas:identification idType="invalid">http://acplt.org/test_asset</aas:identification>
                <aas:kind>Instance</aas:kind>
            </aas:asset>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, ["idType", "invalid"], ValueError, logging.ERROR)

    def test_missing_asset_kind(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:asset>
            </aas:asset>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, "aas:kind", KeyError, logging.ERROR)

    def test_missing_asset_kind_text(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:asset>
                <aas:kind></aas:kind>
            </aas:asset>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, "aas:kind", KeyError, logging.ERROR)

    def test_invalid_asset_kind_text(self) -> None:
        xml = _xml_wrap("""
        <aas:assets>
            <aas:asset>
                <aas:kind>invalidKind</aas:kind>
            </aas:asset>
        </aas:assets>
        """)
        self._assertInExceptionAndLog(xml, ["aas:kind", "invalidKind"], ValueError, logging.ERROR)

    def test_invalid_boolean(self) -> None:
        xml = _xml_wrap("""
        <aas:conceptDescriptions>
            <aas:conceptDescription>
                <aas:identification idType="IRI">http://acplt.org/test_asset</aas:identification>
                <aas:isCaseOf>
                    <aas:keys>
                         <aas:key idType="IRI" local="False" type="GlobalReference">http://acplt.org/test_ref</aas:key>
                    </aas:keys>
                </aas:isCaseOf>
            </aas:conceptDescription>
        </aas:conceptDescriptions>
        """)
        self._assertInExceptionAndLog(xml, "False", ValueError, logging.ERROR)

    def test_no_modeling_kind(self) -> None:
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:identification idType="IRI">http://acplt.org/test_submodel</aas:identification>
                <aas:submodelElements/>
            </aas:submodel>
        </aas:submodels>
        """)
        # should get parsed successfully
        object_store = read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), False)
        # modeling kind should default to INSTANCE
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        assert(isinstance(submodel, model.Submodel))  # to make mypy happy
        self.assertEqual(submodel.kind, model.ModelingKind.INSTANCE)

    def test_reference_kind_mismatch(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:identification idType="IRI">http://acplt.org/test_aas</aas:identification>
                <aas:assetRef>
                    <aas:keys>
                        <aas:key idType="IRI" local="false" type="GlobalReference">http://acplt.org/test_ref</aas:key>
                    </aas:keys>
                </aas:assetRef>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        """)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as context:
            read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), False)
        self.assertIn("GLOBAL_REFERENCE", context.output[0])
        self.assertIn("IRI=http://acplt.org/test_ref", context.output[0])
        self.assertIn("Asset", context.output[0])

    def test_invalid_submodel_element(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyaas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:identification idType="IRI">http://acplt.org/test_submodel</aas:identification>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:invalidSubmodelElement/>
                    </aas:submodelElement>
                </aas:submodelElements>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "aas:invalidSubmodelElement", KeyError, logging.ERROR)

    def test_invalid_constraint(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyaas/-/issues/56
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:identification idType="IRI">http://acplt.org/test_submodel</aas:identification>
                <aas:submodelElements/>
                <aas:qualifier>
                    <aas:invalidConstraint/>
                </aas:qualifier>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "aas:invalidConstraint", KeyError, logging.ERROR)

    def test_operation_variable_no_submodel_element(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyaas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:identification idType="IRI">http://acplt.org/test_submodel</aas:identification>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:operation>
                            <aas:idShort>test_operation</aas:idShort>
                            <aas:outputVariable>
                                <aas:value/>
                            </aas:outputVariable>
                        </aas:operation>
                    </aas:submodelElement>
                </aas:submodelElements>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "aas:value", KeyError, logging.ERROR)

    def test_operation_variable_too_many_submodel_elements(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyaas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:identification idType="IRI">http://acplt.org/test_submodel</aas:identification>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:operation>
                            <aas:idShort>test_operation</aas:idShort>
                            <aas:outputVariable>
                                <aas:value>
                                    <aas:file>
                                        <aas:idShort>test_file</aas:idShort>
                                        <aas:mimeType>application/problem+xml</aas:mimeType>
                                    </aas:file>
                                    <aas:file>
                                        <aas:idShort>test_file2</aas:idShort>
                                        <aas:mimeType>application/problem+xml</aas:mimeType>
                                    </aas:file>
                                </aas:value>
                            </aas:outputVariable>
                        </aas:operation>
                    </aas:submodelElement>
                </aas:submodelElements>
            </aas:submodel>
        </aas:submodels>
        """)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as context:
            read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), False)
        self.assertIn("aas:value", context.output[0])
