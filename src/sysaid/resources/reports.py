"""Reports: ``/reports``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._params import quote_segment
from ._base import JSONList, Resource


class Reports(Resource):
    """Report metadata and preview runs."""

    def operators(self, type: str | None = None) -> JSONList:
        """Field operators, optionally for one data type (``string``, ``date``, ``int``...)."""
        result: JSONList = self._client.request("GET", "/reports/operators", params={"type": type})
        return result

    def run_preview(self, report_id: int | str, definition: Mapping[str, Any]) -> Any:
        """Run a report in preview mode and return the raw JSON.

        ``definition`` is the report body (``entity``, ``select``, ``filter``, ``layout``).
        """
        return self._client.request(
            "POST", f"/reports/{quote_segment(report_id)}/runPreview", json=definition
        )
