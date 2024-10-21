from datetime import datetime

from ..base.common import TOOAPIBaseClass
from ..base.daterange import TOOAPIDateRange
from ..base.status import TOOStatus
from .obsid import TOOAPIObsID


class SwiftManyPointCommand(TOOAPIBaseClass, TOOAPIDateRange, TOOAPIObsID):
    api_name = "SwiftManyPointCommand"

    _parameters = ["username", "filename", "entry"]
    _attributes = [
        "begin",
        "end",
        "command",
        "obsid",
        "grbmet",
        "merit",
        "ra",
        "dec",
        "roll",
        "bat_mode",
        "xrt_mode",
        "uvot_mode",
        "executed",
        "source_name",
        "status",
    ]
    _subclasses = [TOOStatus]

    def __init__(self):
        self.begin = None
        self.end = None
        self.command = None
        self.obsid = None
        self.grbmet = None
        self.merit = None
        self.ra = None
        self.dec = None
        self.roll = None
        self.bat_mode = None
        self.xrt_mode = None
        self.uvot_mode = None
        self._executed = None
        self.source_name = None
        self.status = None
        self.filename = None
        self.entry = None

    @property
    def _table(self):
        header = [
            "Command time",
            "Command	Name",
            "ObsID",
            "RA (J2000)",
            "Dec (J2000)",
            "Roll (Degrees)",
            "Merit",
            "XRTmode",
            "UVOTmode",
            "Executed",
        ]
        tabparams = [
            "begin",
            "command",
            "obsid",
            "ra",
            "dec",
            "roll",
            "merit",
            "xrt_mode",
            "uvot_mode",
            "executed",
        ]
        return header, [[getattr(self, param) for param in tabparams]]

    @property
    def executed(self):
        if self._executed == datetime(1970, 1, 1, 0, 0) or self._executed is None:
            if self.begin < datetime.utcnow():
                if self.command == "ABORTAT" or self.command == "END":
                    return ""
                return "Failed"
            else:
                return "Pending"
        return self._executed

    @executed.setter
    def executed(self, u):
        self._executed = u

    @property
    def exposure(self):
        if self.command == "TOO":
            return (self.end - self._begin).total_seconds()
        return None


class SwiftManyPoint(TOOAPIBaseClass):
    api_name = "SwiftManyPoint"
    _parameters = ["username", "filename"]
    _attributes = [
        "year",
        "day",
        "passtime",
        "uplink",
        "number",
        "transferred",
        "entries",
        "status",
    ]
    _subclasses = [TOOStatus, SwiftManyPointCommand]

    def __init__(self, *args, **kwargs):
        self.year = None
        self.day = None
        self.passtime = None
        self._uplink = None
        self.number = None
        self.transferred = None
        self.entries = []
        self.status = None
        self.filename = None

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.entries)

    @property
    def uplink(self):
        if self._uplink == datetime(1970, 1, 1, 0, 0) or self._uplink is None:
            if self.passtime < datetime.utcnow():
                return "Failed"
            else:
                return "Pending"
        return self._uplink

    @uplink.setter
    def uplink(self, u):
        self._uplink = u

    @property
    def _table(self):
        if len(self) > 0:
            header = ["Filename"] + self[0]._table[0]
        return header, [[ent.filename] + ent._table[1][0] for ent in self.entries]

    def validate(self):
        if self.filename is not None:
            return True
        return False

    def _post_process(self):
        for i in range(len(self)):
            if self[i].command == "TOO":
                self[i].end = self[i + 1].begin

    @property
    def exposure(self):
        return {ent.obsid: ent.exposure for ent in self if ent.exposure is not None}

    @property
    def exposure_by_targetid(self):
        return {ent.targetid: ent.exposure for ent in self if ent.exposure is not None}


class SwiftTOOCommand(TOOAPIBaseClass, TOOAPIObsID):
    """Class structure used to report on results of TOO API interactions"""

    api_name = "SwiftTOOCommand"
    _parameters = ["username", "filename"]
    _attributes = [
        "type",
        "command",
        "currentat",
        "obsid",
        "ra",
        "dec",
        "roll",
        "bat_mode",
        "xrt_mode",
        "uvot_mode",
        "exposure",
        "grbmet",
        "merit",
        "passtime",
        "auto",
        "uplink",
        "transferred",
        "source_name",
        "status",
    ]
    _subclasses = [TOOStatus]

    def __init__(self, *args, **kwargs):
        self.type = None
        self.command = None
        self.currentat = None
        self.obsid = None
        self.ra = None
        self.dec = None
        self.roll = None
        self.bat_mode = None
        self.xrt_mode = None
        self.uvot_mode = None
        self.exposure = None
        self.grbmet = None
        self.merit = None
        self.passtime = None
        self.auto = None
        self._uplink = None
        self.transferred = None
        self.source_name = None
        self.status = None
        self.filename = None

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    @property
    def uplink(self):
        if self._uplink == datetime(1970, 1, 1, 0, 0):
            if self.passtime < datetime.utcnow():
                return "Failed"
            else:
                return "Pending"
        return self._uplink

    @uplink.setter
    def uplink(self, u):
        self._uplink = u

    @property
    def _table(self):
        header = [
            "Command Time",
            "Target",
            "ObsID",
            "RA (J2000)",
            "Dec (J2000)",
            "Roll (Degrees)",
            "Merit",
            "XRTmode",
            "UVOTmode",
            "Exposure",
            "Executed",
        ]
        tabparams = [
            "passtime",
            "source_name",
            "obsid",
            "ra",
            "dec",
            "roll",
            "merit",
            "xrt_mode",
            "uvot_mode",
            "exposure",
            "uplink",
        ]
        return header, [[getattr(self, param) for param in tabparams]]

    def validate(self):
        if self.filename is not None:
            return True
        return False


