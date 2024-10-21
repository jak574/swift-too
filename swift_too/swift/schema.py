from datetime import date, datetime
from typing import Any, List, Literal, Optional, Union

from pydantic import Field, computed_field, model_validator

from ..base.resolve import AutoResolveSchema
from ..base.skycoord import SkyCoordSchema
from ..swift.instruments import XRTMODES

from ..base.schema import (
    BaseSchema,
    DateRangeSchema,
    OptionalCoordSchema,
    OptionalDateRangeSchema,
    PointingSchema,
    TargetIdSegment,
    TOOStatus,
    UserSchema,
)


class SwiftInstrumentSchema(BaseSchema):
    bat_mode: str
    xrt_mode: str
    uvot_mode: str

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def check_instruments(cls, data):
        if isinstance(data, dict):
            if isinstance(data["bat"], int):
                data["bat"] = f"0x{data['bat']:04x}"
            if isinstance(data["uvot"], int):
                data["uvot"] = f"0x{data['uvot']:04x}"
            if isinstance(data["xrt"], int):
                data["xrt"] = XRTMODES[data["xrt"]]
        return data


class SwiftInstrumentApprovedSchema(BaseSchema):
    bat_mode_approved: str = "0x0000"
    xrt_mode_approved: str = "PC"
    uvot_mode_approved: str = "0x9999"

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def check_instruments(cls, data):
        if isinstance(data, dict):
            if "bat_mode_approved" in data.keys() and isinstance(
                data["bat_mode_approved"], int
            ):
                data["bat_mode_approved"] = f"0x{data['bat_mode_approved']:04x}"
            if "uvot_mode_approved" in data.keys() and isinstance(
                data["uvot_mode_approved"], int
            ):
                data["uvot_mode_approved"] = f"0x{data['uvot_mode_approved']:04x}"
            if "xrt_mode_approved" in data.keys() and isinstance(
                data["xrt_mode_approved"], int
            ):
                data["xrt_mode_approved"] = XRTMODES[data["xrt_mode_approved"]]
        return data


class SwiftPlanEntry(
    DateRangeSchema,
    PointingSchema,
    TargetIdSegment,
    SwiftInstrumentSchema,
    SkyCoordSchema,
):
    """Class that defines a Plan Entry. Read in based on datetime."""

    target_name: Optional[str] = None
    fom: Optional[float] = None
    comment: Optional[str] = None
    timetarg: Optional[float] = None
    takodb: Optional[str] = None
    sunHA: Optional[float] = None

    @property
    def exposure(self):
        return (self.end - self.begin).seconds

    def __str__(self):
        return f"{self.begin} - {self.end} Target: {self.target_name} ({self.targetid}/{self.seg}) Exp: {self.exposure}s"

    @property
    def _table(self):
        header = ["begin", "end", "target_name", "obsid", "exposure"]
        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obsid,
                self.exposure,
            ]
        ]


class OptionalSwiftTargetIDSchema(BaseSchema):
    obsid: Optional[int] = None

    @computed_field
    def target_id(self) -> Optional[int]:
        if self.obsid is None:
            return None
        return self.obsid & 0xFFFFFF

    @computed_field
    def segment(self) -> Optional[int]:
        if self.obsid is None:
            return None
        return self.obsid >> 24


class SwiftPlanSchema(
    OptionalDateRangeSchema,
    OptionalCoordSchema,
    OptionalSwiftTargetIDSchema,
    AutoResolveSchema,
):
    radius: Optional[float] = None
    entries: list[SwiftPlanEntry] = []
    ppstmax: Optional[datetime] = None


class SwiftPlanGetSchema(
    OptionalDateRangeSchema,
    OptionalCoordSchema,
    OptionalSwiftTargetIDSchema,
    AutoResolveSchema,
):
    radius: Optional[float] = None

    # Require at least one of the values to be set for the query
    @model_validator(mode="before")  # type: ignore
    @classmethod
    def check_all_none(cls, data):
        if isinstance(data, dict):
            if any(data.values()) is False:
                raise ValueError("At least one of the query parameters must be set")
        else:
            if (
                any(
                    [getattr(data, key) for key in cls.__fields__ if hasattr(data, key)]
                )
                is False
            ):
                raise ValueError("At least one of the query parameters must be set")
        return data


