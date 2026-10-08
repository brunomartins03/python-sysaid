from sysaid import Record


def test_record_value_and_caption() -> None:
    record = Record(
        {
            "id": 5433,
            "canUpdate": "true",
            "info": [
                {"key": "title", "keyCaption": "Title", "value": "T", "valueCaption": "Cap"},
                {"key": "status", "value": "2"},
            ],
        }
    )
    assert record.id == "5433"
    assert record["title"] == "T"
    assert record.caption("title") == "Cap"
    assert record.fields["title"].key_caption == "Title"
    assert record.get("missing") is None
    assert "status" in record
    assert dict(record) == {"title": "T", "status": "2"}
    assert record.raw["canUpdate"] == "true"


def test_record_accepts_snake_case_captions() -> None:
    record = Record(
        {"id": "x", "info": [{"key": "k", "key_caption": "K", "value": 1, "value_caption": "one"}]}
    )
    assert record.fields["k"].key_caption == "K"
    assert record.caption("k") == "one"


def test_form_metadata_is_parsed() -> None:
    record = Record(
        {
            "id": "0",
            "info": [
                {
                    "key": "title",
                    "mandatory": "true",
                    "editable": False,
                    "type": "text",
                    "defaultValue": "d",
                }
            ],
        }
    )
    field = record.fields["title"]
    assert (field.mandatory, field.editable, field.type, field.default_value) == (
        True,
        False,
        "text",
        "d",
    )


def test_record_without_info() -> None:
    record = Record({"id": "24", "tabName": "1"})
    assert len(record) == 0
    assert record.raw["tabName"] == "1"
