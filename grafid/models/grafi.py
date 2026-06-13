"""Grafi startup UI payload models (data layer only; no rendering)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

GrafiIconState = Literal["idle", "attention", "ready", "paused"]


@dataclass(frozen=True)
class GrafiSummaryPayload:
    """
    Lightweight structure for a future Tauri/desktop UI layer.

    All fields are derived from stored local data only.
    """

    icon_state: GrafiIconState
    summary_text: str
    scroll_content: str
    is_closable: bool
    is_dismissed: bool
    project_id: int | None
    project_name: str | None
    startup_summary_id: int | None


@dataclass(frozen=True)
class StartupSummaryPayload:
    """Full startup flow output for CLI and future UI consumers."""

    project_id: int | None
    project_name: str | None
    session_id: int | None
    headline: str
    summary_text: str
    scroll_content: str
    grafi: GrafiSummaryPayload
    startup_summary_id: int | None
    has_unfinished_session: bool
    is_empty: bool


@dataclass(frozen=True)
class PassiveRuntimeInfo:
    """Explains post-startup passive behavior (no background monitoring)."""

    is_passive: bool
    monitoring_enabled: bool
    ai_enabled: bool
    message: str