class SwiftAFSTEntry(
    DateRangeSchema,
    PointingSchema,
    TargetIdSegment,
    SkyCoordSchema,
    SwiftInstrumentSchema,
):
    """Class that defines a AFST Entry. Read in based on datetime."""

    settle: Optional[datetime] = None
    obstype: Optional[str] = None
    target_name: Optional[str] = None
    comment: Optional[str] = None
    timetarget: Optional[float] = None
    timeobs: Optional[float] = None
    flag: Optional[int] = None
    mvdfwpos: Optional[int] = None
    targettype: Optional[int] = None
    sunha: Optional[float] = None
    ra_object: Optional[float] = None
    dec_object: Optional[float] = None

    # Variable names
    _varnames = {
        "begin": "Begin Time",
        "settle": "Settle Time",
        "end": "End Time",
        "ra": "RA(J2000)",
        "dec": "Dec(J200)",
        "roll": "Roll (deg)",
        "target_name": "Target Name",
        "targetid": "Target ID",
        "seg": "Segment",
        "ra_object": "Object RA(J2000)",
        "dec_object": "Object Dec(J2000)",
        "xrt": "XRT Mode",
        "uvot": "UVOT Mode",
        "bat": "BAT Mode",
        "fom": "Figure of Merit",
        "obstype": "Observation Type",
        "obsid": "Observation ID",
        "exposure": "Exposure (s)",
        "slewtime": "Slewtime (s)",
    }

    @property
    def slewtime(self):
        return (self.settle - self.begin).seconds

    @property
    def exposure(self):
        return (self.end - self.settle).seconds

    def __str__(self):
        return f"{self.begin} - {self.end} Target: {self.target_name} ({self.targetid}/{self.seg}) Exp: {self.exposure}s Slewtime: {self.slewtime}s"

    @property
    def _table(self):
        parameters = [
            "begin",
            "end",
            "target_name",
            "obsid",
            "exposure",
            "slewtime",
        ]
        header = [self._varnames[row] for row in parameters]
        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obsid,
                self.exposure,
                self.slewtime,
            ]
        ]


class SwiftAFSTSchema(BaseSchema):
    entries: list[SwiftAFSTEntry]
    afstmax: Optional[datetime] = None
    status: TOOStatus


class OptionalRadiusSchema(BaseSchema):
    radius: Optional[float] = None


class SwiftAFSTGetSchema(
    OptionalDateRangeSchema, OptionalCoordSchema, OptionalRadiusSchema
):
    targetid: Optional[int] = None
    obsid: Optional[int] = None

    # Require at least one of the values to be set for the query
    @model_validator(mode="before")  # type: ignore
    @classmethod
    def check_all_none(cls, data):
        if isinstance(data, dict):
            if any(data.values()) is False:
                raise ValueError("At least one of the query parameters must be set")
        else:
            print(f"It's a {type(data)}")
            if (
                any(
                    [getattr(data, key) for key in cls.__fields__ if hasattr(data, key)]
                )
                is False
            ):
                raise ValueError("At least one of the query parameters must be set")
        return data


class SwiftSAAEntry(DateRangeSchema):
    """Simple class to hold a single SAA passage"""

    _varnames = {"begin": "Begin", "end": "End"}

    @property
    def _table(self):
        header = [self._varnames["begin"], self._varnames["end"]]
        data = [[self.begin, self.end]]
        return header, data


class SwiftSAASchema(BaseSchema):
    entries: List[SwiftSAAEntry]
    status: TOOStatus


class SwiftSAAGetSchema(DateRangeSchema):
    bat: bool = False
    hires: bool = False


class SwiftGUANOGTI(DateRangeSchema):
    exposure: Optional[float] = None
    utcf: float
    acs: str
    filename: Union[str, list]


