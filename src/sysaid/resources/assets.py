"""Assets: ``/asset``. Ids look like ``497db453:147bee7ec09:-7ff2`` and are URL-encoded."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from .._params import quote_segment
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, RecordList, Resource, query


class Assets(Resource):
    def list(
        self,
        *,
        type: str | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> RecordList:
        """``type`` is listed in the Help index only; it is passed through when given."""
        params = query(view=view, fields=fields, type=type, offset=offset, limit=limit)
        return self._list("/asset", params)

    def iter(
        self,
        *,
        type: str | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[Record]:
        return self._iter("/asset", query(view=view, fields=fields, type=type), page_size=page_size)

    def get(
        self, asset_id: str, *, view: str | None = None, fields: Sequence[str] | None = None
    ) -> Record:
        return self._get(f"/asset/{quote_segment(asset_id)}", query(view=view, fields=fields))

    def search(
        self,
        text: str,
        *,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> RecordList:
        params = query(view=view, fields=fields, query=text, offset=offset, limit=limit)
        return self._list("/asset/search", params)
