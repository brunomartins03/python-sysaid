"""Action items: ``/action_item``."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from .._params import quote_segment
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, RecordList, Resource, query


def _filter_params(
    type: str | Sequence[str] | None,
    ids: Sequence[int | str] | None,
    archive: bool | None,
    static_filter_id: str | None,
    text: str | None,
    filters: dict[str, Any],
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "type": type,
        "ids": ids,
        "staticFilterId": static_filter_id,
        "query": text,
    }
    if archive is not None:
        params["archive"] = 1 if archive else 0
    return {**params, **filters}


class ActionItems(Resource):
    """Action items attached to service requests."""

    def list(
        self,
        *,
        type: str | Sequence[str] | None = None,
        ids: Sequence[int | str] | None = None,
        archive: bool | None = None,
        static_filter_id: str | None = None,
        text: str | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: str | None = None,
        **filters: Any,
    ) -> RecordList:
        """One page of action items. ``ids`` are the *SR* ids whose items to return."""
        params = query(
            view=view,
            fields=fields,
            sort=sort,
            direction=direction,
            offset=offset,
            limit=limit,
            **_filter_params(type, ids, archive, static_filter_id, text, filters),
        )
        return self._list("/action_item", params)

    def iter(
        self,
        *,
        type: str | Sequence[str] | None = None,
        ids: Sequence[int | str] | None = None,
        archive: bool | None = None,
        static_filter_id: str | None = None,
        text: str | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        sort: str | None = None,
        direction: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        **filters: Any,
    ) -> Iterator[Record]:
        """Every matching action item, fetching pages transparently."""
        params = query(
            view=view,
            fields=fields,
            sort=sort,
            direction=direction,
            **_filter_params(type, ids, archive, static_filter_id, text, filters),
        )
        return self._iter("/action_item", params, page_size=page_size)

    def count(
        self,
        *,
        type: str | Sequence[str] | None = None,
        ids: Sequence[int | str] | None = None,
        archive: bool | None = None,
        static_filter_id: str | None = None,
        text: str | None = None,
        **filters: Any,
    ) -> int:
        """Number of action items matching the filters."""
        params = _filter_params(type, ids, archive, static_filter_id, text, filters)
        return int(self._client.request("GET", "/action_item/count", params=params)["count"])

    def approve(self, action_item_id: int | str) -> None:
        """Approve the action item."""
        self._change_state(action_item_id, "approve")

    def reject(self, action_item_id: int | str) -> None:
        """Reject the action item."""
        self._change_state(action_item_id, "reject")

    def complete(self, action_item_id: int | str) -> None:
        """Mark the action item as complete."""
        self._change_state(action_item_id, "complete")

    def reopen(self, action_item_id: int | str) -> None:
        """Reopen the action item."""
        self._change_state(action_item_id, "reopen")

    def _change_state(self, action_item_id: int | str, action: str) -> None:
        self._client.request("PUT", f"/action_item/{quote_segment(action_item_id)}/{action}")
