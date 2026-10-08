"""Configuration items: ``/ci``."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

from .._params import encode_info, quote_segment
from ..exceptions import BadRequestError, RelationError
from ..models import Record
from ._base import DEFAULT_PAGE_SIZE, JSONList, RecordList, Resource, query

Relation = tuple[int, int] | Mapping[str, Any]


def _relations_body(relations: Iterable[Relation]) -> list[dict[str, Any]]:
    """Accept ``(dest, relation_type_id)`` tuples or ready ``{dest, ciRelationType}`` dicts."""
    return [
        {"dest": item[0], "ciRelationType": item[1]} if isinstance(item, tuple) else dict(item)
        for item in relations
    ]


class CIs(Resource):
    def list(
        self,
        *,
        ids: Sequence[int | str] | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: str | None = None,
        support_barcode: bool | None = None,
        **filters: Any,
    ) -> RecordList:
        params = query(
            view=view,
            fields=fields,
            sort=sort,
            direction=direction,
            ids=ids,
            offset=offset,
            limit=limit,
            supportBarcode=support_barcode,
            **filters,
        )
        return self._list("/ci", params)

    def iter(
        self,
        *,
        ids: Sequence[int | str] | None = None,
        view: str | None = None,
        fields: Sequence[str] | None = None,
        sort: str | None = None,
        direction: str | None = None,
        support_barcode: bool | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        **filters: Any,
    ) -> Iterator[Record]:
        params = query(
            view=view,
            fields=fields,
            sort=sort,
            direction=direction,
            ids=ids,
            supportBarcode=support_barcode,
            **filters,
        )
        return self._iter("/ci", params, page_size=page_size)

    def update(
        self, ci_id: int | str, values: Mapping[str, Any] | None = None, /, **fields: Any
    ) -> None:
        """Update the given fields only."""
        body = {"id": str(ci_id), "info": encode_info({**(values or {}), **fields})}
        self._client.request("PUT", f"/ci/{quote_segment(ci_id)}", json=body)

    def types(self, *, support_barcode: bool | None = None) -> JSONList:
        result: JSONList = self._client.request(
            "GET", "/ci/type", params={"supportBarcode": support_barcode}
        )
        return result

    def view_fields(self, ci_type_id: int | str, *, view: str | None = None) -> Any:
        """Fields of a view for a CI type, as returned by the server."""
        return self._client.request(
            "GET", f"/ci/view/{quote_segment(ci_type_id)}", params={"view": view}
        )

    def relation_types(self) -> JSONList:
        result: JSONList = self._client.request("GET", "/ci/relationtypes")
        return result

    def relations(self, ci_id: int | str) -> JSONList:
        result: JSONList = self._client.request("GET", f"/ci/{quote_segment(ci_id)}/relation")
        return result

    def create_relations(self, ci_id: int | str, relations: Iterable[Relation]) -> None:
        """Create relations; existing ones are not duplicated.

        Raises :class:`RelationError` (HTTP 400) listing each failing item.
        """
        try:
            self._client.request(
                "POST", f"/ci/{quote_segment(ci_id)}/relation", json=_relations_body(relations)
            )
        except BadRequestError as exc:
            raise RelationError(exc.status_code, exc.message, exc.response) from exc

    def delete_relations(self, ci_id: int | str, relations: Iterable[Relation]) -> None:
        """Delete relations; the server answers OK even for relations that do not exist."""
        self._client.request(
            "DELETE", f"/ci/{quote_segment(ci_id)}/relation", json=_relations_body(relations)
        )
