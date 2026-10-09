"""Session-cookie login (``POST /login``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .exceptions import AuthenticationError, ForbiddenError, UnauthorizedError
from .models import Record

if TYPE_CHECKING:
    from .client import SysAid


@dataclass(frozen=True)
class LoginResult:
    """Outcome of a successful login."""

    logged_in: bool
    user_id: str | None
    language: str | None
    sysaid_version: str | None
    date_format: str | None
    error_msg: str | None
    user: Record | None
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoginResult:
        """Build from the ``/login`` response body."""
        user = Record(data["user"]) if isinstance(data.get("user"), dict) else None
        user_id = data.get("user_id") or (user.id if user else None)
        return cls(
            logged_in=data.get("logged_in", True) is not False,
            user_id=None if user_id is None else str(user_id),
            language=data.get("language"),
            sysaid_version=data.get("sysaid_version"),
            date_format=data.get("date_format"),
            error_msg=data.get("error_msg"),
            user=user,
            raw=data,
        )


def login(
    client: SysAid, username: str, password: str, account_id: str | None = None
) -> LoginResult:
    """Authenticate; the ``JSESSIONID`` cookie is kept by the client's session."""
    body = {"user_name": username, "password": password, "account_id": account_id}
    try:
        data = client.request(
            "POST",
            "/login",
            json={key: value for key, value in body.items() if value is not None},
            auth=False,
        )
    except (UnauthorizedError, ForbiddenError) as exc:
        raise AuthenticationError(exc.message) from exc
    result = LoginResult.from_dict(data if isinstance(data, dict) else {})
    if not result.logged_in:
        raise AuthenticationError(result.error_msg or "login failed")
    return result
