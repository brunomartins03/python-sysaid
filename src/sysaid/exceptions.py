"""Exceptions raised by the SysAid client."""

from __future__ import annotations

from typing import Any

import requests


class SysAidError(Exception):
    """Base class for every error raised by this package."""


class AuthenticationError(SysAidError):
    """Login failed, or credentials are missing."""


class SysAidHTTPError(SysAidError):
    """The server answered with a non-2xx status."""

    def __init__(
        self, status_code: int, message: str, response: requests.Response | None = None
    ) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.response = response


class BadRequestError(SysAidHTTPError):
    """HTTP 400."""


class RelationError(BadRequestError):
    """CI relations could not be created; ``failures`` lists each failing item."""

    @property
    def failures(self) -> list[str]:
        """The per-item messages from the server's CSV error text."""
        return [part.strip() for part in self.message.split(",") if part.strip()]


class UnauthorizedError(SysAidHTTPError):
    """HTTP 401."""


class ForbiddenError(SysAidHTTPError):
    """HTTP 403."""


class NotFoundError(SysAidHTTPError):
    """HTTP 404."""


class ServerError(SysAidHTTPError):
    """HTTP 5xx."""


_BY_STATUS: dict[int, type[SysAidHTTPError]] = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
}


def _message_from(response: requests.Response) -> str:
    """Return ``message`` from a ``{"status", "message"}`` body, else the raw text."""
    try:
        body: Any = response.json()
    except ValueError:
        return response.text or response.reason or ""
    if isinstance(body, dict) and body.get("message") is not None:
        return str(body["message"])
    return response.text


def error_from_response(response: requests.Response) -> SysAidHTTPError:
    """Build the typed exception matching a non-2xx response."""
    status = response.status_code
    cls = _BY_STATUS.get(status)
    if cls is None:
        cls = ServerError if status >= 500 else SysAidHTTPError
    return cls(status, _message_from(response), response)
