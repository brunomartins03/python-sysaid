from datetime import datetime, timedelta, timezone

from sysaid._params import build_params, encode_info, encode_json, encode_value, quote_segment

T = datetime(2014, 5, 1, 9, 54, 17, tzinfo=timezone.utc)
T_MS = 1398938057000


def test_bool_is_lowercase_word() -> None:
    assert encode_value(True) == "true"
    assert encode_value(False) == "false"


def test_datetime_is_ms_utc() -> None:
    assert encode_value(T) == str(T_MS)
    assert encode_value(T.replace(tzinfo=None)) == str(T_MS)
    local = T.astimezone(timezone(timedelta(hours=-3)))
    assert encode_value(local) == str(T_MS)


def test_sequences_are_csv() -> None:
    assert encode_value([4, 5]) == "4,5"
    assert encode_value(("a", "b")) == "a,b"


def test_date_range_tuple() -> None:
    assert encode_value((T, T)) == f"{T_MS},{T_MS}"
    assert encode_value((T, None)) == f"{T_MS},0"
    assert encode_value((None, T)) == f"0,{T_MS}"


def test_build_params_drops_none_and_encodes() -> None:
    params = build_params({"a": None, "status": [4, 5], "archive": True, "n": 0})
    assert params == {"status": "4,5", "archive": "true", "n": "0"}


def test_encode_info_sends_scalars_as_strings() -> None:
    fields = {"status": 2, "due_date": T, "flag": True, "title": "x"}
    assert encode_info(fields) == [
        {"key": "status", "value": "2"},
        {"key": "due_date", "value": str(T_MS)},
        {"key": "flag", "value": "true"},
        {"key": "title", "value": "x"},
    ]


def test_encode_info_converts_nested_datetimes() -> None:
    info = encode_info({"notes": [{"userName": "u", "createDate": T, "text": "t"}]})
    assert info == [
        {"key": "notes", "value": [{"userName": "u", "createDate": T_MS, "text": "t"}]},
    ]
    assert encode_json({"d": T}) == {"d": T_MS}


def test_quote_segment_encodes_colons_and_slashes() -> None:
    assert quote_segment("497db453:147bee7ec09:-7ff2") == "497db453%3A147bee7ec09%3A-7ff2"
    assert quote_segment("a/b") == "a%2Fb"
