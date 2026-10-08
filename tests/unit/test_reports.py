import responses
from responses.matchers import json_params_matcher, query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_operators(client: SysAid) -> None:
    responses.get(
        API + "/reports/operators",
        json=[{"type": "date", "operator": "between"}],
        match=[query_param_matcher({"type": "date"})],
    )
    assert client.reports.operators("date")[0]["operator"] == "between"


@responses.activate
def test_run_preview_passes_body_and_returns_raw(client: SysAid) -> None:
    definition = {"entity": "sr", "select": {"reportSelect": []}}
    responses.post(
        API + "/reports/allReports/72/runPreview",
        json={"rows": []},
        match=[json_params_matcher(definition)],
    )
    assert client.reports.run_preview(72, definition) == {"rows": []}
