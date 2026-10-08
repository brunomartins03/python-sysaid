import json
from datetime import datetime, timezone

import pytest
import responses
from responses.matchers import json_params_matcher, query_param_matcher

from sysaid import SysAid
from sysaid.resources.service_requests import make_note, problem_type
from tests.conftest import API

T = datetime(2014, 2, 7, 6, 40, 38, tzinfo=timezone.utc)
T_MS = 1391755238000


@responses.activate
def test_create(client: SysAid) -> None:
    responses.post(
        API + "/sr",
        json={"id": "45", "info": [{"key": "status", "value": "2"}]},
        match=[
            query_param_matcher({"type": "incident", "template": "39", "fields": "status"}),
            json_params_matcher(
                {
                    "info": [
                        {"key": "due_date", "value": T_MS},
                        {"key": "status", "value": 2},
                        {"key": "problem_type", "value": "A_B_C"},
                    ]
                }
            ),
        ],
    )
    sr = client.service_requests.create(
        {"status": 2},
        type="incident",
        template=39,
        return_fields=["status"],
        due_date=T,
        problem_type=problem_type("A", "B", "C"),
    )
    assert sr.id == "45"


@responses.activate
def test_create_with_clashing_field_id_via_mapping(client: SysAid) -> None:
    responses.post(API + "/sr", json={"id": "1", "info": []})
    client.service_requests.create({"type": 3}, type="incident")
    sent = json.loads(responses.calls[0].request.body or "{}")
    assert sent == {"info": [{"key": "type", "value": 3}]}


@responses.activate
def test_update_builds_key_value_info(client: SysAid) -> None:
    responses.put(
        API + "/sr/273",
        match=[
            json_params_matcher(
                {
                    "id": "273",
                    "info": [
                        {"key": "status", "value": 2},
                        {"key": "responsibility", "value": 66},
                        {
                            "key": "notes",
                            "value": [{"userName": "sysaid", "createDate": T_MS, "text": "Note"}],
                        },
                    ],
                }
            )
        ],
    )
    client.service_requests.update(
        273, status=2, responsibility=66, notes=[make_note("sysaid", "Note", T)]
    )


@responses.activate
def test_close(client: SysAid) -> None:
    responses.put(API + "/sr/273/close", match=[json_params_matcher({"solution": "restarted"})])
    client.service_requests.close(273, solution="restarted")


@responses.activate
def test_delete_many_and_one(client: SysAid) -> None:
    responses.delete(API + "/sr", match=[query_param_matcher({"ids": "1,2"})])
    responses.delete(API + "/sr", match=[query_param_matcher({"ids": "3"})])
    client.service_requests.delete([1, 2])
    client.service_requests.delete(3)


def test_problem_type_validates_levels() -> None:
    assert problem_type("A") == "A"
    with pytest.raises(ValueError):
        problem_type()
    with pytest.raises(ValueError):
        problem_type("a", "b", "c", "d")


def test_make_note_defaults_to_now() -> None:
    note = make_note("u", "t")
    assert isinstance(note["createDate"], datetime)
