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

    def test_trivial_cast(self):
        val = model.datatypes.trivial_cast(5, model.datatypes.UnsignedByte)
        self.assertEqual(5, val)
        self.assertIsInstance(val, model.datatypes.UnsignedByte)

        val = model.datatypes.trivial_cast(-7, model.datatypes.Integer)
        self.assertEqual(-7, val)
        self.assertIsInstance(val, model.datatypes.Integer)

        with self.assertRaises(ValueError):
            model.datatypes.trivial_cast(-7, model.datatypes.PositiveInteger)
        with self.assertRaises(TypeError):
            model.datatypes.trivial_cast(6.7, model.datatypes.Integer)
        with self.assertRaises(TypeError):
            model.datatypes.trivial_cast("17", model.datatypes.Int)


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
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone.utc),
                         model.datatypes.from_xsd("2020-01-24Z", model.datatypes.Date))
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone(datetime.timedelta(hours=11, minutes=20))),
                         model.datatypes.from_xsd("2020-01-24+11:20", model.datatypes.Date))
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone(datetime.timedelta(hours=-8))),
                         model.datatypes.from_xsd("2020-01-24-08:00", model.datatypes.Date))

    # TODO test parsing and serializing of partial dates

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

    def test_serialize_datetime(self):
        self.assertEqual("2020-01-24T15:25:17",
                         model.datatypes.xsd_repr(model.datatypes.DateTime(2020, 1, 24, 15, 25, 17)))
        self.assertEqual("2020-01-24T15:25:17+00:00",
                         model.datatypes.xsd_repr(
                             model.datatypes.DateTime(2020, 1, 24, 15, 25, 17, tzinfo=datetime.timezone.utc)))
        self.assertEqual("2020-01-24T15:25:17+01:00",
                         model.datatypes.xsd_repr(
                             model.datatypes.DateTime(2020, 1, 24, 15, 25, 17,
                                                      tzinfo=datetime.timezone(datetime.timedelta(hours=1)))))
        self.assertEqual("2020-01-24T15:25:17-00:20",
                         model.datatypes.xsd_repr(
                             model.datatypes.DateTime(2020, 1, 24, 15, 25, 17,
                                                      tzinfo=datetime.timezone(datetime.timedelta(minutes=-20)))))

    def test_parse_time(self):
        self.assertEqual(datetime.time(15, 25, 17),
                         model.datatypes.from_xsd("15:25:17", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone.utc),
                         model.datatypes.from_xsd("15:25:17Z", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone(datetime.timedelta(hours=1))),
                         model.datatypes.from_xsd("15:25:17+01:00", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone(datetime.timedelta(minutes=-20))),
                         model.datatypes.from_xsd("15:25:17-00:20", model.datatypes.Time))

    def test_trivial_cast(self):
        val = model.datatypes.trivial_cast(datetime.date(2017, 11, 13), model.datatypes.Date)
        self.assertEqual(model.datatypes.Date(2017, 11, 13), val)
        self.assertIsInstance(val, model.datatypes.Date)
        with self.assertRaises(TypeError):
            model.datatypes.trivial_cast("2017-25-13", model.datatypes.Date)


class TestBinaryTypes(unittest.TestCase):
    # TODO
    pass
