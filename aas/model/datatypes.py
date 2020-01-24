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
"""
This module defines native Python types for all simple built-in XSD datatypes, as well as functions to (de)serialize
them from/into their lexical XML representation.

See https://www.w3.org/TR/xmlschema-2/#built-in-datatypes for the XSD simple type hierarchy and more information on the
datatypes.

# TODO usage of functions
"""
import base64
import datetime
import decimal
import re
from typing import NamedTuple, Type, Union, Dict

Duration = datetime.timedelta
DateTime = datetime.datetime
Date = datetime.date  # TODO derived type with tzinfo
Time = datetime.time
Boolean = bool
Double = float
Decimal = decimal.Decimal
Integer = int
String = str


class GYearMonth(NamedTuple):
    # TODO add tzdata
    year: int
    month: int

    def into_date(self, day: int) -> datetime.date:
        return datetime.date(self.year, self.month, day)

    @classmethod
    def from_date(cls, date: datetime.date) -> "GYearMonth":
        return cls(date.year, date.month)


class GYear(int):
    # TODO add tzdata
    def into_date(self, month: int, day: int) -> datetime.date:
        return datetime.date(self, month, day)

    @classmethod
    def from_date(cls, date: datetime.date) -> "GYear":
        return cls(date.year)


class GMonthDay(NamedTuple):
    # TODO add tzdata
    month: int
    day: int

    def into_date(self, year: int) -> datetime.date:
        return datetime.date(year, self.month, self.day)

    @classmethod
    def from_date(cls, date: datetime.date) -> "GMonthDay":
        return cls(date.month, date.year)


class GDay(int):
    # TODO add tzdata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 1 <= self <= 31:
            raise ValueError("{} is out of the allowed range for type {}".format(self, self.__class__.__name__))

    def into_date(self, year: int, month: int) -> datetime.date:
        return datetime.date(year, month, self)

    @classmethod
    def from_date(cls, date: datetime.date) -> "GDay":
        return cls(date.day)


class GMonth(int):
    # TODO add tzdata

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 1 <= self <= 12:
            raise ValueError("{} is out of the allowed range for type {}".format(self, self.__class__.__name__))

    def into_date(self, year: int, day: int) -> datetime.date:
        return datetime.date(year, self, day)

    @classmethod
    def from_date(cls, date: datetime.date) -> "GMonth":
        return cls(date.month)


class Base64Binary(bytearray):
    pass


class HexBinary(bytearray):
    pass


class Float(float):
    """ A 32bit IEEE754 float. This can not be represented with Python """
    pass


