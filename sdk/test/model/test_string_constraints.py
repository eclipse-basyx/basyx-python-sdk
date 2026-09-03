# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

import unittest

from basyx.aas import model
from basyx.aas.model import _string_constraints


class StringConstraintsTest(unittest.TestCase):
    def test_identifier(self) -> None:
        identifier: model.Identifier = ""
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_identifier(identifier)
        self.assertEqual(
            "Identifier has a minimum length of 1! (length: 0)", cm.exception.args[0]
        )
        identifier = "a" * 2049
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_identifier(identifier)
        self.assertEqual(
            "Identifier has a maximum length of 2048! (length: 2049)",
            cm.exception.args[0],
        )
        identifier = "a" * 2048
        _string_constraints.check_identifier(identifier)

    def test_version_type(self) -> None:
        version: model.VersionType = ""
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_version_type(version)
        self.assertEqual(
            "VersionType has a minimum length of 1! (length: 0)", cm.exception.args[0]
        )
        version = "1" * 5
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_version_type(version)
        self.assertEqual(
            "VersionType has a maximum length of 4! (length: 5)", cm.exception.args[0]
        )
        version = "0" * 4
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_version_type(version)
        self.assertEqual(
            "VersionType must match the pattern '([0-9]|[1-9][0-9]*)'! (value: '0000')",
            cm.exception.args[0],
        )
        version = "0"
        _string_constraints.check_version_type(version)

    def test_aasd_130(self) -> None:
        name: model.NameType = "\0"
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_name_type(name)
        self.assertEqual(
            r"Every string must match the pattern '[\t\n\r -\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*'! "
            r"(value: '\x00')",
            cm.exception.args[0],
        )
        name = "\ud800"
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_name_type(name)
        self.assertEqual(
            r"Every string must match the pattern '[\t\n\r -\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*'! "
            r"(value: '\ud800')",
            cm.exception.args[0],
        )
        name = "\ufffe"
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_name_type(name)
        self.assertEqual(
            r"Every string must match the pattern '[\t\n\r -\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*'! "
            r"(value: '\ufffe')",
            cm.exception.args[0],
        )
        name = "this\ris\na\tvalid täst\uffdd\U0010ab12"
        _string_constraints.check_name_type(name)


class StringConstraintsDecoratorTest(unittest.TestCase):
    @_string_constraints.constrain_path_type("some_attr")
    class DummyClass:
        def __init__(self, path: model.PathType):
            self.some_attr: model.PathType = path

    def test_path_type_decoration(self) -> None:
        with self.assertRaises(ValueError) as cm:
            self.DummyClass("")
        self.assertEqual(
            "DummyClass.some_attr (PathType) has a minimum length of 1! (length: 0)",
            cm.exception.args[0],
        )
        dc = self.DummyClass("a")
        with self.assertRaises(ValueError) as cm:
            dc.some_attr = "a" * 2049
        self.assertEqual(
            "DummyClass.some_attr (PathType) has a maximum length of 2048! (length: 2049)",
            cm.exception.args[0],
        )
        self.assertEqual(dc.some_attr, "a")

    def test_ignore_none_values(self) -> None:
        # None values should be ignored as some decorated attributes are optional. As shown in the following,
        # such assignments are caught by the typechecker anyway.
        dc = self.DummyClass(None)  # type: ignore
        self.assertIsNone(dc.some_attr)
        dc.some_attr = None  # type: ignore

    def test_attribute_name_conflict(self) -> None:
        # We don't want to overwrite existing attributes in case of a name conflict
        with self.assertRaises(AttributeError) as cm:

            @_string_constraints.constrain_revision_type("foo")
            class DummyClass:
                foo = property()

        self.assertEqual(
            "DummyClass already has an attribute named 'foo'", cm.exception.args[0]
        )

        with self.assertRaises(AttributeError) as cm:

            @_string_constraints.constrain_label_type("bar")
            class DummyClass2:
                @property
                def bar(self):
                    return "baz"

        self.assertEqual(
            "DummyClass2 already has an attribute named 'bar'", cm.exception.args[0]
        )


