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

import dateutil

from aas import model


class TestIntTypes(unittest.TestCase):
    def test_parse_int(self) -> None:
        self.assertEqual(5, model.datatypes.from_xsd("5", model.datatypes.Integer))
        self.assertEqual(6, model.datatypes.from_xsd("6", model.datatypes.Byte))
        self.assertEqual(7, model.datatypes.from_xsd("7", model.datatypes.NonNegativeInteger))

    def test_serialize_int(self) -> None:
        self.assertEqual("5", model.datatypes.xsd_repr(model.datatypes.Integer(5)))
        self.assertEqual("6", model.datatypes.xsd_repr(model.datatypes.Byte(6)))
        self.assertEqual("7", model.datatypes.xsd_repr(model.datatypes.NonNegativeInteger(7)))

    def test_range_error(self) -> None:
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

    def test_trivial_cast(self) -> None:
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
    def test_normalized_string(self) -> None:
        self.assertEqual("abc", model.datatypes.NormalizedString("abc"))
        with self.assertRaises(ValueError):
            model.datatypes.NormalizedString("ab\nc")
        with self.assertRaises(ValueError):
            model.datatypes.NormalizedString("ab\tc")
        self.assertEqual("abc", model.datatypes.NormalizedString.from_string("a\r\nb\tc"))

    def test_serialize(self) -> None:
        self.assertEqual("abc", model.datatypes.from_xsd("abc", model.datatypes.String))
        self.assertEqual("abc", model.datatypes.from_xsd("abc", model.datatypes.NormalizedString))
        self.assertEqual("abc", model.datatypes.xsd_repr(model.datatypes.String("abc")))
        self.assertEqual("abc", model.datatypes.xsd_repr(model.datatypes.NormalizedString("abc")))


class TestDateTimeTypes(unittest.TestCase):
    def test_parse_duration(self) -> None:
        # Examples from https://www.w3.org/TR/xmlschema-2/#duration-lexical-repr
        self.assertEqual(dateutil.relativedelta.relativedelta(years=1, months=2, hours=2),
                         model.datatypes.from_xsd("P1Y2MT2H", model.datatypes.Duration))
        self.assertEqual(dateutil.relativedelta.relativedelta(months=1347),
                         model.datatypes.from_xsd("P0Y1347M", model.datatypes.Duration))
        self.assertEqual(dateutil.relativedelta.relativedelta(months=1347),
                         model.datatypes.from_xsd("P0Y1347M0D", model.datatypes.Duration))
        self.assertEqual(dateutil.relativedelta.relativedelta(months=-1347),
                         model.datatypes.from_xsd("-P1347M", model.datatypes.Duration))
        self.assertEqual(dateutil.relativedelta.relativedelta(years=1, months=2, days=3, hours=10, minutes=30),
                         model.datatypes.from_xsd("P1Y2M3DT10H30M", model.datatypes.Duration))
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("P-1347M", model.datatypes.Duration)

    def test_parse_date(self) -> None:
        self.assertEqual(datetime.date(2020, 1, 24), model.datatypes.from_xsd("2020-01-24", model.datatypes.Date))
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone.utc),
                         model.datatypes.from_xsd("2020-01-24Z", model.datatypes.Date))
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone(datetime.timedelta(hours=11, minutes=20))),
                         model.datatypes.from_xsd("2020-01-24+11:20", model.datatypes.Date))
        self.assertEqual(model.datatypes.Date(2020, 1, 24, datetime.timezone(datetime.timedelta(hours=-8))),
                         model.datatypes.from_xsd("2020-01-24-08:00", model.datatypes.Date))
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("2020-01-24+11", model.datatypes.Date)

    def test_serialize_date(self) -> None:
        self.assertEqual("2020-01-24", model.datatypes.xsd_repr(model.datatypes.Date(2020, 1, 24)))
        self.assertEqual("2020-01-24Z", model.datatypes.xsd_repr(
            model.datatypes.Date(2020, 1, 24, datetime.timezone.utc)))
        self.assertEqual("2020-01-24+11:20", model.datatypes.xsd_repr(
            model.datatypes.Date(2020, 1, 24, datetime.timezone(datetime.timedelta(hours=11, minutes=20)))))

    def test_parse_partial_dates(self) -> None:
        self.assertEqual(model.datatypes.GYear(2019),
                         model.datatypes.from_xsd("2019", model.datatypes.GYear))
        self.assertEqual(model.datatypes.GMonth(7),
                         model.datatypes.from_xsd("--07", model.datatypes.GMonth))
        self.assertEqual(model.datatypes.GYearMonth(2020, 5),
                         model.datatypes.from_xsd("2020-05", model.datatypes.GYearMonth))
        self.assertEqual(model.datatypes.GMonthDay(12, 6),
                         model.datatypes.from_xsd("--12-06", model.datatypes.GMonthDay))
        self.assertEqual(model.datatypes.GDay(23),
                         model.datatypes.from_xsd("---23", model.datatypes.GDay))
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("--23", model.datatypes.GDay)
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("---23", model.datatypes.GMonth)
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("10", model.datatypes.GYear)
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("25-10", model.datatypes.GMonthDay)
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("10-10", model.datatypes.GYearMonth)

    def test_serialize_partial_dates(self) -> None:
        self.assertEqual("2019", model.datatypes.xsd_repr(model.datatypes.GYear(2019)))
        self.assertEqual("2019Z", model.datatypes.xsd_repr(model.datatypes.GYear(2019, datetime.timezone.utc)))
        self.assertEqual("--07", model.datatypes.xsd_repr(model.datatypes.GMonth(7)))
        self.assertEqual("2020-05", model.datatypes.xsd_repr(model.datatypes.GYearMonth(2020, 5)))
        self.assertEqual("2020-05-05:15", model.datatypes.xsd_repr(
            model.datatypes.GYearMonth(2020, 5, datetime.timezone(datetime.timedelta(hours=-5, minutes=-15)))))
        self.assertEqual("--12-06", model.datatypes.xsd_repr(model.datatypes.GMonthDay(12, 6)))
        self.assertEqual("--12-06+07:00", model.datatypes.xsd_repr(
            model.datatypes.GMonthDay(12, 6, datetime.timezone(datetime.timedelta(hours=7)))))
        self.assertEqual("---23", model.datatypes.xsd_repr(model.datatypes.GDay(23)))

    def test_parse_datetime(self) -> None:
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
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("--2020-01-24T15:25:17-00:20", model.datatypes.DateTime)

    def test_serialize_datetime(self) -> None:
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

    def test_parse_time(self) -> None:
        self.assertEqual(datetime.time(15, 25, 17),
                         model.datatypes.from_xsd("15:25:17", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone.utc),
                         model.datatypes.from_xsd("15:25:17Z", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, 250000, tzinfo=datetime.timezone(datetime.timedelta(hours=1))),
                         model.datatypes.from_xsd("15:25:17.25+01:00", model.datatypes.Time))
        self.assertEqual(datetime.time(15, 25, 17, tzinfo=datetime.timezone(datetime.timedelta(minutes=-20))),
                         model.datatypes.from_xsd("15:25:17-00:20", model.datatypes.Time))

    def test_serialize_time(self) -> None:
        self.assertEqual("15:25:17", model.datatypes.xsd_repr(datetime.time(15, 25, 17)))
        self.assertEqual("15:25:17+00:00", model.datatypes.xsd_repr(
            datetime.time(15, 25, 17, tzinfo=datetime.timezone.utc)))
        self.assertEqual("15:25:17.250000+01:00", model.datatypes.xsd_repr(
            datetime.time(15, 25, 17, 250000, tzinfo=datetime.timezone(datetime.timedelta(hours=1)))))

    def test_trivial_cast(self) -> None:
        val = model.datatypes.trivial_cast(datetime.date(2017, 11, 13), model.datatypes.Date)
        self.assertEqual(model.datatypes.Date(2017, 11, 13), val)
        self.assertIsInstance(val, model.datatypes.Date)
        with self.assertRaises(TypeError):
            model.datatypes.trivial_cast("2017-25-13", model.datatypes.Date)


