import pytest
import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_list(client: SysAid) -> None:
    responses.get(
        API + "/action_item",
        json=[{"id": "24", "tabName": "1", "hasApproved": "true"}],
        match=[
            query_param_matcher(
                {
                    "type": "all",
                    "ids": "5,6",
                    "status": "active",
                    "staticFilterId": "f1",
                    "query": "x",
                    "archive": "0",
                    "limit": "10",
                }
            )
        ],
    )
    items = client.action_items.list(
        type="all",
        ids=[5, 6],
        status="active",
        static_filter_id="f1",
        text="x",
        archive=False,
        limit=10,
    )
    assert items[0].id == "24"
    assert items[0].raw["hasApproved"] == "true"


@responses.activate
def test_iter(client: SysAid) -> None:
    responses.get(
        API + "/action_item",
        json=[{"id": "1"}],
        match=[query_param_matcher({"offset": "0", "limit": "2"})],
    )
    assert [i.id for i in client.action_items.iter(page_size=2)] == ["1"]


@responses.activate
def test_count(client: SysAid) -> None:
    responses.get(
        API + "/action_item/count",
        json={"count": 24},
        match=[query_param_matcher({"status": "19"})],
    )
    assert client.action_items.count(status=19) == 24


@pytest.mark.parametrize("action", ["approve", "reject", "complete", "reopen"])
@responses.activate
def test_state_changes_put_with_empty_body(client: SysAid, action: str) -> None:
    responses.put(API + f"/action_item/24/{action}")
    getattr(client.action_items, action)(24)
    request = responses.calls[0].request
    assert request.method == "PUT"
    assert request.body is None
