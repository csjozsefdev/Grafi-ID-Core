"""UTC timestamp helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()
