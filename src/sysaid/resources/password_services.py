"""Password self-service: ``/ps``. None of these calls needs a login."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._base import JSONDict, Resource


class PasswordServices(Resource):
    """Flow: :meth:`permissions` -> :meth:`questions` -> :meth:`unlock` or :meth:`reset`
    (-> :meth:`update_password` when the reset method is ``user``).
    """

    def domains(self) -> list[str]:
        """LDAP domain names."""
        result: list[str] = self._client.request("GET", "/ps/domain", auth=False)
        return result

    def permissions(self) -> JSONDict:
        result: JSONDict = self._client.request("GET", "/ps/permission", auth=False)
        return result

    def questions(self, method: str, user_name: str, domain_name: str | None = None) -> JSONDict:
        """Security questions for ``method`` (``reset`` or ``unlock``); keep ``userRefId``."""
        if method not in ("reset", "unlock"):
            raise ValueError("method must be 'reset' or 'unlock'")
        body = {"userName": user_name, "domainName": domain_name}
        result: JSONDict = self._client.request(
            "POST",
            f"/ps/{method}/question",
            json={key: value for key, value in body.items() if value is not None},
            auth=False,
        )
        return result

    def unlock(self, user_ref_id: int, questions: Sequence[Mapping[str, Any]]) -> JSONDict:
        """Unlock an account. ``questions`` are the items returned by :meth:`questions`,
        each with an added ``answer``."""
        return self._answered("/ps/unlock", user_ref_id, questions)

    def reset(self, user_ref_id: int, questions: Sequence[Mapping[str, Any]]) -> JSONDict:
        """Start a password reset; the response depends on the configured reset method."""
        return self._answered("/ps/reset", user_ref_id, questions)

    def update_password(self, user_ref_id: int, new_password: str, token: str) -> JSONDict:
        """Set the new password using the one-time ``token`` from :meth:`reset`."""
        result: JSONDict = self._client.request(
            "POST",
            "/ps/reset/update",
            json={"userRefId": user_ref_id, "newPassword": new_password, "token": token},
            auth=False,
        )
        return result

    def _answered(
        self, path: str, user_ref_id: int, questions: Sequence[Mapping[str, Any]]
    ) -> JSONDict:
        result: JSONDict = self._client.request(
            "POST",
            path,
            json={"userRefId": user_ref_id, "userSecurityQuestionsList": list(questions)},
            auth=False,
        )
        return result
