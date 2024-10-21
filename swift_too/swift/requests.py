from pydantic import ValidationError

from swift_too.swift.schema import SwiftTOORequestsGetSchema, SwiftTOORequestsSchema
from ..base.common import TOOAPIBaseClass
from ..base.daterange import TOOAPIDateRange
from ..base.resolve import TOOAPIAutoResolve
from ..base.skycoord import TOOAPISkyCoord
from ..base.schema import TOOStatus


class TOORequests(TOOAPIBaseClass, TOOAPIDateRange, TOOAPISkyCoord, TOOAPIAutoResolve):
    """Class used to obtain details about previous TOO requests.

    Attributes
    ----------
    username: str
        Swift TOO API username (default 'anonymous')
    api_key: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of TOOs (`Swift_TOO_Request`)
    status : TOOStatus
        Status of API request
    detail : boolean
        Return detailed TOO information (only valid if username matches TOO)
    begin : datetime
        begin time of TOO window
    end : datetime
        end time of TOO window
    length : timedelta
        length of TOO window
    limit : int
        maximum number of TOOs to retrieve
    too_id : int
        ID number of TOO to retrieve
    year : int
        fetch a year of TOOs
    ra : float
        Right Ascension of TOO target in J2000 (decimal degrees)
    dec : float
        Declination of TOO target in J2000 (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    radius : float
        radius in degrees to search for TOOs
    """

    # Local and alias parameters
    _local_args = ["name", "skycoord", "length"]
    _schema = SwiftTOORequestsSchema
    _get_schema = SwiftTOORequestsGetSchema

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username: str
            Swift TOO API username (default 'anonymous')
        api_key: str
            TOO API shared secret (default 'anonymous')
        detail : boolean
            Return detailed TOO information (only valid if username matches TOO)
        begin : datetime
            begin time of TOO window
        end : datetime
            end time of TOO window
        length : timedelta
            length of TOO window
        limit : int
            maximum number of TOOs to retrieve
        too_id : int
            ID number of TOO to retrieve
        year : int
            fetch a year of TOOs
        ra : float
            Right Ascension of TOO target in J2000 (decimal degrees)
        dec : float
            Declination of TOO target in J2000 (decimal degrees)
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        radius : float
            radius in degrees to search for TOOs
        """
        # Parameter values
        self.username = "anonymous"
        self.year = None  # TOOs for a specific year
        # Return detailed information (only returns your TOOs)
        self.detail = None
        # Limit the number of returned TOOs. Default limit is 10.
        self.limit = None
        self.too_id = None  # Request a TOO of a specific TOO ID number
        self.ra = None  # Search on RA / Dec
        self.dec = None  # Default radius is 11.6 arc-minutes
        self.radius = None  # which is the XRT FOV.
        self.skycoord = None  # SkyCoord support in place of RA/Dec
        self.begin = None  # Date range parameters Begin
        self.end = None  # End
        self.length = None  # and length.
        self.debug = False  # Debugging flag
        self.detail = False  # Return detailed TOO information
        # Request status
        self.status = TOOStatus()

        # Results
        self.entries = list()

        # Parse argument keywords
        self._kwargs = kwargs

        # See if we pass validation from the constructor. If yes, execute the query.
        try:
            self.validate_get()
            self.get()
        except ValidationError:
            pass

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def by_id(self, too_id):
        """Return Swift_TOO_Request object for a given too_id.

        Parameters
        ----------
        too_id : id
            TOO ID number

        Returns
        -------
        Swift_TOO_Request
            TOO request matching the given too_id
        """
        return {t.too_id: t for t in self.entries}[too_id]

    @property
    def _table(self):
        table_cols = [
            "too_id",
            "source_name",
            "instrument",
            "ra",
            "dec",
            "uvot_mode_approved",
            "xrt_mode_approved",
            "timestamp",
            "username",
            "urgency",
            "date_begin",
            "date_end",
            "target_id",
        ]
        if len(self.entries) > 0:
            header = [self.entries[0]._varnames[col] for col in table_cols]
        else:
            header = []
        t = list()
        for e in self.entries:
            t.append([getattr(e, col) for col in table_cols])
        return header, t


# Backwards compatible class name aliases
Swift_TOO_Requests = TOORequests
SwiftTOORequests = TOORequests
Swift_TOORequests = TOORequests
