"""Read-only live tests: nothing on the instance is changed."""

import os
from datetime import datetime, timezone
from itertools import islice

import pytest

from sysaid import BadRequestError, Record, ServerError, SysAid
from tests.integration.conftest import permitted

pytestmark = pytest.mark.integration


def test_login(live: SysAid) -> None:
    result = live.login()
    assert result.logged_in
    assert result.user_id
    assert result.sysaid_version
    assert result.user is not None


def test_users(live: SysAid, me: str) -> None:
    page = live.users.list(fields=["first_name"], limit=2)
    assert len(page) == 2
    assert list(page[0]) == ["first_name"]
    assert live.users.list(type="admin", fields=["first_name"], limit=1)[0].raw["isAdmin"]

    user = live.users.get(me)
    assert user.id == me
    assert "email_address" in user

    name = user.raw["name"]
    found = live.users.search(name, fields=["first_name"], sort="first_name", direction="asc")
    assert me in [item.id for item in found]


def test_users_iter_pages(live: SysAid) -> None:
    ids = [user.id for user in islice(live.users.iter(fields=["first_name"], page_size=2), 5)]
    assert len(set(ids)) == len(ids) > 2


def test_user_photo_and_permissions(live: SysAid, me: str) -> None:
    assert isinstance(live.users.get_photo(me), bytes)
    permissions = live.users.permissions(me)["permissions"]
    assert permissions
    key = permissions[0]["key"]
    assert live.users.permission(me, key) == permissions[0]


def test_filters(live: SysAid) -> None:
    filters = live.filters.list(limit=2)
    assert all(len(item["values"]) <= 2 for item in filters)
    one = live.filters.get(filters[0]["id"], limit=1)
    assert one["id"] == filters[0]["id"]
    assert one["metadata"]["limit"] == 1


def test_lists(live: SysAid) -> None:
    lists = live.lists.list(entity="sr")
    assert "status" in [item["id"] for item in lists]
    assert live.lists.get("status")["id"] == "status"
    with pytest.raises(BadRequestError):
        live.lists.get("no-such-list")


def test_service_requests_list(live: SysAid) -> None:
    page = live.service_requests.list(
        type="all", fields=["title", "status"], sort="id", direction="asc", limit=2
    )
    assert len(page) == 2
    assert sorted(page[0]) == ["status", "title"]
    assert int(page[0].id or 0) < int(page[1].id or 0)

    ids = [sr.id or "" for sr in page]
    again = live.service_requests.list(type="all", ids=ids, fields=["status"])
    assert sorted(sr.id or "" for sr in again) == sorted(ids)

    since = datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert live.service_requests.list(fields=["status"], insert_time=(since, None), limit=1)


def test_service_requests_iter_pages(live: SysAid) -> None:
    pages = live.service_requests.iter(type="all", fields=["status"], page_size=2)
    ids = [sr.id for sr in islice(pages, 5)]
    assert len(set(ids)) == len(ids) > 2


def test_service_request_get_search_count(live: SysAid) -> None:
    first = live.service_requests.list(type="all", fields=["title"], limit=1)[0]
    assert first.id is not None

    form = live.service_requests.get(first.id, fields=["title", "status"])
    assert form["title"] == first["title"]
    assert form.fields["status"].type == "list"
    assert form.caption("status")

    assert isinstance(live.service_requests.search("a", type="all", limit=1), list)
    total = live.service_requests.count(type="all")
    assert total >= live.service_requests.count(type="incident") >= 0

    with pytest.raises(BadRequestError):
        live.service_requests.get(999999999)


def test_service_request_template(live: SysAid) -> None:
    template = live.service_requests.template(type="incident")
    assert template.id == "0"
    assert template.fields["title"].editable is True


def test_action_items(live: SysAid) -> None:
    assert live.action_items.count() >= 0
    try:
        items = live.action_items.list(limit=2)
    except ServerError as exc:
        # Seen on 24.4.60 when the count is 0: HTTP 500 instead of an empty list.
        pytest.xfail(f"server could not list action items: {exc}")
    assert all(isinstance(item, Record) for item in items)


def test_assets(live: SysAid) -> None:
    with permitted():
        assets = live.assets.list(limit=2)
        assert isinstance(live.assets.search("a", limit=1), list)
        if assets:
            asset_id = assets[0].id
            assert asset_id is not None
            assert live.assets.get(asset_id).id == asset_id


def test_cis(live: SysAid) -> None:
    with permitted():
        cis = live.cis.list(limit=2)
        types = live.cis.types()
        assert isinstance(live.cis.relation_types(), list)
        if types:
            live.cis.view_fields(types[0]["id"])
        if cis:
            ci_id = cis[0].id
            assert ci_id is not None
            assert isinstance(live.cis.relations(ci_id), list)


def test_addons(live: SysAid) -> None:
    addons = live.addons.list()
    assert all("name" in addon for addon in addons)
    if addons:
        with permitted():
            assert live.addons.get(addons[0]["name"])["name"] == addons[0]["name"]


def test_resource_bundle(live: SysAid) -> None:
    assert live.resource_bundle.translate(["sr.status"])["sr.status"]
    assert live.resource_bundle.translate(["sr.status"], "en") == {"sr.status": "Status"}


def test_password_services_need_no_login() -> None:
    with SysAid(os.environ["SYSAID_URL"]) as anonymous:
        assert isinstance(anonymous.password_services.domains(), list)
        assert "enableResetPassword" in anonymous.password_services.permissions()


def test_report_operators(live: SysAid) -> None:
    with permitted():
        assert live.reports.operators("string")