class SwiftGUANOData(BaseSchema):
    target_time: Optional[datetime] = None
    obsid: Optional[int] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    exposure: Optional[float] = None
    filenames: Optional[List[str]] = None
    gti: Optional[SwiftGUANOGTI] = None
    all_gtis: List[SwiftGUANOGTI] = []
    acs: Optional[str] = None

    @property
    def subthresh(self):
        """Is this data subthreshold? I.e. located in the 'BAT Data for
        Subthreshold Triggers' directory of SDC, as opposed to being associated
        with the target ID."""
        if self.filenames is None:
            return None
        if len(self.filenames) == 1 and "ms" in self.filenames[0]:
            return True
        else:
            return False


class SwiftGUANOEntry(BaseSchema):
    id: Optional[int] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    target_type: Optional[str] = None
    target_time: Optional[datetime] = None
    offset: Optional[float] = None
    duration: Optional[float] = None
    quadsaway: Optional[int] = None
    exectime: Optional[datetime] = None
    obsid: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    data: SwiftGUANOData = SwiftGUANOData()
    uplinked: Optional[datetime] = Field(None, alias="uplink")
    brbd_filename: Optional[str] = None
    brbd_commandnum: Optional[int] = None

    @property
    def _table(self):
        table = []
        for row in self.model_fields:
            value = getattr(self, row)
            if row == "data" and self.data.exposure is not None:
                table += [[row, f"{value.exposure:.1f}s of BAT event data"]]
            elif row == "data" and self.data.exposure is None:
                table += [[row, "No BAT event data found"]]
            elif value is not None:
                table += [[row, f"{value}"]]
        return ["Parameter", "Value"], table


class SwiftGUANOSchema(BaseSchema):
    entries: List[SwiftGUANOEntry] = []
    guanostatus: Optional[bool] = None
    lastcommand: Optional[datetime] = None
    status: TOOStatus


class SwiftGUANOGetSchema(BaseSchema):
    username: Optional[str] = None
    subthreshold: bool = False
    successful: bool = False
    target_time: Optional[datetime] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None


