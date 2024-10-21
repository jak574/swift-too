from tabulate import tabulate

from ..base.common import TOOAPIBaseClass
from ..base.skycoord import SkyCoordSchema
from .schema import SwiftUVOTModeEntry, SwiftUVOTModeGetSchema, SwiftUVOTModeSchema


class SwiftUVOTMode(
    SwiftUVOTModeSchema,
    TOOAPIBaseClass,
    SkyCoordSchema,
    #    TOOAPIInstruments,
):
    """Class to fetch information about a given UVOT mode. Specifically this is
    useful for understanding for a given UVOT hex mode (e.g. 0x30ed), which
    filters and configuration are used by UVOT.

    Attributes
    ----------
    uvotmode : int / str
        UVOT mode to fetch information about (can be hex string or integer)
    status : TOOStatus
        TOO API submission status
    entries : list
        entries (`UVOT_mode_entry`) in UVOT mode table
    """

    _get_schema = SwiftUVOTModeGetSchema

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def __str__(self):
        """Display UVOT mode table"""
        if (
            hasattr(self, "status")
            and self.status == "Rejected"
            and self.status.__class__.__name__ == "TOOStatus"
        ):
            return "Rejected with the following error(s): " + " ".join(
                self.status.errors
            )
        elif self.entries is not None:
            table_cols = [
                "filter_name",
                "eventmode",
                "field_of_view",
                "binning",
                "max_exposure",
                "weight",
                "comment",
            ]
            table_columns = list()
            table_columns.append(
                [
                    "Filter",
                    "Event FOV",
                    "Image FOV",
                    "Bin Size",
                    "Max. Exp. Time",
                    "Weighting",
                    "Comments",
                ]
            )
            for entry in self.entries:
                table_columns.append([getattr(entry, col) for col in table_cols])

            table = f"UVOT Mode: {self.uvotmode}\n"
            table += "The following table summarizes this mode, ordered by the filter sequence:\n"
            table += tabulate(table_columns, tablefmt="pretty")
            table += "\nFilter: The particular filter in the sequence.\n"
            table += (
                "Event FOV: The size of the FOV (in arc-minutes) for UVOT event data.\n"
            )
            table += (
                "Image FOV: The size of the FOV (in arc-minutes) for UVOT image data.\n"
            )
            table += "Max. Exp. Time: The maximum amount of time the snapshot will spend on the particular filter in the sequence.\n"
            table += "Weighting: Ratio of time spent on the particular filter in the sequence.\n"
            table += "Comments: Additional notes that may be useful to know.\n"
            return table
        else:
            return "No data"

    def _repr_html_(self):
        """Jupyter Notebook friendly display of UVOT mode table"""
        if (
            hasattr(self, "status")
            and self.status == "Rejected"
            and self.status.__class__.__name__ == "TOOStatus"
        ):
            return "<b>Rejected with the following error(s): </b>" + " ".join(
                self.status.errors
            )
        elif self.entries is not None:
            html = f"<h2>UVOT Mode: {self.uvotmode}</h2>"
            html += "<p>The following table summarizes this mode, ordered by the filter sequence:</p>"

            html += '<table id="modelist" cellpadding=4 cellspacing=0>'
            html += "<tr>"  # style="background-color:#08f; color:#fff;">'
            html += "<th>Filter</th>"
            html += "<th>Event FOV</th>"
            html += "<th>Image FOV</th>"
            html += "<th>Bin Size</th>"
            html += "<th>Max. Exp. Time</th>"
            html += "<th>Weighting</th>"
            html += "<th>Comments</th>"
            html += "</tr>"

            table_cols = [
                "filter_name",
                "eventmode",
                "field_of_view",
                "binning",
                "max_exposure",
                "weight",
                "comment",
            ]
            i = 0
            for entry in self.entries:
                if i % 2:
                    html += '<tr style="background-color:#eee;">'
                else:
                    html += '<tr">'
                for col in table_cols:
                    html += "<td>"
                    html += f"{getattr(entry,col)}"
                    html += "</td>"

                html += "</tr>"
            html += "</table>"
            html += '<p id="terms">'
            html += "<small><b>Filter: </b>The particular filter in the sequence.<br>"
            html += "<b>Event FOV: </b>The size of the FOV (in arc-minutes) for UVOT event data.<br>"
            html += "<b>Image FOV: </b>The size of the FOV (in arc-minutes) for UVOT image data.<br>"
            html += "<b>Max. Exp. Time: </b>The maximum amount of time the snapshot will spend on the particular filter in the sequence.<br>"
            html += "<b>Weighting: </b>Ratio of time spent on the particular filter in the sequence.<br>"
            html += "<b>Comments: </b>Additional notes that may be useful to know.<br></small>"
            html += "</p>"
            return html
        else:
            return "No data"


# Aliases that are more PEP8 compliant
UVOTMode = SwiftUVOTMode
UVOTModeEntry = SwiftUVOTModeEntry
# Backwards compatibility names
UVOT_mode_entry = SwiftUVOTModeEntry
UVOT_mode = SwiftUVOTMode
SwiftUVOTMode = SwiftUVOTMode
