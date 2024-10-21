from pydantic import ValidationError

from .schema import SwiftSAAGetSchema, SwiftSAASchema
from ..base.common import TOOAPIBaseClass
from ..base.daterange import TOOAPIDateRange
from ..base.schema import TOOStatus
from .clock import TOOAPIClockCorrect


# class Swift_SAAEntry(TOOAPIBaseClass, TOOAPIClockCorrect):
#     """Simple class describing the start and end time of a Swift SAA passage.
#      Attributes
#     ----------
#     begin : datetime
#         Start time of the SAA passage
#     end : datetime
#         End time of the SAA passages
#     """

#     # API details
#     api_name = "Swift_SAA_Entry"
#     # Returned values
#     _attributes = ["begin", "end"]
#     # Display names of columns
#     _varnames = {"begin": "Begin", "end": "End"}

#     def __init__(self):
#         # Attributes
#         self.begin = None
#         self.end = None
#         # Internal values
#         self._isutc = True

#     @property
#     def _table(self):
#         header = [self._header_title("begin"), self._header_title("end")]
#         data = [[self.begin, self.end]]
#         return header, data

#     @property
#     def table(self):
#         return ["begin", "end"], [[self.begin, self.end]]


class SAA(TOOAPIBaseClass, TOOAPIDateRange, TOOAPIClockCorrect):
    """Class to obtain Swift SAA passage times. Two versions are available: The
    Spacecraft definition (default) or an estimate of when the BAT SAA flag is
    up. Note that the BAT SAA flag is dynamically set based on count rate, so
    this result only returns an estimate based on when that is likely to happen.

    Attributes
    ----------
    entries : list
        Array of Swift_SAAEntry classes containing the windows.
    status : TOOStatus
        Status of API request
    """

    # API details
    _schema = SwiftSAASchema
    _get_schema = SwiftSAAGetSchema
    _local_args = ["length"]

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        begin : datetime
            Start of the period for which to fetch SAA passages
        end : datetime (optional)
            End of the period for which to fetch SAA passages
        length : int (default: 1)
            Number of days to calculate for
        bat : boolean
            If set to `True`, use BAT calculation for SAA passages, otherwise,
            use spacecraft.
        hires : boolean
            Calculate SAA with high resolution.
        """
        # Attributes
        self.begin = None
        self.end = None
        self.length = 1
        self.bat = False
        self.status = TOOStatus()
        # Returned values
        self.entries = []
        # Internal values
        self._isutc = True
        self.hires = False
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

    @property
    def _table(self):
        if self.entries is None:
            return [], []
        else:
            vals = list()
            for i in range(len(self.entries)):
                header, values = self.entries[i]._table
                vals.append([i] + values[0])
            return ["#"] + header, vals


# Alias
Swift_SAA = SAA
SwiftSAA = SAA