class TestBoolType(unittest.TestCase):
    def test_parse_bool(self) -> None:
        self.assertEqual(True, model.datatypes.from_xsd("true", model.datatypes.Boolean))
        self.assertEqual(True, model.datatypes.from_xsd("1", model.datatypes.Boolean))
        self.assertEqual(False, model.datatypes.from_xsd("false", model.datatypes.Boolean))
        self.assertEqual(False, model.datatypes.from_xsd("0", model.datatypes.Boolean))
        with self.assertRaises(ValueError):
            model.datatypes.from_xsd("TRUE", model.datatypes.Boolean)

    def test_serialize_bool(self) -> None:
        self.assertEqual("true", model.datatypes.xsd_repr(True))
        self.assertEqual("false", model.datatypes.xsd_repr(False))


class TestBinaryTypes(unittest.TestCase):
    def test_base64(self) -> None:
        self.assertEqual(b"abc\0def", model.datatypes.from_xsd("YWJjAGRlZg==", model.datatypes.Base64Binary))
        self.assertEqual("YWJjAGRlZg==", model.datatypes.xsd_repr(model.datatypes.Base64Binary(b"abc\0def")))
        val = model.datatypes.trivial_cast(b"abc\0def", model.datatypes.Base64Binary)
        self.assertEqual(model.datatypes.Base64Binary(b"abc\0def"), val)
        self.assertIsInstance(val, model.datatypes.Base64Binary)

    def test_hex(self) -> None:
        self.assertEqual(b"abc\0def", model.datatypes.from_xsd("61626300646566", model.datatypes.HexBinary))
        self.assertEqual("61626300646566", model.datatypes.xsd_repr(model.datatypes.HexBinary(b"abc\0def")))
        val = model.datatypes.trivial_cast(b"abc\0def", model.datatypes.HexBinary)
        self.assertEqual(model.datatypes.HexBinary(b"abc\0def"), val)
        self.assertIsInstance(val, model.datatypes.HexBinary)
