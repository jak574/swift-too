from typing import Any, Optional

from pydantic import Field, field_serializer, model_validator

from .common import TOOAPIBaseClass
from .schema import SwiftResolveGetSchema, SwiftResolveSchema, TOOStatus
from .skycoord import SkyCoordSchema, TOOAPISkyCoord


class Resolve(TOOAPIBaseClass, TOOAPISkyCoord):
    """SwiftResolve class

    Performs name resolution using Simbad, TNS or MARS. Simply give the name of
    the source, and it will return `ra` and `dec` in decimal degrees, or a
    astropy SkyCoord (`skycoord`).

    Attributes
    ----------
    name : str
        name of the object to have coordinates resolved.
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    ra : float
        Right Ascension of resolved target in J2000 (decimal degrees)
    dec : float
        Declination of resolved target in J2000 (decimal degrees)
    resolver : str
        Name of name resolving service used
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    status : str
        status of API request
    """

    _schema = SwiftResolveSchema
    _get_schema = SwiftResolveGetSchema

    def __init__(self, name: str):
        """
        Parameters
        ----------
        name : str
            name of the object to have coordinates resolved.
        username: str
            Swift TOO API username (default 'anonymous')
        shared_secret: str
            TOO API shared secret (default 'anonymous')
        """
        # Input parameters
        self.name = None
        self.username = "anonymous"
        # Returned parameters
        self.ra = None
        self.dec = None
        self.resolver = None
        # Initiate status class
        self.status = TOOStatus()
        # Parse argument keywords
        self._kwargs = {"name": name}

    @property
    def _table(self):
        """Displays values in class as a table"""
        if self.ra is not None:
            header = ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]
            table = [[self.name, f"{self.ra:.5f}", f"{self.dec:.5f}", self.resolver]]
            return header, table
        else:
            return [], []


class AutoResolveSchema(SkyCoordSchema):
    name: Optional[str] = Field(None)

    @model_validator(mode="after")
    @classmethod
    def resolve_name(cls, data: Any) -> Any:
        if data.name is not None and (data.ra is None or data.dec is None):
            r = Resolve(data.name)
            if r.get():
                data.ra = r.ra
                data.dec = r.dec
        return data

    @field_serializer("name")
    def serialize_name(self, value: str) -> Optional[str]:
        if value is not None and (self.ra is None or self.dec is None):
            r = Resolve(value)
            if r.get():
                self.ra = r.ra
                self.dec = r.dec
        return value


class TOOAPIAutoResolve:
    """Mixin to automatically any given `name` into RA/Dec coordinates using
    `SwiftResolve`"""

    _name: Optional[str] = None
    _source_name: Optional[str] = None
    _resolve: Optional[Resolve] = None

    @property
    def resolve(self):
        return self._resolve

    @resolve.setter
    def resolve(self, resolver):
        if type(resolver) is Resolve:
            self._resolve = resolver
        else:
            raise TypeError("Needs to be assigned a Resolve object")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, sourcename):
        self.__name_setter(sourcename)

    @property
    def source_name(self):
        return self._source_name

    @source_name.setter
    def source_name(self, sourcename):
        self.__name_setter(sourcename)

    def __name_setter(self, sourcename):
        """If you set a name, use `SwiftResolve` to retrieve it's `ra` and `dec`."""
        if self._name != sourcename:
            self._name = sourcename
            self._source_name = sourcename
            self.resolve = SwiftResolve(name=sourcename)
            self.resolve.get()
            if self.resolve.ra is not None:
                self.ra = self.resolve.ra
                self.dec = self.resolve.dec
            else:
                self.status.error("Could not resolve name.")


# Shorthand alias for class
SwiftResolve = Resolve
