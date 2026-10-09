"""OAuth 1.0 helpers (optional extra: ``pip install python-sysaid[oauth]``).

Three-legged flow: :func:`request_token` -> send the user to :func:`authorize_url` ->
:func:`access_token` with the ``oauth_verifier`` from the callback. Then build a client
with :meth:`sysaid.SysAid.from_oauth`.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import requests

from ._unverified import unverified
from .client import api_url_for
from .exceptions import error_from_response


def oauth1(client_key: str, client_secret: str, **kwargs: Any) -> Any:
    """Build a ``requests_oauthlib.OAuth1`` auth object (HMAC-SHA1)."""
    try:
        from requests_oauthlib import OAuth1
    except ImportError as exc:
        raise ImportError(
            "OAuth support needs requests-oauthlib: pip install 'python-sysaid[oauth]'"
        ) from exc
    return OAuth1(client_key, client_secret=client_secret, **kwargs)


def _post(
    base_url: str, path: str, auth: Any, verify: bool | str, timeout: float | None
) -> dict[str, Any]:
    response = requests.post(
        api_url_for(base_url) + path, auth=auth, verify=verify, timeout=timeout
    )
    if not response.ok:
        raise error_from_response(response)
    token: dict[str, Any] = response.json()
    return token


@unverified
def request_token(
    base_url: str,
    consumer_key: str,
    callback_url: str,
    consumer_secret: str = "",
    *,
    verify: bool | str = True,
    timeout: float | None = 30,
) -> dict[str, Any]:
    """Step 1. Returns ``oauth_token``, ``oauth_token_secret`` and ``oauth_callback_confirmed``."""
    auth = oauth1(consumer_key, consumer_secret, callback_uri=callback_url)
    return _post(base_url, "/oauth/request_token", auth, verify, timeout)


@unverified
def authorize_url(base_url: str, request_token: str) -> str:
    """Step 2. The URL to send the user's browser to."""
    query = urlencode({"oauth_token": request_token})
    return f"{api_url_for(base_url)}/oauth/authorize?{query}"


@unverified
def access_token(
    base_url: str,
    consumer_key: str,
    request_token: str,
    request_token_secret: str,
    verifier: str,
    consumer_secret: str = "",
    *,
    verify: bool | str = True,
    timeout: float | None = 30,
) -> dict[str, Any]:
    """Step 3. Returns the access ``oauth_token`` and ``oauth_token_secret``."""
    auth = oauth1(
        consumer_key,
        consumer_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=verifier,
    )
    return _post(base_url, "/oauth/access_token", auth, verify, timeout)