class SwiftTOOCommands(TOOAPIBaseClass, TOOAPIDateRange):
    api_name = "SwiftTOOCommands"
    _parameters = ["username", "begin", "end", "limit"]
    _attributes = ["status", "entries"]
    _local = ["length"]
    _subclasses = [TOOStatus, SwiftTOOCommand]

    def __init__(self, *args, **kwargs):
        self.begin = None
        self.end = None
        self.limit = None
        self.entries = []

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    @property
    def _table(self):
        if len(self) > 0:
            header = ["Filename"] + self[0]._table[0]
        return header, [[ent.filename] + ent._table[1][0] for ent in self.entries]

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        if self.begin is not None and self.end is not None or self.limit is not None:
            return True
        return False


class SwiftManyPoints(TOOAPIBaseClass, TOOAPIDateRange):
    api_name = "SwiftManyPoints"
    _parameters = ["username", "begin", "end", "limit"]
    _attributes = ["status", "entries"]
    _local = ["length"]

    _subclasses = [TOOStatus, SwiftManyPoint]

    def __init__(self, *args, **kwargs):
        self.begin = None
        self.end = None
        self.limit = None
        self.entries = []

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, i):
        return self.entries[i]

    def validate(self):
        if self.begin is not None and self.end is not None or self.limit is not None:
            return True
        return False

    def _post_process(self):
        [ent._post_process() for ent in self]


class SwiftCommands(TOOAPIBaseClass, TOOAPIDateRange):
    api_name = "SwiftCommands"
    _parameters = ["username", "begin", "end", "limit"]
    _attributes = ["status", "entries"]
    _local = ["length"]
    _subclasses = [TOOStatus, SwiftManyPoint, SwiftTOOCommand]

    def __init__(self, *args, **kwargs):
        self.begin = None
        self.end = None
        self.limit = None
        self.entries = []

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, i):
        return self.entries[i]

    def validate(self):
        if self.begin is not None and self.end is not None or self.limit is not None:
            return True
        return False

    def _post_process(self):
        [ent._post_process() for ent in self]


class SwiftTOOGroup(TOOAPIBaseClass):
    api_name = "SwiftTOOGroup"
    _attributes = ["groupname", "entries"]
    _subclasses = [SwiftTOOCommand]

    def __init__(self):
        # Internal stuff
        self.entries = list()
        self.groupname = None

    @property
    def _table(self):
        if len(self) > 0:
            header = ["Filename"] + self[0]._table[0]
        return header, [[ent.filename] + ent._table[1][0] for ent in self.entries]

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.entries)


class SwiftTOOGroups(TOOAPIBaseClass, TOOAPIDateRange):
    api_name = "SwiftTOOGroups"
    _parameters = ["username", "begin", "end", "limit"]
    _attributes = ["status", "entries"]
    _local = ["length"]
    _subclasses = [
        TOOStatus,
        SwiftManyPoint,
        SwiftTOOCommand,
        SwiftTOOGroup,
    ]

    def __init__(self, *args, **kwargs):
        self.begin = None
        self.end = None
        self.limit = None
        self.entries = []

        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        if self.begin is not None and self.end is not None or self.limit is not None:
            return True
        return False

    def _post_process(self):
        [ent._post_process() for ent in self]

    @property
    def _table(self):
        if len(self) > 0:
            header = ["Groupname"] + self[0]._table[0]
        return header, [[ent.groupname] + ent._table[1][0] for ent in self.entries]


# Shortcuts
ManyPoint = SwiftManyPoint
ManyPoints = SwiftManyPoints
TOOCommand = SwiftTOOCommand
TOOCommands = SwiftTOOCommands
Commands = SwiftCommands
TOOGroup = SwiftTOOGroup
TOOGroups = SwiftTOOGroups
