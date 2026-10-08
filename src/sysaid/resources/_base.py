"""Shared plumbing for the resource classes."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..models import Record

if TYPE_CHECKING:
    from ..client import SysAid

DEFAULT_PAGE_SIZE = 100

# Resource classes define methods named ``list``/``iter``, which would shadow the
# builtins in annotations inside the class body; these aliases avoid that.
RecordList = list[Record]
JSONDict = dict[str, Any]
JSONList = list[dict[str, Any]]


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


def read_upload(file: bytes | str | PathLike[str], filename: str | None) -> tuple[str, bytes]:
    """Resolve an upload given as bytes or a path into ``(filename, content)``."""
    if isinstance(file, bytes):
        return filename or "file", file
    path = Path(file)
    return filename or path.name, path.read_bytes()


class Resource:
    def __init__(self, client: SysAid) -> None:
        self._client = client

    def _get(self, path: str, params: Mapping[str, Any] | None = None) -> Record:
        return Record(self._client.request("GET", path, params=params))

    def _list(self, path: str, params: Mapping[str, Any] | None = None) -> RecordList:
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
