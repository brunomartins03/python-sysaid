"""Service requests (incident, request, problem, change): ``/sr``."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timezone
from os import PathLike
from typing import Any

from .._params import encode_info, encode_value, quote_segment
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, RecordList, Resource, query, read_upload

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
    """Service requests: incidents, requests, problems and changes."""

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
        """Number of SRs matching the filters."""
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

    def create(
        self,
        values: Mapping[str, Any] | None = None,
        /,
        *,
        type: str | None = None,
        template: int | str | None = None,
        view: str | None = None,
        return_fields: Sequence[str] | None = None,
        **fields: Any,
    ) -> Record:
        """Create an SR from field values, given as keywords and/or a mapping.

        Use the mapping for field ids that clash with this method's own keywords
        (e.g. the SR field ``type``). ``type`` and ``template`` select the SR type and
        template; ``view`` and ``return_fields`` shape the returned record.
        """
        body = {"info": encode_info({**(values or {}), **fields})}
        params = query(view=view, fields=return_fields, type=type, template=template)
        return Record(self._client.request("POST", "/sr", params=params, json=body))

    def update(
        self, sr_id: int | str, values: Mapping[str, Any] | None = None, /, **fields: Any
    ) -> None:
        """Update the given fields only. Datetimes become ms-epoch UTC."""
        body = {"id": str(sr_id), "info": encode_info({**(values or {}), **fields})}
        self._client.request("PUT", f"/sr/{quote_segment(sr_id)}", json=body)

    def close(self, sr_id: int | str, solution: str | None = None) -> None:
        """Set the SR to the default *Close* status."""
        body = None if solution is None else {"solution": solution}
        self._client.request("PUT", f"/sr/{quote_segment(sr_id)}/close", json=body)

    def delete(self, ids: int | str | Sequence[int | str]) -> None:
        """Delete one or more SRs."""
        id_list = [ids] if isinstance(ids, (int, str)) else ids
        self._client.request("DELETE", "/sr", params={"ids": id_list})

    def add_link(self, sr_id: int | str, name: str, link: str) -> None:
        """Add a named link to the SR."""
        self._client.request(
            "POST", f"/sr/{quote_segment(sr_id)}/link", json={"name": name, "link": link}
        )

    def delete_link(self, sr_id: int | str, name: str) -> None:
        """Delete a link from the SR by name."""
        self._client.request("DELETE", f"/sr/{quote_segment(sr_id)}/link", json={"name": name})

    def add_attachment(
        self, sr_id: int | str, file: bytes | str | PathLike[str], filename: str | None = None
    ) -> None:
        """Attach a file, given as bytes or a path (multipart part ``file``)."""
        name, content = read_upload(file, filename)
        self._client.request(
            "POST", f"/sr/{quote_segment(sr_id)}/attachment", files={"file": (name, content)}
        )

    def delete_attachment(self, sr_id: int | str, file_id: str) -> None:
        """Delete an attachment by its file id."""
        self._client.request(
            "DELETE", f"/sr/{quote_segment(sr_id)}/attachment", json={"fileId": file_id}
        )

    def add_activity(
        self,
        sr_id: int | str,
        user_id: int | str,
        from_time: datetime | int,
        to_time: datetime | int,
        description: str,
    ) -> None:
        """Log an activity for the user with the given numeric id.

        Times are datetimes or ms-epoch integers.
        """
        body = {
            "userId": user_id,
            "fromTime": from_time,
            "toTime": to_time,
            "description": description,
        }
        self._client.request("POST", f"/sr/{quote_segment(sr_id)}/activity", json=body)

    def delete_activity(self, sr_id: int | str, activity_id: int) -> None:
        """Delete an activity by id."""
        self._client.request(
            "DELETE", f"/sr/{quote_segment(sr_id)}/activity", json={"id": activity_id}
        )

    def send_message(
        self,
        sr_id: int | str,
        to_users: str | Sequence[int | str],
        *,
        from_user_id: int | str,
        subject: str | None = None,
        body: str | None = None,
        cc_users: str | Sequence[int | str] | None = None,
        method: str | None = None,
        add_attachment_to_sr: bool | None = None,
        add_sr_details: bool | None = None,
        attachments: Sequence[bytes | str | PathLike[str]] = (),
    ) -> None:
        """Send a message from the SR.

        Recipients are user ids; a group id goes in brackets, e.g. ``"[3]"``. ``method`` is
        ``email`` (default), ``sms``, ``broadcast`` or ``im``.
        """
        message = {
            "fromUserId": str(from_user_id),
            "toUsers": encode_value(to_users),
            "ccUsers": None if cc_users is None else encode_value(cc_users),
            "msgSubject": subject,
            "msgBody": body,
        }
        parts: list[tuple[str, tuple[str | None, Any]]] = [
            ("message", (None, json.dumps({k: v for k, v in message.items() if v is not None})))
        ]
        parts += [("file", read_upload(attachment, None)) for attachment in attachments]
        self._client.request(
            "POST",
            f"/sr/{quote_segment(sr_id)}/message",
            params={
                "method": method,
                "addAttachmentToSr": add_attachment_to_sr,
                "addSrDetails": add_sr_details,
            },
            files=parts,
        )
