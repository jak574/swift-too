from pydantic import ValidationError

from ..base.common import TOOAPIBaseClass
from ..base.daterange import TOOAPIDateRange, TOOAPITriggerTime
from ..base.schema import TOOStatus
from .clock import TOOAPIClockCorrect
from .schema import SwiftGUANOGetSchema, SwiftGUANOSchema

# class SwiftGUANOGTI(TOOAPIBaseClass, TOOAPIClockCorrect):
#     """Define GUANO event data Good Time Intervals (GTI)

#     Attributes
#     ----------
#     filename : str
#         filename of BAT event data associated with GTI
#     acs : str
#         What was the status of the Swift Attitude Control System during this
#         GTI. Options are 'slewing', 'pointing' and 'mixed'.
#     began : datetime
#         time request began processing
#     completed : datetime
#         time request finished processing
#     exposure : float
#         exposure time of GTI
#     utcf : float
#         UT Correction Factor - this encompasses correction for both the
#         inaccuracies in the Swift clock and also any leap seconds
#     """

#     api_name = "SwiftGUANO_GTI"
#     _attributes = ["begin", "end", "exposure", "utcf", "acs", "filename"]

#     def __init__(self):
#         self.filename = None
#         self.acs = None
#         self.utcf = None
#         self.exposure = None
#         self.begin = None
#         self.end = None
#         # All times UTC
#         self._isutc = True

#     def __str__(self):
#         return f"{self.begin} - {self.end} ({self.exposure})"


# class SwiftGUANOData(
#     TOOAPIBaseClass,
#     TOOAPIObsID,
#     TOOAPIClockCorrect,
#     TOOAPIDownloadData,
#     TOOAPITriggerTime,
# ):
#     """Class to hold information about GUANO data based on analysis of the BAT
#     event files that are downlinked.

#     Attributes
#     ----------
#     filenames : list
#         filenames of BAT event data associated with GUANO dump
#     acs : str
#         What was the status of the Swift Attitude Control System during this
#         GTI. Options are 'slewing', 'pointing' and 'mixed'.
#     begin : datetime
#         start time of GUANO dump
#     end : datetime
#         end time of GUANO dump
#     triggertime : datetime
#         trigger time of event that generated GUANO dump
#     gti : SwiftGUANOGTI
#         Good Time Interval (GTI) for the combined event data
#     all_gtis : list
#         list of individual GTIs. More than one GTI can exist if data is split
#         between multiple files, or if significant gaps appear in the event data
#     obsid : str
#         Observation ID associated with the GUANO data
#     completed : datetime
#         time request finished processing
#     exposure : float
#         exposure time of GTI
#     utcf : float
#         UT Correction Factor - this encompasses correction for both the
#         inaccuracies in the Swift clock and also any leap seconds
#     subthresh : boolean
#         Indicates if the BAT event data associated with this trigger is
#         located in the subthreshold triggers section of the SDC, rather
#         than being associated with normal observation data. If this is
#         true, the data can be fetched utilizing the 'subthresh = True'
#         option of SwiftData (AKA Data)
#     """

#     # API Name
#     api_name = "SwiftGUANO_Data"

#     # Core API definitions
#     _parameters = ["obsid", "triggertime"]
#     _attributes = [
#         "begin",
#         "end",
#         "exposure",
#         "filenames",
#         "gti",
#         "all_gtis",
#         "acs",
#         "utcf",
#         "subthresh",
#     ]
#     _subclasses = [SwiftGUANOGTI]

#     def __init__(self):
#         # All times UTC
#         self._isutc = True
#         # Attributes
#         self.all_gtis = None
#         self.gti = None
#         self._utcf = None
#         self.acs = None
#         self.exposure = None
#         self.filenames = None
#         self.begin = None
#         self.end = None

#     @property
#     def utcf(self):
#         if self.gti is not None:
#             return self.gti.utcf

#     @property
#     def subthresh(self):
#         """Is this data subthreshold? I.e. located in the 'BAT Data for
#         Subthreshold Triggers' directory of SDC, as opposed to being associated
#         with the target ID."""
#         if self.filenames is None:
#             return None
#         if len(self.filenames) == 1 and "ms" in self.filenames[0]:
#             return True
#         else:
#             return False


# class SwiftGUANOEntry(
#     TOOAPIBaseClass,
#     TOOAPIObsID,
#     TOOAPIClockCorrect,
#     TOOAPIDownloadData,
#     TOOAPITriggerTime,
# ):
#     """Entry for an individual BAT ring buffer dump (AKA GUANO) event.

#     Attributes
#     ----------
#     username : str
#         username for TOO API (default 'anonymous')
#     shared_secret : str
#         shared secret for TOO API (default 'anonymous')
#     triggertime : datetime
#         triggertime associated with GUANO dump
#     triggertype : str
#         trigger type (typically what mission triggered the GUANO dump)
#     offset : int
#         Number of seconds the GUANO dump is offset from triggertime
#     duration : int
#         Number of seconds dumped
#     status : str
#         status of API request
#     """

#     # API name
#     api_name = "SwiftGUANO_Entry"
#     # Core API definitions
#     _subclasses = [SwiftGUANOData]
#     _parameters = ["triggertime"]
#     _local = ["begin", "end", "shared_secret"]
#     _attributes = [
#         "triggertype",
#         "offset",
#         "duration",
#         "quadsaway",
#         "obsid",
#         "ra",
#         "dec",
#         "data",
#         "utcf",
#     ]

