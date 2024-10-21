from textwrap import TextWrapper
from tabulate import tabulate
from ..functions import _tablefy


class TOOAPIRepresentation:
    @property
    def _table(self):
        """Table of details of the class"""
        _parameters = self.schema.model_fields
        header = ["Parameter", "Value"]
        table = []
        for row in _parameters:
            value = getattr(self, row)
            if value is not None and value != [] and value != "":
                if row == "status" and not isinstance(value, str):
                    table.append([row, value.status])
                elif isinstance(value, list):
                    table.append([row, "\n".join([f"{le}" for le in value])])
                else:
                    table.append([row, "\n".join(TextWrapper.wrap(f"{value}"))])
        return header, table

    def _repr_html_(self):
        if (
            hasattr(self, "status")
            and self.status.status == "Rejected"
            and self.status.__class__.__name__ == "TOOStatus"
        ):
            return "<b>Rejected with the following error(s): </b>" + " ".join(
                self.status.errors
            )
        else:
            header, table = self._table
            if len(table) > 0:
                return _tablefy(table, header)
            else:
                return "No data"

    def __str__(self):
        if (
            hasattr(self, "status")
            and self.status.status == "Rejected"
            and self.status.__class__.__name__ == "TOOStatus"
        ):
            return "Rejected with the following error(s): " + " ".join(
                self.status.errors
            )
        else:
            header, table = self._table
            if len(table) > 0:
                return tabulate(table, header, tablefmt="pretty", stralign="right")
            else:
                return "No data"

    def __repr__(self):
        name = self.__class__.__name__
        args = ",".join(
            [
                f"{row}='{getattr(self,row)}'"
                for row in self.schema.model_fields
                if getattr(self, row) is not None and getattr(self, row) != []
            ]
        )
        return f"{name}({args})"
