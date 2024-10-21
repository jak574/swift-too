"""
This module contains the definition of various schemas used in the ACROSS API client.

The schemas define the structure and validation rules for different data objects used in the client.
These schemas are used for data serialization, deserialization, and validation.

The module includes the following schemas:
- BaseSchema: Base schema for all other schemas.
- CoordSchema: Schema that defines basic RA/Dec coordinates.
- PositionSchema: Schema that defines position with error.
- OptionalCoordSchema: Schema that defines optional RA/Dec coordinates.
- DateRangeSchema: Schema that defines date range.
- OptionalDateRangeSchema: Schema that defines optional date range.
- UserSchema: Schema for username and API key.
- JobInfo: Schema for ACROSS API Job status.
- VisWindow: Schema for visibility window.
- VisibilitySchema: Schema for visibility entries.
- VisibilityGetSchema: Schema for getting visibility.
- TLEEntry: Schema for TLE entry.
- TLESchema: Schema for TLE.
- SAAEntry: Schema for SAA passage.
- SAASchema: Schema for SAA entries.
- SAAGetSchema: Schema for getting SAA entries.
- PointBase: Schema for spacecraft pointing.
- PointingSchemaBase: Schema for pointing entries.
- PointingGetSchemaBase: Schema for getting pointing entries.
- PlanEntryBase: Schema for plan entry.
- PlanGetSchemaBase: Schema for getting plan entries.
- PlanSchemaBase: Schema for plan entries.
- EphemSchema: Schema for ephemeris entries.
- EphemGetSchema: Schema for getting ephemeris entries.
- MissionSchema: Schema for mission information.
- FOVSchema: Schema for field of view.
- InstrumentSchema: Schema for instrument information.
- EphemConfigSchema: Schema for ephemeris configuration.
- VisibilityConfigSchema: Schema for visibility configuration.
- TLEConfigSchema: Schema for TLE configuration.
- ConfigSchema: Schema for configuration.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

import astropy.units as u  # type: ignore
import numpy as np
from astropy.constants import c, h  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)
from pydantic_core import Url

from ..functions import convert_to_dt, coord_convert  # type: ignore
from .classrepr import TOOAPIRepresentation


class BaseSchema(BaseModel, TOOAPIRepresentation):
    """Base schema for all other schemas"""

    model_config = ConfigDict(from_attributes=True)

    @property
    def _table(self):
        """Get the table representation of the schema"""
        header = self.model_fields.keys()
        return list(header), [list(self.model_dump().values())]


class CoordSchema(BaseSchema):
    """Schema that defines basic RA/Dec"""

    ra: float = Field(ge=0, lt=360)
    dec: float = Field(ge=-90, le=90)

    @model_validator(mode="before")
    @classmethod
    def convert_coord(cls, data: Any) -> Any:
        """Convert the coordinate data to a specific format"""
        if isinstance(data, dict):
            for key in data.keys():
                if key == "ra" or key == "dec":
                    data[key] = coord_convert(data[key])
        else:
            data.ra = coord_convert(data.ra)
            data.dec = coord_convert(data.dec)
        return data

    @property
    def skycoord(self) -> SkyCoord:
        """Get the SkyCoord representation of the coordinates"""
        return SkyCoord(self.ra, self.dec, unit="deg")


class PositionSchema(CoordSchema):
    """Schema that defines position with error"""

    error: Optional[float] = None


class OptionalCoordSchema(BaseSchema):
    """Schema that defines optional RA/Dec"""

    ra: Optional[float] = Field(ge=0, lt=360, default=None)
    dec: Optional[float] = Field(ge=-90, le=90, default=None)

    @model_validator(mode="before")
    @classmethod
    def coord_convert(cls, data: Any) -> Any:
        """Convert the coordinate data to a specific format"""
        if isinstance(data, dict):
            for key in data.keys():
                if key == "ra" or key == "dec":
                    data[key] = coord_convert(data[key])
        elif hasattr(data, "ra") and hasattr(data, "dec"):
            data.ra = coord_convert(data.ra)
            data.dec = coord_convert(data.dec)
        return data

    @model_validator(mode="after")
    @classmethod
    def check_ra_dec(cls, data: Any) -> Any:
        """Check if RA and Dec are both set or both not set"""
        if data.ra is None or data.dec is None:
            assert data.ra == data.dec, "RA/Dec should both be set, or both not set"
        return data

    @property
    def skycoord(self) -> Optional[SkyCoord]:
        """Get the SkyCoord representation of the coordinates"""
        if self.ra is not None and self.dec is not None:
            return SkyCoord(self.ra, self.dec, unit="deg")
        return None


class DateRangeSchema(BaseSchema):
    """Schema that defines optional date range"""

    begin: datetime
    end: datetime
    length: Optional[float] = Field(None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def check_dates(cls, data: Any) -> Any:
        # If end or begin is None, check if length exists and add or subtract
        # from begin or end
        if isinstance(data, dict):
            if "begin" in data:
                data["begin"] = convert_to_dt(data["begin"])
            if "end" in data:
                data["end"] = convert_to_dt(data["end"])
            if "length" in data and "end" in data and "begin" not in data:
                data["begin"] = data["end"] - timedelta(days=data["length"])
            elif "end" not in data and "begin" in data and "length" in data:
                data["end"] = data["begin"] + timedelta(days=data["length"])

            # Check assertions
            assert "begin" in data and "end" in data, "Begin and end required"
            assert (
                data["begin"] is not None and data["end"] is not None
            ), "Begin and end required"

            # Calculate length
            data["length"] = (data["end"] - data["begin"]).total_seconds() / 86400
        else:
            data.begin = convert_to_dt(data["begin"])
            data["end"] = convert_to_dt(data["end"])
            if data.begin is None and data.end is not None and data.length is not None:
                data.begin = convert_to_dt(data.end) - timedelta(days=data.length)
            elif (
                data.end is None and data.begin is not None and data.length is not None
            ):
                data.end = convert_to_dt(data.begin) + timedelta(days=data.length)
            assert (
                data.begin is not None and data.end is not None
            ), "Begin and end required"
            data.begin = convert_to_dt(data.begin)
            data.end = convert_to_dt(data.end)
            data.length = (data.end - data.begin).total_seconds() / 86400
        return data

    @field_serializer("begin")
    def serialize_begin(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None and self.length is not None and self.end is not None:
            return convert_to_dt(self.end) - timedelta(days=self.length)
        return convert_to_dt(value)

    @field_serializer("end")
    def serialize_end(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None and self.length is not None and self.begin is not None:
            return convert_to_dt(self.begin) + timedelta(days=self.length)
        return convert_to_dt(value)


class OptionalDateRangeSchema(BaseSchema):
    """Schema that defines optional date range"""

    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    length: Optional[float] = Field(None, include=False)

    @model_validator(mode="before")
    @classmethod
    def check_dates(cls, data: Any) -> Any:
        # If end or begin is None, check if length exists and add or subtract
        # from begin or end
        if isinstance(data, dict):
            if "length" in data and "end" in data and "begin" not in data:
                data["begin"] = convert_to_dt(data["end"]) - timedelta(
                    days=data["length"]
                )
            elif "end" not in data and "begin" in data and "length" in data:
                data["end"] = convert_to_dt(data["begin"]) + timedelta(
                    days=data["length"]
                )
        else:
            if data.begin is None and data.end is not None and data.length is not None:
                data.begin = convert_to_dt(data.end) - timedelta(days=data.length)
            elif (
                data.end is None and data.begin is not None and data.length is not None
            ):
                data.end = convert_to_dt(data.begin) + timedelta(days=data.length)
        return data

    @field_serializer("begin")
    def serialize_begin(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None and self.length is not None and self.end is not None:
            return convert_to_dt(self.end) - timedelta(days=self.length)
        return convert_to_dt(value)

    @field_serializer("end")
    def serialize_end(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None and self.length is not None and self.begin is not None:
            return convert_to_dt(self.begin) + timedelta(days=self.length)
        return convert_to_dt(value)


class UserSchema(BaseSchema):
    """Schema for username and API key"""

    username: str
    api_key: str


class VisWindow(DateRangeSchema):
    """Schema for visibility window"""

    initial: str
    final: str

    @property
    def _table(self):
        header = ["Begin", "End", "Length (s)"]
        return header, [[self.begin, self.end, self.length]]

    def __getitem__(self, i):
        if i == 0:
            return self.begin
        elif i == 1:
            return self.end
        else:
            raise IndexError("Index out of range")


class VisibilitySchema(BaseSchema):
    """Schema for visibility entries"""

    entries: List[VisWindow]


class VisibilityGetSchema(CoordSchema, DateRangeSchema):
    """Schema for getting visibility"""

    hires: Optional[bool] = True


class TLEEntry(BaseSchema):
    """Schema for TLE entry"""

    tle1: str = Field(min_length=69, max_length=69)
    tle2: str = Field(min_length=69, max_length=69)

    @computed_field  # type: ignore
    @property
    def epoch(self) -> datetime:
        """Calculate the epoch of the TLE"""
        tleepoch = self.tle1.split()[3]
        year, dayofyear = int(f"20{tleepoch[0:2]}"), float(tleepoch[2:])
        fracday, dayofyear = np.modf(dayofyear)
        epoch = datetime.fromordinal(
            datetime(year, 1, 1).toordinal() + int(dayofyear) - 1
        ) + timedelta(days=fracday)
        return epoch


class TLESchema(BaseSchema):
    """Schema for TLE"""

    tle: TLEEntry


class SAAEntry(DateRangeSchema):
    """Schema for SAA passage"""

    ...


class SAASchema(BaseSchema):
    """Schema for SAA entries"""

    entries: List[SAAEntry]


class SAAGetSchema(DateRangeSchema):
    """Schema for getting SAA entries"""


class PointingSchema(CoordSchema):
    roll: float


class PointBase(BaseSchema):
    """Schema for spacecraft pointing"""

    time: datetime
    ra: Optional[float] = None
    dec: Optional[float] = None
    roll: Optional[float] = None
    observing: bool
    infov: Optional[bool] = None


class PointingSchemaBase(BaseSchema):
    """Schema for pointing entries"""

    entries: List[PointBase]


class PointingGetSchemaBase(DateRangeSchema):
    """Schema for getting pointing entries"""

    stepsize: int = 60


class PlanEntryBase(DateRangeSchema, CoordSchema):
    """Schema for plan entry"""

    targname: str
    exposure: int


class PlanGetSchema(OptionalDateRangeSchema, OptionalCoordSchema):
    """Schema for getting plan entries"""

    obsid: Union[str, int, None] = None
    radius: Optional[float] = None


class PlanSchemaBase(BaseSchema):
    """Schema for plan entries"""

    entries: List[PlanEntryBase]


class TargetIdSegment(BaseSchema):
    """Schema for target ID segment"""

    targetid: int
    seg: int

    @computed_field
    def obsid(self) -> str:
        return f"{self.targetid:08d}{self.seg:03d}"

    @property
    def obsidsc(self) -> int:
        return self.targetid + (self.seg << 24)


class EphemSchema(BaseSchema):
    """Schema for ephemeris entries"""

    timestamp: List[datetime] = []
    posvec: List[List[float]]
    earthsize: List[float]
    polevec: Optional[List[List[float]]] = None
    velvec: Optional[List[List[float]]] = None
    sun: List[List[float]]
    moon: List[List[float]]
    latitude: List[float]
    longitude: List[float]
    stepsize: int = 60


class EphemGetSchema(DateRangeSchema):
    """Schema for getting ephemeris entries"""

    stepsize: int = 60


class MissionSchema(BaseSchema):
    """Schema for mission information"""

    name: str
    shortname: str
    agency: str
    type: str
    pi: str
    description: str
    website: Url


class FOVSchema(BaseSchema):
    """Schema for field of view"""

    fovtype: str
    fovarea: float  # degrees**2
    fovparam: Union[str, float, None]
    fovfile: Optional[str] = None


class InstrumentSchema(BaseSchema):
    """Schema for instrument information"""

    name: str
    shortname: str
    description: str
    website: Url
    energy_low: float
    energy_high: float
    fov: FOVSchema

    @property
    def frequency_high(self):
        """Get the high frequency of the instrument"""
        return ((self.energy_high * u.keV) / h).to(u.Hz)  # type: ignore

    @property
    def frequency_low(self):
        """Get the low frequency of the instrument"""
        return ((self.energy_low * u.keV) / h).to(u.Hz)  # type: ignore

    @property
    def wavelength_high(self):
        """Get the high wavelength of the instrument"""
        return c / self.frequency_low.to(u.nm)

    @property
    def wavelength_low(self):
        """Get the low wavelength of the instrument"""
        return c / self.frequency_high.to(u.nm)


class EphemConfigSchema(BaseSchema):
    """Schema for ephemeris configuration"""

    parallax: bool
    apparent: bool
    velocity: bool
    stepsize: int = 60


class VisibilityConfigSchema(BaseSchema):
    """Schema for visibility configuration"""

    earth_cons: bool  # Calculate Earth Constraint
    moon_cons: bool  # Calculate Moon Constraint
    sun_cons: bool  # Calculate Sun Constraint
    ram_cons: bool  # Calculate Ram Constraint
    pole_cons: bool  # Calculate Orbit Pole Constraint
    saa_cons: bool  # Calculate time in SAA as a constraint
    earthoccult: float  # How many degrees from Earth Limb can you look?
    moonoccult: float  # degrees from center of Moon
    sunoccult: float  # degrees from center of Sun
    sunextra: float  # degrees buffer used for planning purpose
    earthextra: float  # degrees buffer used for planning purpose
    moonextra: float  # degrees buffer used for planning purpose


class TLEConfigSchema(BaseSchema):
    """Schema for TLE configuration"""

    tle_bad: float
    tle_url: Optional[Url] = None
    tle_name: str
    tle_heasarc: Optional[Url] = None
    tle_celestrak: Optional[Url] = None


class ConfigSchema(BaseSchema):
    """Schema for configuration"""

    mission: MissionSchema
    instruments: List[InstrumentSchema]
    ephem: EphemConfigSchema
    visibility: VisibilityConfigSchema
    tle: TLEConfigSchema


class TOOStatus(BaseModel):
    status: str = "Accepted"
    too_id: Optional[int] = None
    jobnumber: Optional[int] = None
    errors: list = list()
    warnings: list = list()

    @property
    def num_errors(self):
        return len(self.errors)

    @property
    def num_warnings(self):
        return len(self.warnings)

    def __str__(self):
        if self.too_id:
            return f"{self.status} TOO_ID={self.too_id}"
        else:
            return self.status

    def error(self, error):
        """Add an error to the list of errors"""
        if error not in self.errors:
            self.errors.append(error)
            # Any error makes a TOO rejected
            self.status = "Rejected"

    def warning(self, warning):
        """Add a warning to the list of warnings"""
        if warning not in self.warnings:
            self.warnings.append(warning)


class VisQueryGetSchema(CoordSchema, DateRangeSchema):
    """Schema defining required parameters for GET"""

    hires: bool = False


class VisQuerySchema(BaseSchema):
    entries: List[VisWindow]
    status: TOOStatus


class SwiftResolveSchema(BaseSchema):
    ra: Optional[float] = None
    dec: Optional[float] = None
    resolver: Optional[str] = None
    status: TOOStatus


class SwiftResolveGetSchema(BaseSchema):
    name: str
