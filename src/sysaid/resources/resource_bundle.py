"""Resource bundle translations: ``/rb``."""

from __future__ import annotations

from collections.abc import Sequence

from .._params import quote_segment
from ._base import Resource


class ResourceBundle(Resource):
    def translate(self, keys: Sequence[str], locale: str | None = None) -> dict[str, str]:
        """Translate resource-bundle keys, for the account locale or the given one."""
        path = "/rb" if locale is None else f"/rb/{quote_segment(locale)}"
        result = self._client.request("POST", path, json=[{"key": key} for key in keys])
        return {item["key"]: item["value"] for item in result}
