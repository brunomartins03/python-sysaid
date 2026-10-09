"""Light wrappers around the ``{id, info[]}`` objects returned by SysAid."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    return None


@dataclass(frozen=True)
class Field:
    """One ``info`` entry. Metadata is only present on form and template calls."""

    key: str
    value: Any = None
    key_caption: str | None = None
    value_caption: Any = None
    mandatory: bool | None = None
    editable: bool | None = None
    type: str | None = None
    default_value: Any = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Field:
        """Build from one ``info`` entry (accepts both caption spellings)."""
        # Assets use snake_case captions, everything else camelCase.
        return cls(
            key=str(data["key"]),
            value=data.get("value"),
            key_caption=data.get("keyCaption", data.get("key_caption")),
            value_caption=data.get("valueCaption", data.get("value_caption")),
            mandatory=_as_bool(data.get("mandatory")),
            editable=_as_bool(data.get("editable")),
            type=data.get("type"),
            default_value=data.get("defaultValue"),
        )


class Record(Mapping[str, Any]):
    """An entity with an ``id`` and an ``info`` array, read like a mapping of key -> value."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self.raw: dict[str, Any] = dict(raw)
        self.fields: dict[str, Field] = {
            field.key: field for field in map(Field.from_dict, self.raw.get("info") or [])
        }

    @property
    def id(self) -> str | None:
        """The record id as a string, if present."""
        value = self.raw.get("id")
        return None if value is None else str(value)

    def __getitem__(self, key: str) -> Any:
        return self.fields[key].value

    def __iter__(self) -> Iterator[str]:
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)

    def caption(self, key: str) -> Any:
        """Display value (``valueCaption``) of a field."""
        return self.fields[key].value_caption

    def __repr__(self) -> str:
        return f"Record(id={self.id!r}, fields={list(self.fields)!r})"
