from datetime import datetime, date, timezone
from typing import Union, Optional
from astropy.coordinates import Longitude, Latitude  # type: ignore[import]
from astropy.units import Quantity, deg  # type: ignore[import]
from dateutil import parser
import re
import warnings

# Check if we have astropy support
HAS_ASTROPY = False
try:
    from astropy.time import Time  # type: ignore[import]

    HAS_ASTROPY = True
except ImportError:
    pass


# Regex for matching date, time and datetime strings
DATE_REGEX = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1])?$"
TIME_REGEX = r"^([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
ISO8601_REGEX = r"^([\+-]?\d{4}(?!\d{2}\b))((-?)((0[1-9]|1[0-2])(\3([12]\d|0[1-9]|3[01]))?|W([0-4]\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\d|[12]\d{2}|3([0-5]\d|6[1-6])))([T\s]((([01]\d|2[0-3])((:?)[0-5]\d)?|24\:?00)([\.,]\d+(?!:))?)?(\17[0-5]\d([\.,]\d+)?)?([zZ]|([\+-])([01]\d|2[0-3]):?([0-5]\d)?)?)?)?$"
DATETIME_REGEX = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1]) ([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
FLOAT_REGEX = r"^[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?$"
INT_REGEX = r"^(0|[1-9][0-9]+)$"


def convert_to_dt(value, isutc=False, outfunc=datetime):
    """Convert various date formats to swiftdatetime or datetime

    Parameters
    ----------
    value : varies
        Value to be converted.
    isutc : bool, optional
        Is the value in UTC, by default False
    outfunc : datetime / swiftdatetime, optional
        What format should the output be? By default datetime, can be
        swiftdatetime

    Returns
    -------
    datetime / swiftdatetime
        Returned datetime / swiftdatetime object

    Raises
    ------
    TypeError
        Raised if incorrect format is given for conversion.
    """

    if isinstance(value, str):
        if re.match(DATETIME_REGEX, value):
            if "." in value:
                # Do this because "fromisoformat" is restricted to 0, 3 or 6 decimal plaaces
                dtvalue = outfunc.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            else:
                dtvalue = outfunc.strptime(value, "%Y-%m-%d %H:%M:%S")
        elif re.match(DATE_REGEX, value):
            dtvalue = outfunc.strptime(f"{value} 00:00:00", "%Y-%m-%d %H:%M:%S")
        elif re.match(ISO8601_REGEX, value):
            dtvalue = parser.parse(value)
            if dtvalue.tzinfo is None:
                warnings.warn(
                    "ISO8601 formatted dates should be supplied with timezone. ISO8601 dates with no timezone will be assumed to be localtime and then converted to UTC."
                )
            dtvalue = dtvalue.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            raise ValueError(
                "Date/time given as string should 'YYYY-MM-DD HH:MM:SS' or ISO8601 format."
            )
    elif isinstance(value, date):
        dtvalue = outfunc.strptime(f"{value} 00:00:00", "%Y-%m-%d %H:%M:%S")
    elif isinstance(value, outfunc):
        if value.tzinfo is not None:
            # Strip out timezone info and convert to UTC
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        dtvalue = value  # Just pass through un molested
    # elif (
    #     type(value) == swiftdatetime
    #     and outfunc == datetime
    #     or type(value) == datetime
    #     and outfunc == swiftdatetime
    # ):
    #     if type(value) == datetime and value.tzinfo is not None:
    #         # Strip out timezone info and convert to UTC
    #         value = value.astimezone(timezone.utc).replace(tzinfo=None)
    #     dtvalue = outfunc.fromtimestamp(value.timestamp())
    elif value is None:
        dtvalue = None
    elif HAS_ASTROPY and type(value) is Time:
        dtvalue = value.datetime
    else:
        raise TypeError(
            'Date should be given as a datetime, astropy Time, or as string of format "YYYY-MM-DD HH:MM:SS"'
        )
    # if outfunc is swiftdatetime and dtvalue.isutc != isutc:
    #     dtvalue.isutc = isutc
    return dtvalue


def coord_convert(
    coord: Union[float, int, str, Quantity, Longitude, None],
) -> Optional[float]:
    """Convert coordinates of various types either string, integer,
    astropy Longitude or astropy "deg" unit, to a float.

    Parameters
    ----------
    coord : Union[float, str, int, Quantity, Longitude, None]
        Coordinate in one of the types

    Returns
    -------
    float | None
        Coordinate expressed as a float. Just pass through a None.
    """
    if coord is None:
        return None
    if type(coord) is Quantity:
        return coord.to(deg).value
    if type(coord) is Longitude or type(coord) is Latitude:
        return coord.value
    # Universal translator
    return float(coord)


def _tablefy(table, header=None):
    """Simple HTML table generator

    Parameters
    ----------
    table : list
        Data for table
    header : list
        Headers for table, by default None

    Returns
    -------
    str
        HTML formatted table.
    """

    tab = "<table>"
    if header is not None:
        tab += "<thead>"
        tab += "".join(
            [f"<th style='text-align: left;'>{head}</th>" for head in header]
        )
        tab += "</thead>"

    for row in table:
        tab += "<tr>"
        # Replace any carriage returns with <br>
        row = [f"{col}".replace("\n", "<br>") for col in row]
        tab += "".join([f"<td style='text-align: left;'>{col}</td>" for col in row])
        tab += "</tr>"
    tab += "</table>"
    return tab
