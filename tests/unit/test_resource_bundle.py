import responses
from responses.matchers import json_params_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_translate_default_and_locale(client: SysAid) -> None:
    responses.post(
        API + "/rb",
        json=[{"key": "dir", "value": "LTR"}],
        match=[json_params_matcher([{"key": "dir"}])],
    )
    responses.post(API + "/rb/pt_BR", json=[{"key": "dir", "value": "ltr-br"}])
    assert client.resource_bundle.translate(["dir"]) == {"dir": "LTR"}
    assert client.resource_bundle.translate(["dir"], locale="pt_BR") == {"dir": "ltr-br"}
