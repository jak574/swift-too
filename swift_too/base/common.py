import re
import warnings
from datetime import date, datetime, timedelta, timezone
from pathlib import PosixPath
from typing import Any, Optional, Type

import requests
from dateutil import parser
from requests.auth import HTTPBasicAuth

from ..version import version_tuple
from .classrepr import TOOAPIRepresentation
from .schema import BaseSchema, TOOStatus

# Make Warnings a little less weird
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = (
    lambda message, category, filename, lineno, line=None: formatwarning_orig(
        message, category, filename, lineno, line=""
    )
)

# Define the API version
api_version = f"{version_tuple[0]}.{version_tuple[1]}"

# Next imports are not dependancies, but if you have them installed, we'll use
# them
try:
    import keyring

    # Check that keyring actually is set up and working
    if keyring.get_keyring().name != "fail Keyring":
        keyring_support = True
    else:
        keyring_support = False
except ImportError:
    keyring_support = False

# Check if we have astropy support
HAS_ASTROPY = False
try:
    from astropy.time import Time  # type: ignore[import]

    HAS_ASTROPY = True
except ImportError:
    pass


# Convert degrees to radians
dtor = 0.017453292519943295

# Regex for matching date, time and datetime strings
DATE_REGEX = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1])?$"
TIME_REGEX = r"^([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
ISO8601_REGEX = r"^([\+-]?\d{4}(?!\d{2}\b))((-?)((0[1-9]|1[0-2])(\3([12]\d|0[1-9]|3[01]))?|W([0-4]\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\d|[12]\d{2}|3([0-5]\d|6[1-6])))([T\s]((([01]\d|2[0-3])((:?)[0-5]\d)?|24\:?00)([\.,]\d+(?!:))?)?(\17[0-5]\d([\.,]\d+)?)?([zZ]|([\+-])([01]\d|2[0-3]):?([0-5]\d)?)?)?)?$"
DATETIME_REGEX = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1]) ([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
FLOAT_REGEX = r"^[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?$"
INT_REGEX = r"^(0|[1-9][0-9]+)$"

# Submission URL
API_URL = "https://e1-swiftweb24.swift.psu.edu/api/v1/"
API_URL = "http://localhost:8000/api/v1/"


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
    elif (
        isinstance(value, swiftdatetime)
        and outfunc == datetime
        or isinstance(value, datetime)
        and outfunc == swiftdatetime
    ):
        if isinstance(value, datetime) and value.tzinfo is not None:
            # Strip out timezone info and convert to UTC
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        dtvalue = outfunc.fromtimestamp(value.timestamp())
    elif value is None:
        dtvalue = None
    elif HAS_ASTROPY and type(value) is Time:
        dtvalue = value.datetime
    else:
        raise TypeError(
            'Date should be given as a datetime, astropy Time, or as string of format "YYYY-MM-DD HH:MM:SS"'
        )
    if outfunc is swiftdatetime and dtvalue.isutc != isutc:
        dtvalue.isutc = isutc
    return dtvalue


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


class TOOAPIBaseClass(TOOAPIRepresentation):
    """
    Base class for Swift TOO API Classes including common methods for all API classes.
    """

    # API descriptors type hints
    _schema: Type[BaseSchema]
    _get_schema: Type[BaseSchema]
    _put_schema: Type[BaseSchema]
    _post_schema: Type[BaseSchema]
    _del_schema: Type[BaseSchema]
    _local_args: list
    _kwargs: dict

    _mission: str = "Swift"

    # Authentication
    username: Optional[str] = None
    api_key: Optional[str] = None

    # Job Status information
    status: TOOStatus = TOOStatus()

    # By default all API dates are in Swift Time
    _isutc = False

    def __getitem__(self, i):
        if hasattr(self, "entries"):
            return self.entries[i]

    @property
    def api_name(self) -> str:
        """Ensure api_name is of the form MissionActivity

        Returns
        -------
        str
            API Name
        """
        return f"{self._mission}{self.__class__.__name__.replace(self._mission,'')}"

    def api_url(self, argdict) -> str:
        """
        URL for this API call.

        Returns
        -------
        str
            URL for API call
        """
        # If arguments has `id` in it, then put this in the path
        if hasattr(self, "id") and self.id is not None:
            return f"{API_URL}{self._mission.lower()}/{self.api_name.replace(self._mission,'').lower()}/{self.id}"
        return f"{API_URL}{self._mission.lower()}/{self.api_name.replace(self._mission,'').lower()}"

    @property
    def schema(self) -> Any:
        """Return pydantic schema for this API class

        Returns
        -------
        object
            Pydantic Schema
        """
        return self._schema.model_validate(self)

    @property
    def parameters(self) -> dict:
        """
        Return parameters as dict

        Returns
        -------
        dict
            Dictionary of parameters
        """
        return {k: v for k, v in self._schema.model_validate(self) if v is not None}

    @parameters.setter
    def parameters(self, params: dict):
        """
        Set API parameters from a given dict which is validated from self._schema

        Parameters
        ----------
        params : dict
            Dictionary of class parameters
        """
        for k, v in self._schema(**params):
            if hasattr(self, k) and v is not None:
                setattr(self, k, v)

    def get(self) -> bool:
        """
        Perform a 'GET' submission to Swift TOO API. Used for fetching
        information.

        Returns
        -------
        bool
            Was the get successful?

        Raises
        ------
        HTTPError
            Raised if GET doesn't return a 200 response.
        """
        if self.validate_get():
            # Check if we need to do auth
            if (
                self.username != "anonymous"
                and self.username is not None
                and self.api_key is not None
            ):
                auth = HTTPBasicAuth(self.username, self.api_key)
            else:
                auth = None

            # Create an array of parameters from the schema
            # Do the GET request
            req = requests.get(
                self.api_url(self.get_params),
                params=self.get_params,
                timeout=60,
                auth=auth,
                verify=False,
            )
            print(req.status_code, req.url)
            if req.status_code == 200:
                # Parse, validate and record values from returned API JSON
                if isinstance(self, BaseSchema):
                    for k, v in self.model_validate(req.json()):
                        setattr(self, k, v)
                else:
                    for k, v in self._schema.model_validate(req.json()):
                        setattr(self, k, v)
                return True
            elif req.status_code == 404:
                """Handle 404 errors gracefully, by issuing a warning"""
                warnings.warn(req.json()["detail"])
            else:
                # Raise an exception if the HTML response was not 200
                self.status.error(f"{req.json()['detail']}")
        return False

    def delete(self) -> bool:
        """
        Perform a 'GET' submission to Swift TOO API. Used for fetching
        information.

        Returns
        -------
        bool
            Was the get successful?

        Raises
        ------
        HTTPError
            Raised if GET doesn't return a 200 response.
        """
        if self.validate_del():
            # Create an array of parameters from the schema
            del_params = {
                key: value for key, value in self._del_schema.model_validate(self)
            }
            # Do the DELETE request
            req = requests.delete(
                self.api_url(del_params), params=del_params, timeout=60
            )
            if req.status_code == 200:
                # Parse, validate and record values from returned API JSON
                for k, v in self._schema.model_validate(req.json()):
                    setattr(self, k, v)
                return True
            else:
                # Raise an exception if the HTML response was not 200
                req.raise_for_status()
        return False

    def put(self, payload={}) -> bool:
        """
        Perform a 'PUT' submission to Swift TOO API. Used for pushing/replacing
        information.

        Returns
        -------
        bool
            Was the get successful?

        Raises
        ------
        HTTPError
            Raised if PUT doesn't return a 201 response.
        """
        if self.validate_put():
            # Other non-file parameters
            put_params = {
                key: value
                for key, value in self._put_schema.model_validate(self)
                if key != "entries"
            }

            # URL for this API call
            api_url = self.api_url(put_params)
            if "id" in put_params.keys():
                put_params.pop("id")  # Remove id from query parameters

            # Extract any entries data, and upload this as JSON
            if hasattr(self, "entries") and len(self.entries) > 0:
                jsdata = self._put_schema.model_validate(self).model_dump(
                    include={"entries"}, mode="json"
                )
            # Or else pass any specific payload
            else:
                jsdata = payload

            # Make PUT request
            req = requests.put(
                api_url,
                params=put_params,
                json=jsdata,
                timeout=60,
            )
            if req.status_code == 201:
                # Parse, validate and record values from returned API JSON
                for k, v in self._schema.model_validate(req.json()):
                    setattr(self, k, v)
                return True
            else:
                print("ERROR: ", req.status_code, req.json())
                req.raise_for_status()
        return False

    def post(self) -> bool:
        """
        Perform a 'PUT' submission to Swift TOO API. Used for pushing/replacing
        information.

        Returns
        -------
        bool
            Was the get successful?

        Raises
        ------
        HTTPError
            Raised if POST doesn't return a 201 response.
        """
        if self.validate_post():
            # Extract any files out of the arguments
            files = {
                key: (
                    # Return either the existing filelike object, or open the file
                    value.name,
                    (
                        getattr(self, key.replace("filename", "file"))
                        if hasattr(self, key.replace("filename", "file"))
                        else value.open("rb")
                    ),
                )
                for key, value in self._post_schema.model_validate(self)
                if type(value) is PosixPath
            }

            # Extract query arguments
            post_params = {
                key: value
                for key, value in self._post_schema.model_validate(self)
                if key != "entries" and type(value) is not PosixPath
            }

            # Extract any entries data, and upload this as JSON
            if hasattr(self, "entries") and len(self.entries) > 0:
                jsdata = self._post_schema.model_validate(self).model_dump(
                    include={"entries"}, mode="json"
                )
            else:
                jsdata = {}

            if files == {}:
                # If there are no files, we can upload self.entries as JSON data
                req = requests.post(
                    self.api_url(post_params),
                    params=post_params,
                    json=jsdata,
                    timeout=60,
                    verify=False,
                )
            else:
                # Otherwise we need to use multipart/form-data for files, and pass the other parameters as query parameters
                req = requests.post(
                    self.api_url(post_params),
                    params=post_params,
                    files=files,
                    timeout=60,
                    verify=False,
                )

            if req.status_code == 201:
                # Parse, validate and record values from returned API JSON
                for k, v in self._schema.model_validate(req.json()):
                    setattr(self, k, v)
                return True
            elif req.status_code == 200:
                warnings.warn(req.json()["detail"])
                return False
            else:
                # Raise an exception if the HTML response was not 200
                req.raise_for_status()
        return False

    @property
    def get_params(self) -> dict:
        return {
            key: getattr(self, key)
            for key in self._get_schema.model_fields
            if key != "id"
        }

    def validate_get(self) -> bool:
        """Validate arguments for GET

        Returns
        -------
        bool
            Do arguments validate? True | False

        Raises
        ------
        ValidationError
            If arguments don't validate
        """

        if hasattr(self, "_get_schema"):
            # Set arguments from kwargs
            if not isinstance(self, BaseSchema):
                for key in self._kwargs:
                    if (
                        key in self._get_schema.model_fields
                        or key in self._local_args
                        or key == "api_key"
                        or key == "shared_secret"
                    ):
                        # For backwards compatibility with 1.2
                        value = self._kwargs[key]
                        if key == "shared_secret":
                            key = "api_key"
                        setattr(self, key, value)
                # Validate GET parameters
                self._get_schema.model_validate(self.get_params)
            else:
                self._get_schema.model_validate(self)
        else:
            warnings.warn("GET not allowed for this class.")
            return False
        return True

    def validate_put(self) -> bool:
        """Validate if value to be PUT matches Schema

        Returns
        -------
        bool
            Is it validated? True | False

        Raises
        ------
        ValidationError
            If the value to be PUT doesn't match the Schema


        """
        if hasattr(self, "_put_schema"):
            self._put_schema.model_validate(self.__dict__)
        else:
            warnings.warn("PUT not allowed for this class.")
            return False
        return True

    def validate_post(self) -> bool:
        """Validate if value to be POST matches Schema

        Returns
        -------
        bool
            Is it validated? True | False
        """
        if hasattr(self, "_post_schema"):
            self._post_schema.model_validate(self.__dict__)
        else:
            warnings.warn("POST not allowed for this class.")
            return False
        return True

    def validate_del(self) -> bool:
        """Validate if value to be POST matches Schema

        Returns
        -------
        bool
            Is it validated? True | False
        """
        if hasattr(self, "_del_schema"):
            self._del_schema.model_validate(self.__dict__)
        else:
            warnings.warn("DELETE not allowed for this class.")
            return False
        return True


class swiftdatetime(datetime, TOOAPIBaseClass):
    """Extend datetime to store met, utcf and swifttime. Default value is UTC"""

    api_name = "swiftdatetime"
    _parameters = ["met", "utcf", "swifttime", "utctime", "isutc"]

    def __new__(self, *args, **kwargs):
        return super(swiftdatetime, self).__new__(self, *args)

    def __init__(self, *args, **kwargs):
        self._met = None
        self.utcf = None
        self._swifttime = None
        self._utctime = None
        self._isutc = False
        self._isutc_set = False
        if "tzinfo" in kwargs.keys():
            raise TypeError("swiftdatetime does not support timezone information.")
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return f"swiftdatetime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.microsecond}, isutc={self.isutc}, utcf={self.utcf})"

    def __sub__(self, other):
        """Redefined __sub__ to handle mismatched time bases"""
        if isinstance(other, swiftdatetime):
            if self.isutc != other.isutc and (
                self.utctime is None or other.utctime is None
            ):
                raise ArithmeticError(
                    "Cannot subtract mismatched time zones with no UTCF"
                )  # FIXME - correct exception?

            if (
                self.isutc is True
                and other.isutc is True
                or self.isutc is False
                and other.isutc is False
            ):
                return super().__sub__(other)
            else:
                if self.isutc:
                    return super().__sub__(other.utctime)
                else:
                    return self.utctime.__sub__(other.utctime)
        else:
            value = super().__sub__(other)
            if hasattr(value, "isutc"):
                value.isutc = self.isutc
            return value

    def __add__(self, other):
        """Custom add for swiftdatetime. Note that UTCF is not preserved, on purpose."""
        value = super().__add__(other)
        if hasattr(value, "isutc"):
            value.isutc = self.isutc
        return value

    @property
    def isutc(self):
        return self._isutc

    @isutc.setter
    def isutc(self, utc):
        """Is this swiftdatetime based on UTC or Swift Time"""
        if self._isutc_set is not True:
            # If we change the time base for this, reset the values of swifttime and utctime
            self._isutc = utc
            self.swifttime = None
            self.utctime = None
            self._isutc_set = True
        else:
            raise AttributeError("Cannot set attribute isutc when previously set.")

    @property
    def met(self):
        if self.swifttime is not None:
            return (self.swifttime - datetime(2001, 1, 1)).total_seconds()

    @met.setter
    def met(self, met):
        self._met = met

    @property
    def utctime(self):
        if self._utctime is None:
            if self.isutc:
                self._utctime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None:
                self._utctime = self.swifttime + timedelta(seconds=self.utcf)
        return self._utctime

    @utctime.setter
    def utctime(self, utc):
        if isinstance(utc, datetime):
            # Ensure that utctime set to a pure datetime
            if utc.tzinfo is not None:
                utc = utc.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            self._utctime = utc

    @property
    def swifttime(self):
        if self._swifttime is None:
            if not self.isutc:
                self._swifttime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None:
                self._swifttime = self.utctime - timedelta(seconds=self.utcf)
        return self._swifttime

    @swifttime.setter
    def swifttime(self, st):
        if isinstance(st, datetime):
            # Ensure that swifttime set to a pure datetime
            if st.tzinfo is not None:
                st = st.astimezone(timezone.utc).replace(tzinfo=None)
            self._swifttime = st
        else:
            self._swifttime = convert_to_dt(st)

    @property
    def _table(self):
        if self._isutc:
            header = [
                "MET (s)",
                "Swift Time",
                "UTC Time (default)",
                "UTCF (s)",
            ]
        else:
            header = [
                "MET (s)",
                "Swift Time (default)",
                "UTC Time",
                "UTCF (s)",
            ]
        return header, [[self.met, self.swifttime, self.utctime, self.utcf]]

    @classmethod
    def frommet(cls, met, utcf=None, isutc=False):
        """Construct a swiftdatetime from a given MET and (optional) UTCF."""
        dt = datetime(2001, 1, 1) + timedelta(seconds=met)
        if isutc and utcf is not None:
            dt += timedelta(seconds=utcf)
        ret = cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
        )
        ret.utcf = utcf
        ret.isutc = isutc
        return ret

    # Attribute aliases
    swift = swifttime
    utc = utctime
