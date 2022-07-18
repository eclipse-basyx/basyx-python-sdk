# Copyright (c) 2020 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import io
import logging
import unittest

from basyx.aas import model
from basyx.aas.adapter.xml import StrictAASFromXmlDecoder, XMLConstructables, read_aas_xml_file, \
    read_aas_xml_file_into, read_aas_xml_element
from lxml import etree  # type: ignore
from typing import Iterable, Type, Union


def _xml_wrap(xml: str) -> str:
    return \
        """<?xml version="1.0" encoding="utf-8" ?>""" \
        """<aas:aasenv xmlns:aas="http://www.admin-shell.io/aas/3/0"> """ \
        + xml + """</aas:aasenv>"""


def _root_cause(exception: BaseException) -> BaseException:
    while exception.__cause__ is not None:
        exception = exception.__cause__
    return exception


class XmlDeserializationTest(unittest.TestCase):
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
            read_aas_xml_file(bytes_io, failsafe=True)
        with self.assertRaises(error_type) as err_ctx:
            read_aas_xml_file(bytes_io, failsafe=False)
        cause = _root_cause(err_ctx.exception)
        for s in strings:
            self.assertIn(s, log_ctx.output[0])  # type: ignore
            self.assertIn(s, str(cause))

    def test_malformed_xml(self) -> None:
        xml = (
            "invalid xml",
            _xml_wrap("<<>>><<<<<"),
            _xml_wrap("<aas:submodels><aas:submodel/>")
        )
        for s in xml:
            self._assertInExceptionAndLog(s, [], etree.XMLSyntaxError, logging.ERROR)

    def test_invalid_list_name(self) -> None:
        xml = _xml_wrap("<aas:invalidList></aas:invalidList>")
        self._assertInExceptionAndLog(xml, "aas:invalidList", TypeError, logging.WARNING)

    def test_invalid_element_in_list(self) -> None:
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:invalidElement/>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, ["aas:invalidElement", "aas:submodels"], KeyError, logging.WARNING)

    def test_missing_asset_kind(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:assetInformation>
                </aas:assetInformation>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        """)
        self._assertInExceptionAndLog(xml, "aas:assetKind", KeyError, logging.ERROR)

    def test_missing_asset_kind_text(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:assetInformation>
                    <aas:assetKind></aas:assetKind>
                </aas:assetInformation>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        """)
        self._assertInExceptionAndLog(xml, "aas:assetKind", KeyError, logging.ERROR)

    def test_invalid_asset_kind_text(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:assetInformation>
                    <aas:assetKind>invalidKind</aas:assetKind>
                </aas:assetInformation>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        """)
        self._assertInExceptionAndLog(xml, ["aas:assetKind", "invalidKind"], ValueError, logging.ERROR)

    def test_invalid_boolean(self) -> None:
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:submodelElementCollection>
                            <aas:ordered>False</aas:ordered>
                            <aas:idShort>collection</aas:idShort>
                        </aas:submodelElementCollection>
                    </aas:submodelElement>
                </aas:submodelElements>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "False", ValueError, logging.ERROR)

    def test_no_modeling_kind(self) -> None:
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:submodelElements/>
            </aas:submodel>
        </aas:submodels>
        """)
        # should get parsed successfully
        object_store = read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), failsafe=False)
        # modeling kind should default to INSTANCE
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        assert isinstance(submodel, model.Submodel)  # to make mypy happy
        self.assertEqual(submodel.kind, model.ModelingKind.INSTANCE)

    def test_reference_kind_mismatch(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:assetInformation>
                    <aas:assetKind>Instance</aas:assetKind>
                </aas:assetInformation>
                <aas:derivedFrom type="ModelReference">
                    <aas:keys>
                        <aas:key type="Submodel">http://acplt.org/test_ref</aas:key>
                    </aas:keys>
                </aas:derivedFrom>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        """)
        with self.assertLogs(logging.getLogger(), level=logging.WARNING) as context:
            read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), failsafe=False)
        for s in ("SUBMODEL", "http://acplt.org/test_ref", "AssetAdministrationShell"):
            self.assertIn(s, context.output[0])  # type: ignore

    def test_invalid_submodel_element(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:invalidSubmodelElement/>
                    </aas:submodelElement>
                </aas:submodelElements>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "aas:invalidSubmodelElement", KeyError, logging.ERROR)

    def test_empty_qualifier(self) -> None:
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:submodelElements/>
                <aas:qualifiers>
                    <aas:qualifier/>
                </aas:qualifiers>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, ["aas:qualifier", "has no child aas:type"], KeyError, logging.ERROR)

    def test_operation_variable_no_submodel_element(self) -> None:
        # TODO: simplify this should our suggestion regarding the XML schema get accepted
        # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
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
        # https://git.rwth-aachen.de/acplt/pyi40aas/-/issues/57
        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:submodelElements>
                    <aas:submodelElement>
                        <aas:operation>
                            <aas:idShort>test_operation</aas:idShort>
                            <aas:outputVariable>
                                <aas:value>
                                    <aas:file>
                                        <aas:kind>Template</aas:kind>
                                        <aas:idShort>test_file</aas:idShort>
                                        <aas:contentType>application/problem+xml</aas:contentType>
                                    </aas:file>
                                    <aas:file>
                                        <aas:idShort>test_file2</aas:idShort>
                                        <aas:contentType>application/problem+xml</aas:contentType>
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
            read_aas_xml_file(io.BytesIO(xml.encode("utf-8")), failsafe=False)
        self.assertIn("aas:value", context.output[0])  # type: ignore

    def test_duplicate_identifier(self) -> None:
        xml = _xml_wrap("""
        <aas:assetAdministrationShells>
            <aas:assetAdministrationShell>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:idShort>NotSet</aas:idShort>
                <aas:assetInformation>
                    <aas:assetKind>Instance</aas:assetKind>
                </aas:assetInformation>
            </aas:assetAdministrationShell>
        </aas:assetAdministrationShells>
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_aas</aas:id>
                <aas:idShort>NotSet</aas:idShort>
                <aas:submodelElements/>
            </aas:submodel>
        </aas:submodels>
        """)
        self._assertInExceptionAndLog(xml, "duplicate identifier", KeyError, logging.ERROR)

    def test_duplicate_identifier_object_store(self) -> None:
        sm_id = "http://acplt.org/test_submodel"

        def get_clean_store() -> model.DictObjectStore:
            store: model.DictObjectStore = model.DictObjectStore()
            submodel_ = model.Submodel(sm_id, id_short="test123")
            store.add(submodel_)
            return store

        xml = _xml_wrap("""
        <aas:submodels>
            <aas:submodel>
                <aas:id>http://acplt.org/test_submodel</aas:id>
                <aas:idShort>test456</aas:idShort>
                <aas:submodelElements/>
            </aas:submodel>
        </aas:submodels>
        """)
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        object_store = get_clean_store()
        identifiers = read_aas_xml_file_into(object_store, bytes_io, replace_existing=True, ignore_existing=False)
        self.assertEqual(identifiers.pop(), sm_id)
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test456")

        object_store = get_clean_store()
        with self.assertLogs(logging.getLogger(), level=logging.INFO) as log_ctx:
            identifiers = read_aas_xml_file_into(object_store, bytes_io, replace_existing=False, ignore_existing=True)
        self.assertEqual(len(identifiers), 0)
        self.assertIn("already exists in the object store", log_ctx.output[0])  # type: ignore
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test123")

        object_store = get_clean_store()
        with self.assertRaises(KeyError) as err_ctx:
            identifiers = read_aas_xml_file_into(object_store, bytes_io, replace_existing=False, ignore_existing=False)
        self.assertEqual(len(identifiers), 0)
        cause = _root_cause(err_ctx.exception)
        self.assertIn("already exists in the object store", str(cause))
        submodel = object_store.pop()
        self.assertIsInstance(submodel, model.Submodel)
        self.assertEqual(submodel.id_short, "test123")

    def test_read_aas_xml_element(self) -> None:
        xml = """
        <aas:submodel xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:id>http://acplt.org/test_submodel</aas:id>
            <aas:submodelElements/>
        </aas:submodel>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        submodel = read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL)
        self.assertIsInstance(submodel, model.Submodel)


