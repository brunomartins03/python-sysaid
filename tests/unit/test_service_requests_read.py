from datetime import datetime, timezone
from typing import Any

import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_list_encodes_filters(client: SysAid, load_fixture: Any) -> None:
    responses.get(
        API + "/sr",
        json=load_fixture("sr_list.json"),
        match=[
            query_param_matcher(
                {
                    "type": "incident,request",
                    "ids": "1,2",
                    "archive": "1",
                    "status": "4,5",
                    "due_date": "1398935657000,0",
                    "fields": "title",
                    "sort": "title",
                    "dir": "desc",
                    "limit": "10",
                    "offset": "20",
                }
            )
        ],
    )
    srs = client.service_requests.list(
        type=["incident", "request"],
        ids=[1, 2],
        archive=True,
        status=[4, 5],
        due_date=(datetime.fromtimestamp(1398935657, timezone.utc), None),
        fields=["title"],
        sort="title",
        direction="desc",
        limit=10,
        offset=20,
    )
    assert srs[0].id == "5433"
    assert srs[0]["title"] == "basic Service Request"
    assert srs[0].caption("request_user") == "Leonardo Gonzalez"
    assert srs[0].raw["canUpdate"] is True


@responses.activate
def test_archive_false_is_zero(client: SysAid) -> None:
    responses.get(API + "/sr", json=[], match=[query_param_matcher({"archive": "0"})])
    assert client.service_requests.list(archive=False) == []


@responses.activate
def test_iter_pages_with_filters(client: SysAid) -> None:
    responses.get(
        API + "/sr",
        json=[{"id": "1", "info": []}, {"id": "2", "info": []}],
        match=[query_param_matcher({"status": "4", "offset": "0", "limit": "2"})],
    )
    responses.get(
        API + "/sr",
        json=[{"id": "3", "info": []}],
        match=[query_param_matcher({"status": "4", "offset": "2", "limit": "2"})],
    )
    ids = [sr.id for sr in client.service_requests.iter(status=4, page_size=2)]
    assert ids == ["1", "2", "3"]


@responses.activate
def test_get(client: SysAid) -> None:
    responses.get(
        API + "/sr/273",
        json={
            "id": "273",
            "info": [{"key": "status", "value": "2", "mandatory": "true", "type": "list"}],
        },
        match=[query_param_matcher({"fields": "status"})],
    )
    sr = client.service_requests.get(273, fields=["status"])
    assert sr.fields["status"].mandatory is True


@responses.activate
def test_search_sends_query(client: SysAid) -> None:
    responses.get(
        API + "/sr/search",
        json=[],
        match=[query_param_matcher({"query": "54", "view": "SysAidMobile", "limit": "2"})],
    )
    assert client.service_requests.search("54", view="SysAidMobile", limit=2) == []


@responses.activate
def test_count(client: SysAid) -> None:
    responses.get(
        API + "/sr/count", json={"count": 128}, match=[query_param_matcher({"computer_id": "1"})]
    )
    assert client.service_requests.count(computer_id=1) == 128


@responses.activate
def test_template(client: SysAid) -> None:
    responses.get(
        API + "/sr/template",
        json={"id": "0", "info": []},
        match=[query_param_matcher({"type": "incident", "template": "39"})],
    )
    assert client.service_requests.template(type="incident", template=39).id == "0"
