"""Settings table row model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingRecord:
    """Represents one row in the settings table."""

    id: int
    key: str
    value: str | None
    created_at: str
    updated_at: str
