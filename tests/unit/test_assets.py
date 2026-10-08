import responses
from responses.matchers import query_param_matcher

from sysaid import SysAid
from tests.conftest import API

ASSET_ID = "497db453:147bee7ec09:-7ff2"
ASSET = {
    "id": ASSET_ID,
    "name": "ISA-VCHER-DW7",
    "group": "\\",
    "info": [
        {
            "key": "computer_type",
            "key_caption": "Type",
            "value": "Workstation",
            "value_caption": "WS",
        }
    ],
}


@responses.activate
def test_list(client: SysAid) -> None:
    responses.get(
        API + "/asset",
        json=[ASSET],
        match=[query_param_matcher({"fields": "computer_type", "type": "x", "limit": "2"})],
    )
    assets = client.assets.list(fields=["computer_type"], type="x", limit=2)
    assert assets[0].id == ASSET_ID
    assert assets[0]["computer_type"] == "Workstation"
    assert assets[0].caption("computer_type") == "WS"
    assert assets[0].raw["name"] == "ISA-VCHER-DW7"


@responses.activate
def test_get_url_encodes_colons(client: SysAid) -> None:
    responses.get(API + "/asset/497db453%3A147bee7ec09%3A-7ff2", json=ASSET)
    assert client.assets.get(ASSET_ID).id == ASSET_ID
    assert "%3A" in str(responses.calls[0].request.url)


@responses.activate
def test_search_and_iter(client: SysAid) -> None:
    responses.get(
        API + "/asset/search", json=[ASSET], match=[query_param_matcher({"query": "DW7"})]
    )
    responses.get(
        API + "/asset", json=[ASSET], match=[query_param_matcher({"offset": "0", "limit": "5"})]
    )
    assert client.assets.search("DW7")[0].id == ASSET_ID
    assert [a.id for a in client.assets.iter(page_size=5)] == [ASSET_ID]