class SwiftTOOSchema(SwiftInstrumentApprovedSchema):
    id: Optional[int] = None
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    ra: Optional[float] = Field(None, ge=0, le=360)
    dec: Optional[float] = Field(None, ge=-90, le=90)
    instrument: Optional[str] = None
    obs_type: Optional[str] = None
    urgency: Optional[int] = Field(None, ge=0, le=5)
    opt_mag: Union[float, str, None] = None
    opt_filt: Optional[str] = None
    xrt_countrate: Optional[str] = None
    bat_countrate: Optional[str] = None
    other_brightness: Optional[str] = None
    detector: Optional[str] = None
    grb_detector: Optional[str] = None
    grb_target_time: Optional[datetime] = None
    redshift_val: Optional[float] = None
    redshift_status: Optional[str] = None
    uvot_mode: Optional[str] = None
    uvot_exposure: Optional[float] = None
    science_just: Optional[str] = None
    visibility_sum: Optional[float] = None
    fot_comment: Optional[str] = None
    decision: Optional[str] = None
    exposure: Optional[float] = None
    proposal: bool = False
    observed: Optional[str] = None
    target_id: Optional[int] = None
    epoch: Optional[str] = None
    proposal_id: Optional[int] = None
    tcrit_met: Optional[int] = None
    proposal_trigger_just: Optional[str] = None
    emailed: Optional[int] = None
    time_on_target: Optional[float] = None
    proposal_pi: Optional[str] = None
    done: Optional[int] = None
    priority: Optional[int] = None
    poserr: Optional[float] = None
    uvot_just: Optional[str] = None
    exp_time_just: Optional[str] = None
    exp_time_per_visit: Optional[float] = None
    num_of_visits: Optional[int] = None
    monitoring_freq: Optional[str] = None
    xrt_mode: Optional[int] = None
    #    xrt_mode_approved: Optional[int] = None
    xrt_mode_comment: Optional[str] = None
    #    uvot_mode_approved: Optional[int] = None
    uvot_mode_comment: Optional[str] = None
    exp_time_per_visit_approved: Optional[float] = None
    num_of_visits_approved: Optional[int] = None
    total_exp_time_approved: Optional[float] = None
    monitoring_freq_approved: Optional[str] = None
    ods_comments: Optional[str] = None
    obs_comment: Optional[str] = None
    obs_end: Optional[date] = None
    first_seg: Optional[int] = None
    obs_n: Optional[str] = None
    fom: Optional[str] = None
    obs_begin: Optional[date] = None
    monitoring_freq_n_approved: Optional[float] = None
    monitoring_freq_base_approved: Optional[str] = None
    expo_since_too: Optional[float] = None
    slewinplace: Optional[int] = None
    date_begin: Optional[date] = None
    date_end: Optional[date] = None
    sip_uvot_mode_approved: Union[int, str, None] = None
    sip_target_id: Optional[int] = None
    sip_ssmin: Optional[float] = None
    sip_roll: Optional[float] = None
    immediate_objective: Optional[str] = None
    #    bat_mode_approved: Optional[int] = None
    decision_date: Optional[datetime] = None
    tiling: bool = False
    number_of_tiles: Optional[str] = Field(None, alias="tiling_type")
    exposure_time_per_tile: Optional[float] = None
    tiling_justification: Optional[str] = None
    tiling_approved: Optional[bool] = None
    tiling_type_approved: Optional[str] = None
    exposure_time_per_tile_approved: Optional[float] = None
    tiling_comments: Optional[str] = None
    debug: bool = False

    # English Descriptions of all the variables
    _varnames = {
        "decision": "Decision",
        "done": "Done",
        "date_begin": "Begin date",
        "date_end": "End date",
        "calendar": "Calendar",
        "slew_in_place": "Slew in Place",
        "grb_target_time": "GRB Trigger Time (UT)",
        "exp_time_per_visit_approved": "Exposure Time per Visit (s)",
        "total_exp_time_approved": "Total Exposure (s)",
        "num_of_visits_approved": "Number of Visits",
        "l_name": "Requester",
        "username": "Requester",
        "too_id": "ToO ID",
        "timestamp": "Time Submitted",
        "target_id": "Primary Target ID",
        "sourceinfo": "Object Information",
        "ra": "Right Ascenscion (J2000)",
        "dec": "Declination (J2000)",
        "source_name": "Object Name",
        "resolve": "Resolve coordinates",
        "position_err": "Position Error",
        "poserr": "Position Error (90% confidence - arcminutes)",
        "obs_type": "What is Driving the Exposure Time?",
        "source_type": "Type or Classification",
        "tiling": "Tiling",
        "immediate_objective": "Immediate Objective",
        "proposal": "GI Program",
        "proposal_details": "GI Proposal Details",
        "instrument": "Instrument",
        "tiling_type": "Tiling Type",
        "number_of_tiles": "Number of Tiles",
        "exposure_time_per_tile": "Exposure Time per Tile",
        "tiling_justification": "Tiling Justification",
        "instruments": "Instrument Most Critical to your Science Goals",
        "urgency": "Urgency",
        "proposal_id": "GI Proposal ID",
        "proposal_pi": "GI Proposal PI",
        "proposal_trigger_just": "GI Trigger Justification",
        "source_brightness": "Object Brightness",
        "opt_mag": "Optical Magnitude",
        "opt_filt": "Optical Filter",
        "xrt_countrate": "XRT Estimated Rate (c/s)",
        "bat_countrate": "BAT Countrate (c/s)",
        "other_brightness": "Other Brightness",
        "science_just": "Science Justification",
        "monitoring": "Observation Campaign",
        "obs_n": "Observation Strategy",
        "num_of_visits": "Number of Visits",
        "exp_time_per_visit": "Exposure Time per Visit (seconds)",
        "monitoring_freq": "Monitoring Cadence",
        "monitoring_freq_approved": "Monitoring Cadence",
        "monitoring_details": "Monitoring Details",
        "exposure": "Exposure Time (seconds)",
        "exp_time_just": "Exposure Time Justification",
        "xrt_mode": "XRT Mode",
        "xrt_mode_approved": "XRT Mode (Approved)",
        "uvot_mode": "UVOT Mode",
        "uvot_mode_approved": "UVOT Mode (Approved)",
        "uvot_just": "UVOT Mode Justification",
        "trigger_date": "GRB Trigger Date (YYYY/MM/DD)",
        "trigger_time": "GRB Trigger Time (HH:MM:SS)",
        "grb_detector": "GRB Discovery Instrument",
        "grbinfo": "GRB Details",
        "debug": "Debug mode",
        "validate_only": "Validate only",
        "quiet": "Quiet mode",
    }

    @computed_field  # type: ignore[misc]
    @property
    def too_id(self) -> Optional[int]:
        return self.id


