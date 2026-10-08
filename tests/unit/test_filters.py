from typing import Any

import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_list(client: SysAid, load_fixture: Any) -> None:
    responses.get(
        API + "/filters",
        json=load_fixture("filters.json"),
        match=[query_param_matcher({"fields": "values", "limit": "20"})],
    )
    filters = client.filters.list(fields=["values"], limit=20)
    assert filters[0]["id"] == "status"
    assert filters[0]["values"][0]["caption"] == "closed"


@responses.activate
def test_get(client: SysAid, load_fixture: Any) -> None:
    responses.get(
        API + "/filters/status",
        json=load_fixture("filters.json")[0],
        match=[query_param_matcher({"view": "SysAidMobile"})],
    )
    assert client.filters.get("status", view="SysAidMobile")["metadata"]["total"] == "2"