class Long(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if abs(res) > 2**63-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class Int(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if abs(res) > 2**31-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class Short(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if abs(res) > 2**15-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class Byte(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if abs(res) > 2**7-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class NonPositiveInteger(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if res > 0:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class NegativeInteger(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if res >= 0:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class NonNegativeInteger(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if res < 0:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class PositiveInteger(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if res <= 0:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class UnsignedLong(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if not 0 <= res <= 2**64-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class UnsignedInt(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if not 0 <= res <= 2**32-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class UnsignedShort(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if not 0 <= res <= 2**16-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class UnsignedByte(int):
    def __new__(cls, *args, **kwargs):
        res = int.__new__(cls, *args, **kwargs)
        if not 0 <= res <= 2**8-1:
            raise ValueError("{} is out of the allowed range for type {}".format(res, cls.__name__))
        return res


class AnyURI(str):
    pass


class NormalizedString(str):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ('\r' in self) or ('\n' in self) or ('\t' in self):
            raise ValueError("\\r, \\n and \\t are not allowed in NormalizedStrings")

    @classmethod
    def from_string(cls, value: str) -> "NormalizedString":
        """
        Make a string a normalized string by simply dropping all carriage return, newline and tab characters.
        """
        return cls(value.translate({0xD: None, 0xA: None, 0x9: None}))


AllXSDTypes = (Duration, DateTime, Date, Time, GYearMonth, GYear, GMonthDay, GMonth, GDay, Boolean, Base64Binary,
               HexBinary, Float, Double, Decimal, Integer, Long, Int, Short, Byte, NonPositiveInteger,
               NegativeInteger, NonNegativeInteger, PositiveInteger, UnsignedLong, UnsignedInt, UnsignedShort,
               UnsignedByte, AnyURI, String, NormalizedString)

# Unfortunately, Union does not accept a tuple of Types.
AnyXSDType = Union[
    Duration, DateTime, Date, Time, GYearMonth, GYear, GMonthDay, GMonth, GDay, Boolean, Base64Binary,
    HexBinary, Float, Double, Decimal, Integer, Long, Int, Short, Byte, NonPositiveInteger, NegativeInteger,
    NonNegativeInteger, PositiveInteger, UnsignedLong, UnsignedInt, UnsignedShort, UnsignedByte, AnyURI, String,
    NormalizedString]


XSD_TYPE_NAMES: Dict[Type[AnyXSDType], str] = {
    Duration: "duration",
    DateTime: "dateTime",
    Date: "date",
    Time: "time",
    GYearMonth: "gYearMonth",
    GYear: "gYear",
    GMonthDay: "gMonthDay",
    GMonth: "gMonth",
    GDay: "gDay",
    Boolean: "boolean",
    Base64Binary: "base64Binary",
    HexBinary: "heyBinary",
    Float: "float",
    Double: "double",
    Decimal: "decimal",
    Integer: "integer",
    Long: "long",
    Int: "int",
    Short: "short",
    Byte: "byte",
    NonPositiveInteger: "nonPositiveInteger",
    NegativeInteger: "negativeInteger",
    NonNegativeInteger: "nonNegativeInteger",
    PositiveInteger: "positiveInteger",
    UnsignedLong: "unsignedLong",
    UnsignedShort: "unsignedShort",
    UnsignedInt: "unsignedByte",
    AnyURI: "anyURI",
    String: "string",
    NormalizedString: "normalizedString",
}
XSD_TYPE_CLASSES: Dict[str, Type[AnyXSDType]] = {v: k for k, v in XSD_TYPE_NAMES.items()}


def trivial_cast(value, type_: Type[AnyXSDType]) -> AnyXSDType:  # workaround. We should be able to use a TypeVar here
    for baseclass in (int, float, str, bytes):
        if isinstance(value, baseclass) and issubclass(type_, baseclass):
            return type_(value)  # type: ignore
    raise TypeError("{} cannot be trivially casted into {}".format(value, type_.__name__))


def xsd_repr(value: AnyXSDType) -> str:
    if isinstance(value, (DateTime, Date, Time)):
        # TODO fix trailing zeros of seconds fraction (XSD:
        #  "The fractional second string, if present, must not end in '0'")
        return value.isoformat()
    elif isinstance(value, GYearMonth):
        return "{:02d}-{:02d}".format(*value)
    elif isinstance(value, GYear):
        return "{:04d}".format(value)
    elif isinstance(value, GMonthDay):
        return "--{:02d}-{:02d}".format(*value)
    elif isinstance(value, GDay):
        return "---{:02d}".format(value)
    elif isinstance(value, GMonth):
        return "--{:04d}".format(value)
    elif isinstance(value, Boolean):
        return "true" if value else "false"
    elif isinstance(value, Base64Binary):
        return base64.b64encode(value).decode()
    elif isinstance(value, HexBinary):
        return value.hex()
    elif isinstance(value, str):
        return value
    elif isinstance(value, float):
        return repr(value).translate({0x65: 'E', 0x66: 'F', 0x69: 'I', 0x6e: 'N'})
    else:
        return str(value)


def from_xsd(value: str, type_: Type[AnyXSDType]) -> AnyXSDType:  # workaround. We should be able to use a TypeVar here
    if issubclass(type_, (int, float, str)):
        return type_(value)
    elif type_ is Duration:
        return _parse_xsd_duration(value)
    elif type_ is DateTime:
        return _parse_xsd_datetime(value)
    elif type_ is Date:
        return _parse_xsd_date(value)
    elif type_ is Time:
        return _parse_xsd_time(value)
    elif type_ in {Base64Binary, HexBinary}:
        return type_(base64.b64decode(value.encode()))  # type: ignore
    elif type_ is Boolean:
        return _parse_xsd_bool(value)
    elif type_ in {GYearMonth, GYear, GMonth, GMonthDay, GDay}:
        # TODO
        raise NotImplementedError()
    raise ValueError("{} is not a valid simple built-in XSD type".format(type_.__name__))


DATETIME_RE = re.compile(r'^-?(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?([+\-](\d\d):(\d\d)|Z)?$')
TIME_RE = re.compile(r'^(\d\d):(\d\d):(\d\d)(\.\d+)?([+\-](\d\d):(\d\d)|Z)?$')
DATE_RE = re.compile(r'^-?(\d\d\d\d)-(\d\d)-(\d\d)([+\-](\d\d):(\d\d)|Z)?$')


def _parse_xsd_duration(value: str) -> Duration:
    # TODO
    raise NotImplementedError()


def _parse_xsd_date(value: str) -> Date:
    # TODO
    raise NotImplementedError()


def _parse_xsd_datetime(value: str) -> DateTime:
    match = DATETIME_RE.match(value)
    if not match:
        raise ValueError("Value is not a valid XSD datetime string")
    microseconds = int(float(match[7]) * 1e6) if match[7] else 0
    tzinfo = datetime.timezone.utc if match[8] == 'Z' else (
        datetime.timezone(datetime.timedelta(hours=int(match[9]), minutes=int(match[10]))
                          * (-1 if match[8][0] == '-' else 1))
        if match[8] else None)
    return DateTime(int(match[1]), int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6]),
                    microseconds, tzinfo)


def _parse_xsd_time(value: str) -> Time:
    match = TIME_RE.match(value)
    if not match:
        raise ValueError("Value is not a valid XSD datetime string")
    microseconds = int(float(match[4]) * 1e6) if match[4] else 0
    tzinfo = datetime.timezone.utc if match[5] == 'Z' else (
        datetime.timezone(datetime.timedelta(hours=int(match[6]), minutes=int(match[7]))
                          * (-1 if match[5][0] == '-' else 1))
        if match[8] else None)
    return Time(int(match[1]), int(match[2]), int(match[3]), microseconds, tzinfo)


def _parse_xsd_bool(value: str) -> Boolean:
    if value in {"1", "true"}:
        return True
    elif value in {"0", "false"}:
        return False
    else:
        raise ValueError("Invalid literal for XSD bool type")