class StringConstraintsAttributeTest(unittest.TestCase):
    """
    Tests that constraint violations name the attribute that caused them, see issue #203
    """

    def test_check_function_attribute(self) -> None:
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_name_type("", attribute="Property.id_short")
        self.assertEqual(
            "Property.id_short (NameType) has a minimum length of 1! (length: 0)",
            cm.exception.args[0],
        )
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_version_type(
                "v1", attribute="AdministrativeInformation.version"
            )
        self.assertEqual(
            "AdministrativeInformation.version (VersionType) must match the pattern "
            "'([0-9]|[1-9][0-9]*)'! (value: 'v1')",
            cm.exception.args[0],
        )
        with self.assertRaises(ValueError) as cm:
            _string_constraints.check_name_type("\0", attribute="Property.id_short")
        self.assertEqual(
            r"Property.id_short (NameType): Every string must match the pattern "
            r"'[\t\n\r -\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*'! (value: '\x00')",
            cm.exception.args[0],
        )

    def test_metamodel_attributes(self) -> None:
        # Note that the reported class is the class the attribute was assigned on, not the class the constraint
        # was defined on: `category` and `id_short` are constrained in Referable, but reported as Property.
        expected_messages = {
            lambda: model.Property(
                "a" * 129, model.datatypes.Int
            ): "Property.id_short (NameType) has a maximum length of 128! (length: 129)",
            lambda: model.Property(
                "Prop", model.datatypes.Int, category="a" * 129
            ): "Property.category (NameType) has a maximum length of 128! (length: 129)",
            lambda: model.Submodel(
                ""
            ): "Submodel.id (Identifier) has a minimum length of 1! (length: 0)",
            lambda: model.File(
                "File", "a" * 129
            ): "File.content_type (ContentType) has a maximum length of 128! (length: 129)",
            lambda: model.Qualifier(
                "", model.datatypes.Int
            ): "Qualifier.type (QualifierType) has a minimum length of 1! (length: 0)",
            lambda: model.Extension(
                "a" * 129
            ): "Extension.name (NameType) has a maximum length of 128! (length: 129)",
            lambda: model.Key(
                model.KeyTypes.SUBMODEL, ""
            ): "Key.value (Identifier) has a minimum length of 1! (length: 0)",
            lambda: model.AdministrativeInformation(
                version="1", revision="a"
            ): "AdministrativeInformation.revision (RevisionType) must match the pattern "
            "'([0-9]|[1-9][0-9]*)'! (value: 'a')",
            lambda: model.SpecificAssetId(
                "a" * 65, "value"
            ): "SpecificAssetId.name (LabelType) has a maximum length of 64! (length: 65)",
            lambda: model.AssetInformation(
                global_asset_id=""
            ): "AssetInformation.global_asset_id (Identifier) has a minimum length of 1! (length: 0)",
            lambda: model.Entity(
                "Entity", model.EntityType.SELF_MANAGED_ENTITY, global_asset_id=""
            ): "Entity.global_asset_id (Identifier) has a minimum length of 1! (length: 0)",
        }
        for construct, expected_message in expected_messages.items():
            with self.subTest(expected_message):
                with self.assertRaises(ValueError) as cm:
                    construct()
                self.assertEqual(expected_message, cm.exception.args[0])

    def test_subclasses(self) -> None:
        # Subclasses defined outside of this repository are reported by their own name as well
        class MyProperty(model.Property):
            pass

        class MyEntity(model.Entity):
            pass

        with self.assertRaises(ValueError) as cm:
            MyProperty("a" * 129, model.datatypes.Int)
        self.assertEqual(
            "MyProperty.id_short (NameType) has a maximum length of 128! (length: 129)",
            cm.exception.args[0],
        )
        with self.assertRaises(ValueError) as cm:
            MyEntity("Entity", model.EntityType.SELF_MANAGED_ENTITY, global_asset_id="")
        self.assertEqual(
            "MyEntity.global_asset_id (Identifier) has a minimum length of 1! (length: 0)",
            cm.exception.args[0],
        )