class XmlDeserializationStrippedObjectsTest(unittest.TestCase):
    def test_stripped_qualifiable(self) -> None:
        xml = """
        <aas:submodel xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:id>http://acplt.org/test_stripped_submodel</aas:id>
            <aas:submodelElements>
                <aas:submodelElement>
                    <aas:operation>
                        <aas:idShort>test_operation</aas:idShort>
                        <aas:qualifiers>
                            <aas:qualifier>
                                <aas:type>test_qualifier</aas:type>
                                <aas:valueType>string</aas:valueType>
                            </aas:qualifier>
                        </aas:qualifiers>
                    </aas:operation>
                </aas:submodelElement>
            </aas:submodelElements>
            <aas:qualifiers>
                <aas:qualifier>
                    <aas:type>test_qualifier</aas:type>
                    <aas:valueType>string</aas:valueType>
                </aas:qualifier>
            </aas:qualifiers>
        </aas:submodel>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        # check if XML with qualifiers can be parsed successfully
        submodel = read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL, failsafe=False)
        self.assertIsInstance(submodel, model.Submodel)
        assert isinstance(submodel, model.Submodel)
        self.assertEqual(len(submodel.qualifier), 1)
        operation = submodel.submodel_element.pop()
        self.assertEqual(len(operation.qualifier), 1)

        # check if qualifiers are ignored in stripped mode
        submodel = read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL, failsafe=False, stripped=True)
        self.assertIsInstance(submodel, model.Submodel)
        assert isinstance(submodel, model.Submodel)
        self.assertEqual(len(submodel.qualifier), 0)
        self.assertEqual(len(submodel.submodel_element), 0)

    def test_stripped_annotated_relationship_element(self) -> None:
        xml = """
        <aas:annotatedRelationshipElement xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:idShort>test_annotated_relationship_element</aas:idShort>
            <aas:first type="ModelReference">
                <aas:keys>
                    <aas:key type="Submodel">http://acplt.org/Test_Submodel</aas:key>
                    <aas:key type="AnnotatedRelationshipElement">test_ref</aas:key>
                </aas:keys>
            </aas:first>
            <aas:second type="ModelReference">
                <aas:keys>
                    <aas:key type="Submodel">http://acplt.org/Test_Submodel</aas:key>
                    <aas:key type="AnnotatedRelationshipElement">test_ref</aas:key>
                </aas:keys>
            </aas:second>
        </aas:annotatedRelationshipElement>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        # XML schema requires annotations to be present, so parsing should fail
        with self.assertRaises(KeyError):
            read_aas_xml_element(bytes_io, XMLConstructables.ANNOTATED_RELATIONSHIP_ELEMENT, failsafe=False)

        # check if it can be parsed in stripped mode
        read_aas_xml_element(bytes_io, XMLConstructables.ANNOTATED_RELATIONSHIP_ELEMENT, failsafe=False, stripped=True)

    def test_stripped_entity(self) -> None:
        xml = """
        <aas:entity xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:idShort>test_entity</aas:idShort>
            <aas:entityType>CoManagedEntity</aas:entityType>
        </aas:entity>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        # XML schema requires statements to be present, so parsing should fail
        with self.assertRaises(KeyError):
            read_aas_xml_element(bytes_io, XMLConstructables.ENTITY, failsafe=False)

        # check if it can be parsed in stripped mode
        read_aas_xml_element(bytes_io, XMLConstructables.ENTITY, failsafe=False, stripped=True)

    def test_stripped_submodel_element_collection(self) -> None:
        xml = """
        <aas:submodelElementCollection xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:idShort>test_collection</aas:idShort>
            <aas:allowDuplicates>true</aas:allowDuplicates>
            <aas:ordered>false</aas:ordered>
        </aas:submodelElementCollection>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        # XML schema requires value to be present, so parsing should fail
        with self.assertRaises(KeyError):
            read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL_ELEMENT_COLLECTION, failsafe=False)

        # check if it can be parsed in stripped mode
        read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL_ELEMENT_COLLECTION, failsafe=False, stripped=True)

    def test_stripped_asset_administration_shell(self) -> None:
        xml = """
        <aas:assetAdministrationShell xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:id>http://acplt.org/test_aas</aas:id>
            <aas:assetInformation>
                <aas:assetKind>Instance</aas:assetKind>
            </aas:assetInformation>
            <aas:submodelRefs>
                <aas:submodelRef type="ModelReference">
                    <aas:keys>
                        <aas:key type="Submodel">http://acplt.org/test_ref</aas:key>
                    </aas:keys>
                </aas:submodelRef>
            </aas:submodelRefs>
        </aas:assetAdministrationShell>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        # check if XML with submodelRef can be parsed successfully
        aas = read_aas_xml_element(bytes_io, XMLConstructables.ASSET_ADMINISTRATION_SHELL, failsafe=False)
        self.assertIsInstance(aas, model.AssetAdministrationShell)
        assert isinstance(aas, model.AssetAdministrationShell)
        self.assertEqual(len(aas.submodel), 1)

        # check if submodelRef is ignored in stripped mode
        aas = read_aas_xml_element(bytes_io, XMLConstructables.ASSET_ADMINISTRATION_SHELL, failsafe=False,
                                   stripped=True)
        self.assertIsInstance(aas, model.AssetAdministrationShell)
        assert isinstance(aas, model.AssetAdministrationShell)
        self.assertEqual(len(aas.submodel), 0)


class XmlDeserializationDerivingTest(unittest.TestCase):
    def test_submodel_constructor_overriding(self) -> None:
        class EnhancedSubmodel(model.Submodel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.enhanced_attribute = "fancy!"

        class EnhancedAASDecoder(StrictAASFromXmlDecoder):
            @classmethod
            def construct_submodel(cls, element: etree.Element, object_class=EnhancedSubmodel, **kwargs) \
                    -> model.Submodel:
                return super().construct_submodel(element, object_class=object_class, **kwargs)

        xml = """
        <aas:submodel xmlns:aas="http://www.admin-shell.io/aas/3/0">
            <aas:id>http://acplt.org/test_stripped_submodel</aas:id>
            <aas:submodelElements/>
        </aas:submodel>
        """
        bytes_io = io.BytesIO(xml.encode("utf-8"))

        submodel = read_aas_xml_element(bytes_io, XMLConstructables.SUBMODEL, decoder=EnhancedAASDecoder)
        self.assertIsInstance(submodel, EnhancedSubmodel)
        assert isinstance(submodel, EnhancedSubmodel)
        self.assertEqual(submodel.enhanced_attribute, "fancy!")
