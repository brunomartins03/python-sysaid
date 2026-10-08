"""Service requests (incident, request, problem, change): ``/sr``."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from .._params import quote_segment
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, RecordList, Resource, query

SrType = str | Sequence[str]


def make_note(user_name: str, text: str, created: datetime | None = None) -> dict[str, Any]:
    """An entry for the ``notes`` field."""
    return {
        "userName": user_name,
        "createDate": created or datetime.now(timezone.utc),
        "text": text,
    }


def problem_type(*levels: str) -> str:
    """Join up to three category levels into the ``problem_type`` value."""
    if not 1 <= len(levels) <= 3:
        raise ValueError("problem_type takes one to three category levels")
    return "_".join(levels)


class ServiceRequests(Resource):
    def list(
        self,
        *,
        type: SrType | None = None,
        ids: Sequence[int | str] | None = None,
        archive: bool | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: str | None = None,
        **filters: Any,
    ) -> RecordList:
        """One page of SRs. Extra keyword arguments are filters from ``client.filters``."""
        params = self._list_params(type, ids, archive, view, fields, sort, direction, filters)
        return self._list("/sr", {**params, "offset": offset, "limit": limit})

    def iter(
        self,
        *,
        type: SrType | None = None,
        ids: Sequence[int | str] | None = None,
        archive: bool | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        sort: str | None = None,
        direction: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        **filters: Any,
    ) -> Iterator[Record]:
        """Every matching SR, fetching pages transparently."""
        params = self._list_params(type, ids, archive, view, fields, sort, direction, filters)
        return self._iter("/sr", params, page_size=page_size)

    def get(
        self, sr_id: int | str, *, view: str | None = None, fields: Sequence[str] | None = None
    ) -> Record:
        """The SR as a form: fields carry ``mandatory``/``editable``/``type`` metadata."""
        return self._get(f"/sr/{quote_segment(sr_id)}", query(view=view, fields=fields))

    def search(
        self,
        text: str,
        *,
        type: SrType | None = None,
        archive: bool | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: str | None = None,
        **filters: Any,
    ) -> RecordList:
        """Search SRs; the server defaults ``type`` to ``incident`` here."""
        params = self._list_params(type, None, archive, view, fields, sort, direction, filters)
        return self._list("/sr/search", {**params, "query": text, "offset": offset, "limit": limit})

    def count(self, **filters: Any) -> int:
        result = self._client.request("GET", "/sr/count", params=filters)
        return int(result["count"])

    def template(
        self,
        *,
        type: str | None = None,
        template: int | str | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
    ) -> Record:
        """A blank SR (``id`` ``"0"``) showing mandatory fields and defaults."""
        return self._get(
            "/sr/template", query(view=view, fields=fields, type=type, template=template)
        )

    @staticmethod
    def _list_params(
        type: SrType | None,
        ids: Sequence[int | str] | None,
        archive: bool | None,
        view: str | None,
        fields: Sequence[str] | None,
        sort: str | None,
        direction: str | None,
        filters: Mapping[str, Any],
    ) -> dict[str, Any]:
        params = query(view=view, fields=fields, sort=sort, direction=direction, type=type, ids=ids)
        if archive is not None:
            params["archive"] = 1 if archive else 0
        return {**params, **filters}
