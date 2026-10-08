"""Filters: ``/filters``."""

from __future__ import annotations

from collections.abc import Sequence

from .._params import quote_segment
from ._base import JSONDict, JSONList, Resource, query


class Filters(Resource):
    """Valid query parameters (and their values) for list calls such as ``/sr``."""

    def list(
        self,
        *,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> JSONList:
        """``offset``/``limit`` page the filter *values*."""
        result: JSONList = self._client.request(
            "GET",
            "/filters",
            params=query(view=view, fields=fields, offset=offset, limit=limit),
        )
        return result

    def get(
        self,
        filter_id: str,
        *,
        view: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> JSONDict:
        """One filter with its values; ``offset``/``limit`` page the values."""
        result: JSONDict = self._client.request(
            "GET",
            f"/filters/{quote_segment(filter_id)}",
            params=query(view=view, offset=offset, limit=limit),
        )
        return result
