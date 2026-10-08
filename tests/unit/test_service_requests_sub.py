import json
from datetime import datetime, timezone
from pathlib import Path

import responses
from responses.matchers import json_params_matcher, query_param_matcher

from sysaid import SysAid
from tests.conftest import API


@responses.activate
def test_links(client: SysAid) -> None:
    responses.post(
        API + "/sr/6/link",
        match=[json_params_matcher({"name": "link2", "link": "http://google.co.il"})],
    )
    responses.delete(API + "/sr/6/link", match=[json_params_matcher({"name": "link2"})])
    client.service_requests.add_link(6, "link2", "http://google.co.il")
    client.service_requests.delete_link(6, "link2")


@responses.activate
def test_attachments(client: SysAid, tmp_path: Path) -> None:
    path = tmp_path / "doc.pdf"
    path.write_bytes(b"%PDF")
    responses.post(API + "/sr/6/attachment")
    responses.delete(
        API + "/sr/6/attachment", match=[json_params_matcher({"fileId": "111934645_312638760"})]
    )
    client.service_requests.add_attachment(6, path)
    body = responses.calls[0].request.body
    assert isinstance(body, bytes)
    assert b'name="file"; filename="doc.pdf"' in body
    client.service_requests.delete_attachment(6, "111934645_312638760")


@responses.activate
def test_activities(client: SysAid) -> None:
    start = datetime(2013, 9, 6, 21, 0, tzinfo=timezone.utc)
    responses.post(
        API + "/sr/6/activity",
        match=[
            json_params_matcher(
                {
                    "userId": "sysaid",
                    "fromTime": 1378501200000,
                    "toTime": 1378846800000,
                    "description": "work",
                }
            )
        ],
    )
    responses.delete(API + "/sr/6/activity", match=[json_params_matcher({"id": 2})])
    client.service_requests.add_activity(6, "sysaid", start, 1378846800000, "work")
    client.service_requests.delete_activity(6, 2)


@responses.activate
def test_send_message_is_multipart_with_json_message_part(client: SysAid, tmp_path: Path) -> None:
    responses.post(
        API + "/sr/6/message",
        match=[
            query_param_matcher(
                {"method": "email", "addAttachmentToSr": "false", "addSrDetails": "true"}
            )
        ],
    )
    client.service_requests.send_message(
        6,
        [1, 140, "[3]"],
        from_user_id=124,
        cc_users="125",
        subject="Hi",
        body="Hello",
        method="email",
        add_attachment_to_sr=False,
        add_sr_details=True,
        attachments=[b"data"],
    )
    request = responses.calls[0].request
    assert "multipart/form-data" in request.headers["Content-Type"]
    assert isinstance(request.body, bytes)
    assert b'name="message"' in request.body
    message = json.dumps(
        {
            "fromUserId": "124",
            "toUsers": "1,140,[3]",
            "ccUsers": "125",
            "msgSubject": "Hi",
            "msgBody": "Hello",
        }
    )
    assert message.encode() in request.body
    assert b'name="file"; filename="file"' in request.body


@responses.activate
def test_send_message_minimal_omits_optional_keys(client: SysAid) -> None:
    responses.post(API + "/sr/6/message")
    client.service_requests.send_message(6, "1", from_user_id=2)
    body = responses.calls[0].request.body
    assert isinstance(body, bytes)
    assert b'{"fromUserId": "2", "toUsers": "1"}' in body
