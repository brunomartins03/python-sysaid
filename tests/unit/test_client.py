from typing import Any

import pytest
import responses

from sysaid import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    SysAid,
    SysAidHTTPError,
    UnauthorizedError,
)
from sysaid.resources._base import Resource
from tests.conftest import API, BASE_URL

LOGIN_OK = {
    "language": "en",
    "sysaid_version": "24.4.60",
    "date_format": "yyyymmdd hh:MM:ss",
    "user": {"id": "2", "name": "sysaid", "info": [{"key": "display_name", "value": "Sys"}]},
}


@responses.activate
def test_base_url_gets_api_prefix_once() -> None:
    assert SysAid(BASE_URL + "/").api_url == API
    assert SysAid(API).api_url == API


@responses.activate
def test_request_sends_encoded_params(client: SysAid) -> None:
    responses.get(
        API + "/sr",
        json=[],
        match=[responses.matchers.query_param_matcher({"status": "4,5", "archive": "true"})],
    )
    assert client.request("GET", "/sr", params={"status": [4, 5], "archive": True, "x": None}) == []


@responses.activate
def test_non_json_and_empty_bodies(client: SysAid) -> None:
    responses.get(API + "/a", body="OK")
    responses.get(API + "/b", status=204)
    assert client.request("GET", "/a") == "OK"
    assert client.request("GET", "/b") is None


@responses.activate
def test_raw_returns_response(client: SysAid) -> None:
    responses.get(API + "/users/1/photo", body=b"\x89PNG")
    assert client.request("GET", "/users/1/photo", raw=True).content == b"\x89PNG"


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, BadRequestError),
        (401, UnauthorizedError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (500, ServerError),
        (409, SysAidHTTPError),
    ],
)
@responses.activate
def test_errors_are_mapped(client: SysAid, status: int, exc: type[SysAidHTTPError]) -> None:
    responses.get(API + "/sr", status=status, json={"status": status, "message": "boom"})
    with pytest.raises(exc) as info:
        client.request("GET", "/sr")
    assert info.value.status_code == status
    assert info.value.message == "boom"
    assert info.value.response is not None


@responses.activate
def test_error_message_skips_html_pages(client: SysAid) -> None:
    responses.get(API + "/sr", status=404, body="<html>Not Found</html>", content_type="text/html")
    with pytest.raises(NotFoundError) as info:
        client.request("GET", "/sr")
    assert info.value.message == "Not Found"


@responses.activate
def test_error_message_falls_back_to_text(client: SysAid) -> None:
    responses.get(API + "/sr", status=500, body="plain failure")
    with pytest.raises(ServerError, match="plain failure"):
        client.request("GET", "/sr")


@responses.activate
def test_login_posts_json_and_is_lazy() -> None:
    responses.post(API + "/login", json=LOGIN_OK)
    responses.get(API + "/sr", json=[])
    client = SysAid(BASE_URL, username="sysaid", password="secret", account_id="cmdb")
    assert len(responses.calls) == 0
    client.request("GET", "/sr")
    client.request("GET", "/sr")
    login_calls = [c for c in responses.calls if str(c.request.url).endswith("/login")]
    assert len(login_calls) == 1
    assert login_calls[0].request.body == (
        b'{"user_name": "sysaid", "password": "secret", "account_id": "cmdb"}'
    )


@responses.activate
def test_login_result() -> None:
    responses.post(API + "/login", json=LOGIN_OK)
    result = SysAid(BASE_URL, username="sysaid", password="p").login()
    assert result.logged_in
    assert result.user_id == "2"
    assert result.sysaid_version == "24.4.60"
    assert result.user is not None
    assert result.user["display_name"] == "Sys"


@responses.activate
def test_login_failures_raise_authentication_error() -> None:
    responses.post(API + "/login", json={"logged_in": False, "error_msg": "bad credentials"})
    with pytest.raises(AuthenticationError, match="bad credentials"):
        SysAid(BASE_URL, username="u", password="p").login()
    responses.replace(responses.POST, API + "/login", status=401, body="no")
    with pytest.raises(AuthenticationError):
        SysAid(BASE_URL, username="u", password="p").login()


def test_login_without_credentials_raises(client: SysAid) -> None:
    with pytest.raises(AuthenticationError):
        client.login()


@responses.activate
def test_auth_false_skips_login() -> None:
    responses.get(API + "/ps/permission", json={})
    client = SysAid(BASE_URL, username="u", password="p")
    client.request("GET", "/ps/permission", auth=False)
    assert len(responses.calls) == 1


def test_repr_hides_password() -> None:
    assert "secret" not in repr(SysAid(BASE_URL, username="u", password="secret"))


@responses.activate
def test_context_manager_closes_session() -> None:
    with SysAid(BASE_URL) as client:
        responses.get(API + "/sr", json=[])
        client.request("GET", "/sr")


@responses.activate
def test_iter_stops_on_short_page(client: SysAid) -> None:
    def page(ids: list[int]) -> list[dict[str, Any]]:
        return [{"id": str(i), "info": []} for i in ids]

    responses.get(
        API + "/sr",
        json=page([1, 2]),
        match=[responses.matchers.query_param_matcher({"offset": "0", "limit": "2"})],
    )
    responses.get(
        API + "/sr",
        json=page([3, 4]),
        match=[responses.matchers.query_param_matcher({"offset": "2", "limit": "2"})],
    )
    responses.get(
        API + "/sr",
        json=page([5]),
        match=[responses.matchers.query_param_matcher({"offset": "4", "limit": "2"})],
    )
    ids = [r.id for r in Resource(client)._iter("/sr", page_size=2)]
    assert ids == ["1", "2", "3", "4", "5"]


@responses.activate
def test_iter_stops_after_empty_full_boundary(client: SysAid) -> None:
    responses.get(
        API + "/sr",
        json=[{"id": "1", "info": []}],
        match=[
            responses.matchers.query_param_matcher(
                {"offset": "0", "limit": "1", "type": "incident"}
            )
        ],
    )
    responses.get(
        API + "/sr",
        json=[],
        match=[
            responses.matchers.query_param_matcher(
                {"offset": "1", "limit": "1", "type": "incident"}
            )
        ],
    )
    records = list(Resource(client)._iter("/sr", {"type": "incident"}, page_size=1))
    assert [r.id for r in records] == ["1"]
