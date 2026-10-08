"""Shared plumbing for the resource classes."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ..models import Record

if TYPE_CHECKING:
    from ..client import SysAid

DEFAULT_PAGE_SIZE = 100


def query(
    *,
    view: str | None = None,
    fields: Sequence[str] | None = None,
    sort: str | None = None,
    direction: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Common list parameters (``dir`` is exposed as ``direction``) plus extras."""
    return {"view": view, "fields": fields, "sort": sort, "dir": direction, **extra}


class Resource:
    def __init__(self, client: SysAid) -> None:
        self._client = client

    def _get(self, path: str, params: Mapping[str, Any] | None = None) -> Record:
        return Record(self._client.request("GET", path, params=params))

    def _list(self, path: str, params: Mapping[str, Any] | None = None) -> list[Record]:
        return [Record(item) for item in self._client.request("GET", path, params=params)]

    def _iter(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Iterator[Record]:
        """Yield every record, fetching pages until one is shorter than ``page_size``."""
        while True:
            page = self._list(path, {**(params or {}), "offset": offset, "limit": page_size})
            yield from page
            if len(page) < page_size:
                return
            offset += page_size
