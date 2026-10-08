from typing import Any

import pytest
import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from sysaid.resources.users import MAX_PHOTO_BYTES
from tests.conftest import API


@responses.activate
def test_list(client: SysAid, load_fixture: Any) -> None:
    responses.get(
        API + "/users",
        json=load_fixture("users_list.json"),
        match=[
            query_param_matcher({"view": "Mobile", "fields": "a,b", "type": "admin", "limit": "5"})
        ],
    )
    users = client.users.list(view="Mobile", fields=["a", "b"], type="admin", limit=5)
    assert users[0].id == "1"
    assert users[0]["display_name"] == "John Doe"
    assert users[0].raw["name"] == "ILIENT\\Johnny"


@responses.activate
def test_iter_pages(client: SysAid) -> None:
    for offset, ids in (("0", ["1", "2"]), ("2", ["3"])):
        responses.get(
            API + "/users",
            json=[{"id": i, "info": []} for i in ids],
            match=[query_param_matcher({"offset": offset, "limit": "2"})],
        )
    assert [u.id for u in client.users.iter(page_size=2)] == ["1", "2", "3"]


@responses.activate
def test_get(client: SysAid) -> None:
    responses.get(
        API + "/users/1",
        json={"id": "1", "info": [{"key": "phone", "value": "1"}]},
        match=[query_param_matcher({"view": "Mobile"})],
    )
    assert client.users.get(1, view="Mobile")["phone"] == "1"


@responses.activate
def test_search(client: SysAid) -> None:
    responses.get(
        API + "/users/search",
        json=[{"id": "2", "isAdmin": True, "info": []}],
        match=[
            query_param_matcher(
                {"query": "Jo", "fields": "display_name", "dir": "desc", "sort": "x"}
            )
        ],
    )
    found = client.users.search("Jo", fields=["display_name"], sort="x", direction="desc")
    assert found[0].raw["isAdmin"] is True


@responses.activate
def test_get_photo(client: SysAid) -> None:
    responses.get(API + "/users/1/photo", body=b"\xff\xd8jpeg")
    assert client.users.get_photo(1) == b"\xff\xd8jpeg"


@responses.activate
def test_upload_photo_sends_multipart_file(client: SysAid) -> None:
    responses.post(API + "/users/1/photo", status=200)
    client.users.upload_photo(1, b"abc", filename="me.jpg")
    request = responses.calls[0].request
    assert "multipart/form-data" in request.headers["Content-Type"]
    assert isinstance(request.body, bytes)
    assert b'name="file"; filename="me.jpg"' in request.body


@responses.activate
def test_upload_photo_from_path(client: SysAid, tmp_path: Any) -> None:
    path = tmp_path / "me.png"
    path.write_bytes(b"png")
    responses.post(API + "/users/1/photo", status=200)
    client.users.upload_photo(1, path)
    body = responses.calls[0].request.body
    assert isinstance(body, bytes)
    assert b'filename="me.png"' in body


def test_upload_photo_over_limit_is_rejected_client_side(client: SysAid) -> None:
    with pytest.raises(ValueError, match="limit"):
        client.users.upload_photo(1, b"x" * (MAX_PHOTO_BYTES + 1))


@responses.activate
def test_permissions(client: SysAid) -> None:
    body = {"id": "1", "permissions": [{"key": "userPermissionUserSelfService", "value": "false"}]}
    responses.get(API + "/users/1/permission", json=body)
    responses.get(
        API + "/users/1/permission/userPermissionUserSelfService",
        json={"key": "userPermissionUserSelfService", "value": "false"},
    )
    assert client.users.permissions(1) == body
    assert client.users.permission(1, "userPermissionUserSelfService")["value"] == "false"
