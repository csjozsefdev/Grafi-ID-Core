"""Startup summary persistence models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StartupSummaryRecord:
    """One persisted startup summary row."""

    id: int
    project_id: int | None
    session_id: int | None
    snapshot_id: int | None
    headline: str
    summary_text: str
    scroll_content: str
    grifi_icon_state: str
    generated_at: str
    dismissed_at: str | None
    is_dismissed: bool
