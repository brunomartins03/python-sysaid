"""The :class:`SysAid` client."""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

import requests

from . import auth as _auth
from ._params import build_params, encode_json
from ._unverified import unverified
from .exceptions import AuthenticationError, error_from_response
from .resources.action_items import ActionItems
from .resources.addons import Addons
from .resources.assets import Assets
from .resources.cis import CIs
from .resources.filters import Filters
from .resources.lists import Lists
from .resources.password_services import PasswordServices
from .resources.reports import Reports
from .resources.resource_bundle import ResourceBundle
from .resources.service_requests import ServiceRequests
from .resources.users import Users

API_PATH = "/api/v1"


def api_url_for(base_url: str) -> str:
    """``https://host`` or ``https://host/api/v1`` -> ``https://host/api/v1``."""
    base = base_url.rstrip("/")
    return base if base.endswith(API_PATH) else base + API_PATH


class SysAid:
    """Client for the SysAid REST API.

    Credentials are optional: with ``username`` and ``password`` the client logs in
    on first use; without them only unauthenticated calls (password services) work.
    """

    def __init__(
        self,
        base_url: str,
        username: str | None = None,
        password: str | None = None,
        account_id: str | None = None,
        timeout: float | None = 30,
        verify: bool | str = True,
        session: requests.Session | None = None,
    ) -> None:
        self.api_url = api_url_for(base_url)
        self.account_id = account_id
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.verify = verify
        self._username = username
        self._password = password
        self._logged_in = False
        self.users = Users(self)
        self.filters = Filters(self)
        self.lists = Lists(self)
        self.service_requests = ServiceRequests(self)
        self.action_items = ActionItems(self)
        self.assets = Assets(self)
        self.cis = CIs(self)
        self.addons = Addons(self)
        self.resource_bundle = ResourceBundle(self)
        self.password_services = PasswordServices(self)
        self.reports = Reports(self)

    @classmethod
    @unverified
    def from_oauth(
        cls,
        base_url: str,
        consumer_key: str,
        access_token: str,
        access_token_secret: str,
        consumer_secret: str = "",
        **kwargs: Any,
    ) -> SysAid:
        """A client that signs every request with OAuth 1.0 (needs ``python-sysaid[oauth]``)."""
        from .oauth import oauth1

        client = cls(base_url, **kwargs)
        client.session.auth = oauth1(
            consumer_key,
            consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        return client

    def __repr__(self) -> str:
        return f"SysAid({self.api_url!r}, username={self._username!r})"

    def __enter__(self) -> SysAid:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()
        self._logged_in = False

    def login(self) -> _auth.LoginResult:
        """Log in with the configured credentials."""
        if self._username is None or self._password is None:
            raise AuthenticationError("username and password are required to log in")
        result = _auth.login(self, self._username, self._password, self.account_id)
        self._logged_in = True
        return result

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        files: Any = None,
        auth: bool = True,
        raw: bool = False,
    ) -> Any:
        """Send a request and return the decoded JSON (text if not JSON, ``None`` if empty).

        With ``raw=True`` the :class:`requests.Response` is returned instead.
        With ``auth=False`` no login is attempted first.
        """
        if auth and not self._logged_in and self._username is not None:
            self.login()
        response = self.session.request(
            method,
            self.api_url + "/" + path.lstrip("/"),
            params=build_params(params or {}),
            json=encode_json(json),
            data=data,
            files=files,
            timeout=self.timeout,
        )
        if not response.ok:
            raise error_from_response(response)
        if raw:
            return response
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text
