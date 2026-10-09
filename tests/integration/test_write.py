"""Live tests that write: they create one SR and clean up after themselves."""

from collections.abc import Iterator
from contextlib import suppress
from datetime import datetime, timedelta, timezone

import pytest

from sysaid import BadRequestError, Record, SysAid
from sysaid._params import to_ms
from sysaid.resources.service_requests import make_note

pytestmark = [pytest.mark.integration, pytest.mark.destructive]

TITLE = "python-sysaid integration test (safe to delete)"
NOW = datetime.now(timezone.utc).replace(microsecond=0)


@pytest.fixture(scope="module")
def sr(live: SysAid, me: str) -> Iterator[Record]:
    """An incident assigned to the logged-in user; closed afterwards."""
    created = live.service_requests.create(
        type="incident", return_fields=["title", "responsibility"], title=TITLE, responsibility=me
    )
    assert created.id is not None
    yield created
    # Deleting is a disabled feature, so the SR is left closed (a 400 means it already is).
    with suppress(BadRequestError):
        live.service_requests.close(created.id, "integration test finished")


def read(live: SysAid, sr: Record, *fields: str) -> Record:
    assert sr.id is not None
    return live.service_requests.get(sr.id, fields=fields)


def test_create(sr: Record, me: str) -> None:
    assert int(sr.id or 0) > 0
    assert sr["title"] == TITLE
    assert str(sr["responsibility"]) == me


def test_update(live: SysAid, sr: Record) -> None:
    assert sr.id is not None
    due = NOW + timedelta(days=3)
    live.service_requests.update(sr.id, {"title": TITLE + " *"}, urgency=2, due_date=due)
    after = read(live, sr, "title", "urgency", "due_date")
    assert after["title"] == TITLE + " *"
    assert after["urgency"] == 2
    assert after["due_date"] == to_ms(due)


def test_notes(live: SysAid, sr: Record) -> None:
    assert sr.id is not None
    user = live.login().raw["user"]["name"]
    live.service_requests.update(sr.id, notes=[make_note(user, "a note")])
    assert "a note" in read(live, sr, "notes")["notes"][0]


def test_links(live: SysAid, sr: Record) -> None:
    assert sr.id is not None
    live.service_requests.add_link(sr.id, "docs", "https://example.com/")
    assert [link["name"] for link in read(live, sr, "links")["links"]] == ["docs"]
    live.service_requests.delete_link(sr.id, "docs")
    assert read(live, sr, "links")["links"] == []


def test_attachments(live: SysAid, sr: Record) -> None:
    assert sr.id is not None
    live.service_requests.add_attachment(sr.id, b"hello\n", "hello.txt")
    attachments = read(live, sr, "attachments")["attachments"]
    assert [item["fileName"] for item in attachments] == ["hello.txt"]
    live.service_requests.delete_attachment(sr.id, attachments[0]["fileId"])
    assert read(live, sr, "attachments")["attachments"] == []


def test_activities(live: SysAid, sr: Record, me: str) -> None:
    assert sr.id is not None
    live.service_requests.add_activity(sr.id, int(me), NOW - timedelta(minutes=30), NOW, "work")
    activities = read(live, sr, "activities")["activities"]
    assert [(item["description"], item["total"]) for item in activities] == [("work", "00:30")]
    live.service_requests.delete_activity(sr.id, activities[0]["id"])
    assert read(live, sr, "activities")["activities"] == []


def test_send_message_to_self(live: SysAid, sr: Record, me: str) -> None:
    assert sr.id is not None
    try:
        live.service_requests.send_message(
            sr.id,
            [me],
            from_user_id=me,
            cc_users=[me],
            subject="python-sysaid",
            body="test",
            add_sr_details=False,
            attachments=[b"attached\n"],
        )
    except BadRequestError as exc:
        pytest.skip(f"the logged-in user cannot receive mail: {exc}")
    after = read(live, sr, "messages", "attachments")
    message = after["messages"][-1]
    assert "python-sysaid" in message["msgSubject"]
    assert message["msgBody"].startswith("test")
    assert message["method"] == "email"
    assert message["ccUsers"]
    assert len(after["attachments"]) == 1


def test_close(live: SysAid, sr: Record) -> None:
    assert sr.id is not None
    live.service_requests.close(sr.id, "solved")
    after = read(live, sr, "solution", "close_time")
    assert after["solution"] == "solved"
    assert after["close_time"]


def test_upload_photo(live: SysAid, me: str) -> None:
    # Smallest valid GIF; it replaces the photo of the logged-in (API) user.
    photo = b"GIF89a\x01\x00\x01\x00\x00\x00\x00;"
    live.users.upload_photo(me, photo, "pixel.gif")
    assert live.users.get_photo(me) == photo


def test_addons_refresh(live: SysAid) -> None:
    live.addons.refresh()
