"""Add-ons: ``/addons``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._params import quote_segment
from ._base import JSONDict, JSONList, Resource


def _payload(name: str, active: bool | None, params: Mapping[str, Any] | None) -> JSONDict:
    body: JSONDict = {"name": name}
    if active is not None:
        body["active"] = active
    if params is not None:
        body["params"] = [{"name": key, "value": value} for key, value in params.items()]
    return body


class Addons(Resource):
    """SysAid add-ons and their parameters."""

    def list(self) -> JSONList:
        """All add-ons (``params`` is always ``None`` in this list)."""
        result: JSONList = self._client.request("GET", "/addons")
        return result

    def get(self, name: str) -> JSONDict:
        """The add-on with its ``params``."""
        result: JSONDict = self._client.request("GET", f"/addons/{quote_segment(name)}")
        return result

    def update(
        self, name: str, *, active: bool | None = None, params: Mapping[str, Any] | None = None
    ) -> Any:
        """Set ``active`` and/or parameter values (``{param name: value}``).

        Only these are updated server-side. The server answers with a message.
        """
        return self._client.request(
            "PUT", f"/addons/{quote_segment(name)}", json=_payload(name, active, params)
        )

    def test_connection(
        self, name: str, *, active: bool | None = None, params: Mapping[str, Any] | None = None
    ) -> Any:
        """Same payload as :meth:`update`, but only tests; nothing is saved."""
        return self._client.request(
            "PUT",
            f"/addons/{quote_segment(name)}/testConnection",
            json=_payload(name, active, params),
        )

    def refresh(self) -> Any:
        """Refresh the add-ons list immediately."""
        return self._client.request("GET", "/addons/refresh")