#     def __init__(self):
#         # All times UTC
#         self._isutc = True
#         # Attributes
#         self.triggertype = None
#         self.duration = None
#         self._quadsaway = None
#         self.offset = None
#         self.ra = None
#         self.dec = None
#         self.data = None
#         self.utcf = None
#         self.begin = None
#         self.end = None

#     # Next part handles the use of "quadsaway" to determine if a GUANO command has been uplinked to the spacecraft,
#     # and if it has been executed onboard.
#     @property
#     def quadsaway(self):
#         if self._quadsaway > 0 and self._quadsaway < 4:
#             return 0
#         return self._quadsaway

#     @quadsaway.setter
#     def quadsaway(self, qa):
#         self._quadsaway = qa

#     @property
#     def uplinked(self):
#         """Has the GUANO command been uplinked to Swift?"""
#         if self._quadsaway == 1 or self._quadsaway == 3:
#             return False
#         return True

#     @property
#     def executed(self):
#         """Has the GUANO command been executed on board Swift?"""
#         if self._quadsaway == 2 or self._quadsaway == 3:
#             return False
#         return True

#     @property
#     def _table(self):
#         table = []
#         for row in self._parameters + self._attributes:
#             value = getattr(self, row)
#             if row == "data" and self.data.exposure is not None:
#                 table += [[row, f"{value.exposure:.1f}s of BAT event data"]]
#             elif row == "data" and self.data.exposure is None:
#                 table += [[row, "No BAT event data found"]]
#             elif value is not None:
#                 table += [[row, f"{value}"]]
#         return ["Parameter", "Value"], table

#     def _calc_begin_end(self):
#         self.begin = self.triggertime + timedelta(
#             seconds=self.offset - self.duration / 2
#         )
#         self.end = self.triggertime + timedelta(seconds=self.offset + self.duration / 2)


class GUANO(TOOAPIBaseClass, TOOAPIDateRange, TOOAPIClockCorrect, TOOAPITriggerTime):
    """Query BAT ring buffer dumps of event data associated with the Gamma-Ray
    Burst Urgent Archiver for Novel Opportunities (GUANO).

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    triggertime : datetime
        triggertime to search around
    triggertype : str
        trigger type (typically what mission triggered the GUANO dump)
    begin : datetime
        start of time period to search
    end : datetime
        end of time period to search
    length : float
        length of time to search after `begin`
    limit : int
        limit number of results fetched
    entries : list
        list of GUANO dumps found given query parameters
    status : str
        status of API request
    guanostatus : boolean
        current status of guano system
    lastcommand : datetime
        when was the last GUANO command executed
    """

    _local_args = ["length"]
    _schema = SwiftGUANOSchema
    _get_schema = SwiftGUANOGetSchema

    # Attributes
    guanostatus = None
    lastcommand = None

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anony mous')
        triggertime : datetime
            triggertime to search around
        triggertype : str
            trigger type (typically what mission triggered the GUANO dump)
        begin : datetime
            start of time period to search
        end : datetime
            end of time period to search
        length : float
            length of time to search after `begin`
        limit : int
            limit number of results fetched
        """
        # Set all times in this class to UTC
        self._isutc = True

        # Login user
        self.username = "anonymous"
        self.api_key = None
        # Parameters
        self.subthreshold = False
        self.successful = True
        self.begin = None
        self.end = None
        self.length = None
        self.limit = None
        self.triggertype = None
        # Results
        self.entries = []

        # Status of query
        self.status = TOOStatus()

        # Parse argument keywords
        self._kwargs = kwargs
        try:
            self.validate_get()
            self.get()
        except ValidationError:
            pass

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if (
            self.limit is not None
            or self.begin is not None
            or self.end is not None
            or self.length is not None
            or self.triggertime is not None
            or self.triggertype is not None
        ):
            if self.subthreshold is True and self.username == "anonymous":
                self.status.error(
                    "For subthreshold triggers, username cannot be anonymous."
                )
                return False
            return True

    @property
    def _table(self):
        header = [
            "Trigger Type",
            "Trigger Time",
            "Offset (s)",
            "Window Duration (s)",
            "Observation ID",
        ]
        table = []
        for ent in self.entries:
            if ent.data.exposure is not None:
                if round(ent.duration) != round(ent.data.exposure):
                    exposure = f"{ent.duration} ({ent.data.exposure:.0f})"
                else:
                    exposure = f"{ent.duration}"
                if ent.data.gti is None:
                    exposure += "*"
            else:
                exposure = ent.duration
            if ent.obsid is not None:
                obsid = ent.obsid
            else:
                if ent.executed:
                    obsid = "Pending Data"
                elif ent.uplinked:
                    obsid = "Pending Execution"
            table.append(
                [
                    ent.triggertype,
                    ent.triggertime,
                    ent.offset,
                    exposure,
                    obsid,
                ]
            )

        return header, table

    def _post_process(self):
        """Things to do after data are fetched from the API."""
        # Calculate begin and end times for all GUANO entries
        [e._calc_begin_end() for e in self.entries]
        # Perform clock correction by default for all dates retrieved
        self.clock_correct()


# Shorthand alias names for class and for better PEP8 compliance
SwiftGUANO = GUANO
SwiftGUANO = GUANO
# GUANOData = SwiftGUANOData
# GUANOEntry = SwiftGUANOEntry
# GUANOGTI = SwiftGUANOGTI
# Backwards API compat
# SwiftGUANO_Entry = GUANOEntry
# SwiftGUANO_GTI = GUANOGTI
# SwiftGUANO_Entry = GUANOEntry
