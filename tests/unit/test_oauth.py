import sys

import pytest
import responses

from sysaid import SysAid, UnauthorizedError, oauth
from tests.conftest import API, BASE_URL


def auth_header(call: responses.Call) -> str:
    return str(call.request.headers["Authorization"])


@responses.activate
def test_request_token_signs_with_callback() -> None:
    responses.post(
        API + "/oauth/request_token",
        json={"oauth_token": "rt", "oauth_token_secret": "rs", "oauth_callback_confirmed": True},
    )
    token = oauth.request_token(BASE_URL, "ck", "http://app/cb", "cs")
    assert token["oauth_callback_confirmed"] is True
    header = auth_header(responses.calls[0])
    assert 'oauth_consumer_key="ck"' in header
    assert 'oauth_callback="http%3A%2F%2Fapp%2Fcb"' in header
    assert 'oauth_signature_method="HMAC-SHA1"' in header
    assert 'oauth_version="1.0"' in header


def test_authorize_url() -> None:
    assert oauth.authorize_url(BASE_URL, "a b") == API + "/oauth/authorize?oauth_token=a+b"


@responses.activate
def test_access_token_sends_verifier() -> None:
    responses.post(
        API + "/oauth/access_token", json={"oauth_token": "at", "oauth_token_secret": "as"}
    )
    token = oauth.access_token(BASE_URL, "ck", "rt", "rs", "ver", "cs")
    assert token["oauth_token"] == "at"
    header = auth_header(responses.calls[0])
    assert 'oauth_token="rt"' in header
    assert 'oauth_verifier="ver"' in header


@responses.activate
def test_from_oauth_signs_api_calls_without_login() -> None:
    responses.get(API + "/sr", json=[])
    client = SysAid.from_oauth(BASE_URL, "ck", "at", "as", consumer_secret="cs")
    client.service_requests.list()
    assert len(responses.calls) == 1
    header = auth_header(responses.calls[0])
    assert 'oauth_token="at"' in header
    assert 'oauth_consumer_key="ck"' in header


@responses.activate
def test_oauth_errors_are_typed() -> None:
    responses.post(API + "/oauth/request_token", status=401, body="bad consumer")
    with pytest.raises(UnauthorizedError, match="bad consumer"):
        oauth.request_token(BASE_URL, "ck", "http://app/cb")


def test_missing_extra_gives_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "requests_oauthlib", None)
    with pytest.raises(ImportError, match=r"python-sysaid\[oauth\]"):
        oauth.oauth1("ck", "cs")
