from typing import Any

import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_list(client: SysAid, load_fixture: Any) -> None:
    responses.get(
        API + "/list",
        json=load_fixture("lists.json"),
        match=[query_param_matcher({"entity": "ci", "fields": "id,caption"})],
    )
    lists = client.lists.list(entity="ci", fields=["id", "caption"])
    assert lists[0]["values"][1]["id"] == "2"


@responses.activate
def test_get_uses_camel_case_params(client: SysAid) -> None:
    responses.get(
        API + "/list/responsibility",
        json={"id": "responsibility", "values": []},
        match=[
            query_param_matcher({"entity": "sr", "entityId": "6", "entityType": "3", "key": "name"})
        ],
    )
    result = client.lists.get("responsibility", entity="sr", entity_id=6, entity_type=3, key="name")
    assert result["id"] == "responsibility"
