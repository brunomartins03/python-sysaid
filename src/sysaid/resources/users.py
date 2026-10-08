"""Users: ``/users``."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from os import PathLike

from .._params import quote_segment
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, JSONDict, RecordList, Resource, query, read_upload

MAX_PHOTO_BYTES = 500 * 1024


class Users(Resource):
    def list(
        self,
        *,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        type: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> RecordList:
        """One page of users. ``type`` is ``admin``, ``user`` or ``manager``."""
        params = query(view=view, fields=fields, type=type, offset=offset, limit=limit)
        return self._list("/users", params)

    def iter(
        self,
        *,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        type: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[Record]:
        """Every user, fetching pages transparently."""
        return self._iter("/users", query(view=view, fields=fields, type=type), page_size=page_size)

    def get(
        self, user_id: int | str, *, view: str | None = None, fields: Sequence[str] | None = None
    ) -> Record:
        return self._get(f"/users/{quote_segment(user_id)}", query(view=view, fields=fields))

    def search(
        self,
        text: str,
        *,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        type: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: str | None = None,
    ) -> RecordList:
        params = query(
            view=view,
            fields=fields,
            sort=sort,
            direction=direction,
            query=text,
            type=type,
            offset=offset,
            limit=limit,
        )
        return self._list("/users/search", params)

    def get_photo(self, user_id: int | str) -> bytes:
        """Raw bytes of the user's photo."""
        response = self._client.request("GET", f"/users/{quote_segment(user_id)}/photo", raw=True)
        return bytes(response.content)

    def upload_photo(
        self, user_id: int | str, photo: bytes | str | PathLike[str], filename: str | None = None
    ) -> None:
        """Upload a photo, given as bytes or a file path. The server limit is 500 KB."""
        filename, content = read_upload(photo, filename)
        if len(content) > MAX_PHOTO_BYTES:
            raise ValueError(f"photo is {len(content)} bytes; the limit is {MAX_PHOTO_BYTES}")
        self._client.request(
            "POST",
            f"/users/{quote_segment(user_id)}/photo",
            files={"file": (filename, content)},
        )

    def permissions(self, user_id: int | str) -> JSONDict:
        """``{id, name, permissions: [{key, value}]}`` for the user."""
        result: JSONDict = self._client.request(
            "GET", f"/users/{quote_segment(user_id)}/permission"
        )
        return result

    def permission(self, user_id: int | str, permission_id: str) -> JSONDict:
        """``{key, value}`` for one permission."""
        result: JSONDict = self._client.request(
            "GET", f"/users/{quote_segment(user_id)}/permission/{quote_segment(permission_id)}"
        )
        return result
