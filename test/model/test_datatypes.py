# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import datetime
import unittest

from aas import model


class TestIntTypes(unittest.TestCase):
    def test_parse_int(self):
        self.assertEqual(5, model.datatypes.from_xsd("5", model.datatypes.Integer))
        self.assertEqual(6, model.datatypes.from_xsd("6", model.datatypes.Byte))
        self.assertEqual(7, model.datatypes.from_xsd("7", model.datatypes.NonNegativeInteger))

    def test_serialize_int(self):
        self.assertEqual("5", model.datatypes.xsd_repr(model.datatypes.Integer(5)))
        self.assertEqual("6", model.datatypes.xsd_repr(model.datatypes.Byte(6)))
        self.assertEqual("7", model.datatypes.xsd_repr(model.datatypes.NonNegativeInteger(7)))

    def test_range_error(self):
        with self.assertRaises(ValueError):
            model.datatypes.NonNegativeInteger(-7)
        with self.assertRaises(ValueError):
            model.datatypes.Byte(128)
        with self.assertRaises(ValueError):
            model.datatypes.UnsignedByte(256)
        with self.assertRaises(ValueError):
            model.datatypes.UnsignedByte(1000)
        with self.assertRaises(ValueError):
            model.datatypes.PositiveInteger(0)


class TestStringTypes(unittest.TestCase):
    def test_normalized_string(self):
        self.assertEqual("abc", model.datatypes.NormalizedString("abc"))
        with self.assertRaises(ValueError):
            model.datatypes.NormalizedString("ab\nc")
        with self.assertRaises(ValueError):
            model.datatypes.NormalizedString("ab\tc")
        self.assertEqual("abc", model.datatypes.NormalizedString.from_string("a\r\nb\tc"))


class TestDateTimeTypes(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(datetime.date(2020, 1, 24), model.datatypes.from_xsd("2020-01-24", model.datatypes.Date))

        # TODO test parsing of tzinfo

    def test_parse_datetime(self):
        self.assertEqual(datetime.datetime(2020, 1, 24, 15, 25, 17),
                         model.datatypes.from_xsd("2020-01-24T15:25:17", model.datatypes.DateTime))
        self.assertEqual(datetime.datetime(2020, 1, 24, 15, 25, 17, tzinfo=datetime.timezone.utc),
                         model.datatypes.from_xsd("2020-01-24T15:25:17Z", model.datatypes.DateTime))
        self.assertEqual(datetime.datetime(2020, 1, 24, 15, 25, 17,
                                           tzinfo=datetime.timezone(datetime.timedelta(hours=1))),
                         model.datatypes.from_xsd("2020-01-24T15:25:17+01:00", model.datatypes.DateTime))
        self.assertEqual(datetime.datetime(2020, 1, 24, 15, 25, 17,
                                           tzinfo=datetime.timezone(datetime.timedelta(minutes=-20))),
                         model.datatypes.from_xsd("2020-01-24T15:25:17-00:20", model.datatypes.DateTime))

    def test_parse_time(self):
        self.assertEqual(datetime.time(15, 25, 17),
                         model.datatypes.from_xsd("15:25:17", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone.utc),
                         model.datatypes.from_xsd("15:25:17Z", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone(datetime.timedelta(hours=1))),
                         model.datatypes.from_xsd("15:25:17+01:00", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone(datetime.timedelta(minutes=-20))),
                         model.datatypes.from_xsd("15:25:17-00:20", model.datatypes.Time))


class TestBinaryTypes(unittest.TestCase):
    # TODO
    pass
