"""Encoding of Python values into SysAid query parameters and JSON bodies."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote


def to_ms(value: datetime) -> int:
    """Milliseconds since the epoch, UTC. Naive datetimes are taken as UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return round(value.timestamp() * 1000)


def _is_date_range(value: tuple[Any, ...]) -> bool:
    return (
        len(value) == 2
        and all(item is None or isinstance(item, datetime) for item in value)
        and any(item is not None for item in value)
    )


def encode_value(value: Any) -> str:
    """Encode one query value.

    ``bool`` -> ``"true"``/``"false"``; ``datetime`` -> ms; a list or tuple -> CSV;
    a ``(from, to)`` tuple of datetimes (``None`` = open end) -> ``"from,to"`` with ``0``
    for the open end.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return str(to_ms(value))
    if isinstance(value, tuple) and _is_date_range(value):
        return ",".join("0" if item is None else str(to_ms(item)) for item in value)
    if isinstance(value, (list, tuple)):
        return ",".join(encode_value(item) for item in value)
    return str(value)


def build_params(params: Mapping[str, Any]) -> dict[str, str]:
    """Encode query parameters, dropping those whose value is ``None``."""
    return {key: encode_value(value) for key, value in params.items() if value is not None}


def encode_json(value: Any) -> Any:
    """Recursively convert datetimes in a JSON body to ms-epoch integers."""
    if isinstance(value, datetime):
        return to_ms(value)
    if isinstance(value, Mapping):
        return {key: encode_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode_json(item) for item in value]
    return value


def encode_info(fields: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build the ``info`` array of ``{key, value}`` objects used by write calls.

    The server only accepts scalar values as strings (a JSON number is answered with
    HTTP 500), so numbers, booleans and datetimes are sent as text. Structured values
    such as ``notes`` keep their JSON shape.
    """
    return [
        {
            "key": key,
            "value": encode_value(value)
            if isinstance(value, (int, float, datetime))
            else encode_json(value),
        }
        for key, value in fields.items()
    ]


def quote_segment(value: object) -> str:
    """Percent-encode one URL path segment (asset ids contain ``:``)."""
    return quote(str(value), safe="")
