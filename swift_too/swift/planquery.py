from ..base.common import TOOAPIBaseClass
from .clock import TOOAPIClockCorrect
from .obsquery import SwiftObservation
from .schema import SwiftPlanGetSchema, SwiftPlanSchema


class PlanQuery(
    SwiftPlanSchema,
    TOOAPIBaseClass,
    TOOAPIClockCorrect,
    #    AutoResolveSchema
    #    TOOAPIDateRange,
    #    TOOAPISkyCoord,
    #    TOOAPIObsID,
    #    TOOAPIDownloadData,
    #    TOOAPIAutoResolve,
    #    TOOAPIClockCorrect,
):
    """Class to fetch Swift Pre-Planned Science Timeline (PPST) for given
    constraints. Essentially this will return what Swift was planned to observe
    and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a
    given target ID (targetid) or Observation ID (obsnum).

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
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of observations (`SwiftAFSTEntry`)
    status : TOOStatus
        Status of API request
    ppstmax: datetime
        When is the PPST valid up to
    """

    _schema = SwiftPlanSchema
    _get_schema = SwiftPlanGetSchema

    @property
    def _table(self):
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [ppt._table[1][0] for ppt in self.entries]

    @property
    def observations(self):
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obsnum] = SwiftObservation()
            _ = [self._observations[q.obsnum].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)


# Class aliases for better PEP8 compliant and future compat
PPST = PlanQuery
SwiftPPST = PlanQuery
SwiftPPST = PlanQuery
SwiftPlanQuery = PlanQuery
