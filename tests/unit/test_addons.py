import responses
from responses.matchers import json_params_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_list_get_refresh_use_plural(client: SysAid) -> None:
    responses.get(API + "/addons", json=[{"name": "bomgar", "active": True}])
    responses.get(API + "/addons/bomgar", json={"name": "bomgar", "params": [{"name": "p"}]})
    responses.get(API + "/addons/refresh", body="Refreshed")
    assert client.addons.list()[0]["name"] == "bomgar"
    assert client.addons.get("bomgar")["params"][0]["name"] == "p"
    assert client.addons.refresh() == "Refreshed"


@responses.activate
def test_update_and_test_use_singular(client: SysAid) -> None:
    body = {
        "name": "bomgar",
        "active": True,
        "params": [{"name": "bomgar_url", "value": "https://sysaid.bomgar.com"}],
    }
    responses.put(API + "/addons/bomgar", body="Saved", match=[json_params_matcher(body)])
    responses.put(
        API + "/addons/bomgar/testConnection", body="Connected", match=[json_params_matcher(body)]
    )
    params = {"bomgar_url": "https://sysaid.bomgar.com"}
    assert client.addons.update("bomgar", active=True, params=params) == "Saved"
    assert client.addons.test_connection("bomgar", active=True, params=params) == "Connected"


@responses.activate
def test_update_only_sends_given_keys(client: SysAid) -> None:
    responses.put(API + "/addons/x", match=[json_params_matcher({"name": "x", "active": False})])
    client.addons.update("x", active=False)
