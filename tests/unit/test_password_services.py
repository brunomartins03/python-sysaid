import pytest
import responses
from responses.matchers import json_params_matcher

from sysaid import SysAid
from tests.conftest import API

QUESTIONS = [{"id": 1, "question": "City?", "answer": "Rio"}]


@responses.activate
def test_calls_work_without_login() -> None:
    client = SysAid("https://sysaid.test", username="u", password="p")
    responses.get(API + "/ps/domain", json=["QA-LAB"])
    responses.get(API + "/ps/permission", json={"enableResetPassword": True})
    assert client.password_services.domains() == ["QA-LAB"]
    assert client.password_services.permissions()["enableResetPassword"] is True
    assert len(responses.calls) == 2  # no /login


@responses.activate
def test_questions(client: SysAid) -> None:
    responses.post(
        API + "/ps/reset/question",
        json={"userRefId": 842},
        match=[json_params_matcher({"userName": "test11", "domainName": "QA-LAB"})],
    )
    assert client.password_services.questions("reset", "test11", "QA-LAB")["userRefId"] == 842


def test_questions_rejects_unknown_method(client: SysAid) -> None:
    with pytest.raises(ValueError):
        client.password_services.questions("delete", "x")


@responses.activate
def test_unlock_reset_update(client: SysAid) -> None:
    body = {"userRefId": 842, "userSecurityQuestionsList": QUESTIONS}
    responses.post(
        API + "/ps/unlock", json={"actionMessage": "ok"}, match=[json_params_matcher(body)]
    )
    responses.post(API + "/ps/reset", json={"token": "t"}, match=[json_params_matcher(body)])
    responses.post(
        API + "/ps/reset/update",
        json={"actionMessage": "done"},
        match=[json_params_matcher({"userRefId": 842, "newPassword": "N#1", "token": "t"})],
    )
    assert client.password_services.unlock(842, QUESTIONS)["actionMessage"] == "ok"
    assert client.password_services.reset(842, QUESTIONS)["token"] == "t"
    assert client.password_services.update_password(842, "N#1", "t")["actionMessage"] == "done"