class SwiftTOORequestsSchema(BaseSchema):
    entries: List[SwiftTOOSchema]
    status: TOOStatus


class SwiftTOORequestsGetSchema(
    OptionalDateRangeSchema, OptionalCoordSchema, OptionalRadiusSchema, SkyCoordSchema
):
    username: Optional[str] = None
    limit: Optional[int] = None
    year: Optional[int] = None
    detail: bool = False
    too_id: Optional[int] = None
    debug: bool = False


class SwiftTOOGetSchema(BaseSchema):
    id: int


class SwiftTOODeleteSchema(UserSchema):
    id: int


class SwiftTOOPutSchema(SwiftTOOSchema): ...


class SwiftTOOPostSchema(BaseSchema):
    source_name: str = Field(description="Source Name")
    source_type: str = Field(description="Source Type")
    ra: float = Field(description="Right Ascension (degrees)", ge=0, le=360)
    dec: float = Field(description="Declination (degrees)", ge=-90, le=90)
    instrument: Literal["XRT", "UVOT", "BAT"] = Field(
        "XRT", description="Primary Instrument"
    )
    obs_type: Literal["Spectroscopy", "Light Curve", "Position", "Timing"] = Field(
        ..., description="Observation Type"
    )
    urgency: int = Field(3, description="TOO Urgency", ge=0, le=4)
    # Optical brightness
    opt_mag: Union[float, str, None] = Field(None, description="Optical Magnitude")
    opt_filt: Optional[str] = Field(None, description="Optical Filter")
    xrt_countrate: Optional[str] = Field(None, description="XRT Count Rate")
    bat_countrate: Optional[str] = Field(None, description="BAT Count Rate")
    other_brightness: Optional[str] = Field(None, description="Other Brightness")

    @model_validator(mode="after")
    @classmethod
    def check_brightness(cls, data: Any) -> Any:
        if (
            (data.opt_mag is None or data.opt_filt is None)
            and data.xrt_countrate is None
            and data.bat_countrate is None
            and data.other_brightness is None
        ):
            raise ValueError(
                "Must specify at least one brightness value. If specifying optical brightness, ensure filter is set."
            )
        return data

    #    detector: Optional[str] = Field(None, description="Detector")
    grb_detector: Optional[str] = Field(None, description="GRB Detector")
    grb_target_time: Optional[datetime] = Field(None, description="GRB Trigger Time")

    @model_validator(mode="after")
    @classmethod
    def check_grb_target_time(cls, data: Any) -> Any:
        if data.source_type == "GRB" and (
            data.grb_target_time is None or data.grb_detector is None
        ):
            raise ValueError(
                "Must specify GRB trigger time and detector if source type is GRB.",
            )
        return data

    redshift_val: Optional[float] = Field(None, description="Redshift Value")
    redshift_status: Optional[str] = Field(None, description="Redshift Status")
    uvot_mode: str = Field("0x9999", description="UVOT Mode")
    science_just: str = Field(description="Science Justification")
    immediate_objective: str = Field(description="Immediate Objective")
    exposure: float = Field(description="Exposure Time")
    # GI Proposal
    proposal: bool = Field(False, description="GI Proposal")
    proposal_id: Optional[int] = Field(None, description="Proposal ID")
    proposal_trigger_just: Optional[str] = Field(
        None, description="GI Program Trigger Criteria Justification"
    )
    proposal_pi: Optional[str] = Field(None, description="GI Proposal PI")

    @model_validator(mode="after")
    @classmethod
    def check_proposal(cls, data: Any) -> Any:
        if data.proposal is True and (
            data.proposal_id is None or data.proposal_pi is None
        ):
            raise ValueError(
                "Must specify proposal ID and PI if GI proposal.",
            )
        if data.proposal is True and data.proposal_trigger_just is None:
            raise ValueError(
                "Must specify proposal trigger justification if proposal is True.",
            )
        return data

    poserr: Optional[float] = Field(None, description="Positional Error")
    uvot_just: Optional[str] = Field(None, description="UVOT Filter Justification")

    @model_validator(mode="after")
    @classmethod
    def check_uvot_just(cls, data: Any) -> Any:
        if data.uvot_just is None and "0x9999" not in data.uvot_mode:
            raise ValueError(
                "Must specify UVOT justification if UVOT mode is not filter of the day (0x9999).",
            )
        return data

    exp_time_just: Optional[str] = Field(
        None, description="Exposure Time Justification"
    )
    exp_time_per_visit: Optional[float] = Field(
        None, description="Exposure Time per Visit"
    )
    num_of_visits: Optional[int] = Field(None, description="Number of Visits")
    monitoring_freq: Optional[str] = Field(None, description="Monitoring Frequency")

    @model_validator(mode="after")
    @classmethod
    def check_exp_time_just(cls, data: Any) -> Any:
        if data.exp_time_just is None:
            raise ValueError(
                "Must specify exposure time justification if exposure time per visit is specified.",
            )
        if data.exp_time_per_visit is None and data.num_of_visits is not None:
            raise ValueError(
                "Must specify exposure time per visit if number of visits is specified.",
            )
        if (
            data.num_of_visits is not None
            and data.num_of_visits > 1
            and data.monitoring_freq is None
        ):
            raise ValueError(
                "Must specify monitoring frequency if number of visits is greater than 1.",
            )
        return data

    xrt_mode: int = Field(7, description="XRT Mode")
    tiling: bool = Field(False, description="Tiling")
    number_of_tiles: Union[str, int, None] = Field(None, alias="tiling_type")
    exposure_time_per_tile: Optional[float] = Field(
        None, description="Exposure Time per Tile"
    )
    tiling_justification: Optional[str] = Field(
        None, description="Tiling Justification"
    )
    debug: bool = False

    @model_validator(mode="after")
    @classmethod
    def check_tiling_justification(cls, data: Any) -> Any:
        if data.tiling_justification is None and data.tiling is True:
            raise ValueError(
                "Must specify tiling justification if tiling is True.",
            )
        return data


class SwiftUVOTModeEntry(BaseSchema):
    uvot_mode: int
    filter_num: int
    min_exposure: float
    filter_pos: int
    filter_seqid: int
    image_fov: Optional[int] = Field(None, exclude=True)
    event_fov: Optional[int] = Field(None, exclude=True)
    binning: Optional[int] = None
    max_exposure: Optional[float] = None
    weight: int
    special: str
    comment: str
    filter_name: str

    def __str__(self):
        return self.filter_name

    @computed_field
    def field_of_view(self) -> Optional[int]:
        return self.image_fov if self.image_fov is not None else self.event_fov

    @computed_field
    def eventmode(self) -> bool:
        return True if self.event_fov is not None else False


class SwiftUVOTModeSchema(AutoResolveSchema):
    uvot_mode: Optional[int] = None
    entries: list[SwiftUVOTModeEntry] = []


class SwiftUVOTModeGetSchema(BaseSchema):
    uvot_mode: int
    ra: Optional[float] = None
    dec: Optional[float] = None
