"""Lists (dropdown id/caption pairs): ``/list``."""

from __future__ import annotations

from collections.abc import Sequence

from .._params import quote_segment
from ._base import JSONDict, JSONList, Resource, query


class Lists(Resource):
    def list(
        self,
        *,
        entity: str | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> JSONList:
        """All lists of an entity (server default ``sr``)."""
        result: JSONList = self._client.request(
            "GET",
            "/list",
            params=query(entity=entity, fields=fields, offset=offset, limit=limit),
        )
        return result

    def get(
        self,
        list_id: str,
        *,
        entity: str | None = None,
        entity_id: int | str | None = None,
        entity_type: int | None = None,
        fields: Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        key: str | None = None,
    ) -> JSONDict:
        """One list. ``entity_id`` applies per-record filtering; ``key`` is ``id`` or ``name``."""
        result: JSONDict = self._client.request(
            "GET",
            f"/list/{quote_segment(list_id)}",
            params=query(
                entity=entity,
                entityId=entity_id,
                entityType=entity_type,
                fields=fields,
                offset=offset,
                limit=limit,
                key=key,
            ),
        )
        return result
