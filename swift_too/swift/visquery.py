from ..base.common import TOOAPIBaseClass
from ..base.daterange import TOOAPIDateRange
from ..base.resolve import TOOAPIAutoResolve
from ..base.skycoord import TOOAPISkyCoord
from ..base.schema import TOOStatus
from ..base.schema import VisQuerySchema, VisQueryGetSchema
from .clock import TOOAPIClockCorrect
from pydantic import ValidationError


class VisQuery(
    TOOAPIBaseClass,
    TOOAPIDateRange,
    TOOAPISkyCoord,
    TOOAPIAutoResolve,
    TOOAPIClockCorrect,
):
    """
    Request Swift Target visibility entries. These results are low-fidelity,
    so do not give orbit-to-orbit visibility, but instead long term entries
    indicates when a target is observable by Swift and not in a Sun/Moon/Pole
    constraint.

    Attributes
    ----------
    begin : datetime
        begin time of visibility window
    end : datetime
        end time of visibility window
    length : timedelta
        length of visibility window
    ra : float
        Right Ascension of target in J2000 (decimal degrees)
    dec : float
        Declination of target in J2000 (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    hires : boolean
        Calculate visibility with high resolution, including Earth
        constraints
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    entries : list
        List of visibility entries (`Swift_VisWindow`)
    status : TOOStatus
        Status of API request
    """

    _schema = VisQuerySchema
    _get_schema = VisQueryGetSchema
    _local_args = ["length", "name", "skycoord"]

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        begin : datetime
            begin time of visibility window
        end : datetime
            end time of visibility window
        length : timedelta
            length of visibility window
        ra : float
            Right Ascension of target in J2000 (decimal degrees)
        dec : float
            Declination of target in J2000 (decimal degrees)
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        hires : boolean
            Calculate visibility with high resolution, including Earth
            constraints
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        """
        # Set all times in this class to UTC
        self._isutc = True
        # User arguments
        self.username = "anonymous"
        self.ra = None
        self.dec = None
        self.hires = None
        self.length = None
        # Visibility entries go here
        self.entries = list()
        # Status of request
        self.status = TOOStatus()
        # Parse argument keywords
        self._kwargs = kwargs
        try:
            self.validate_get()
            self.get()
        except ValidationError:
            pass

    @property
    def _table(self):
        if len(self.entries) != 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [win._table[1][0] for win in self.entries]

    # For compatibility / consistency with other classes.
    @property
    def windows(self):
        return self.entries

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)


# Shorthand alias for class
SwiftVisQuery = VisQuery
Swift_VisQuery = SwiftVisQuery
