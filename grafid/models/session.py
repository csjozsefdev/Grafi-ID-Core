"""Work session models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkSessionRecord:
    """One persisted developer work session."""

    id: int
    project_id: int
    started_at: str
    ended_at: str | None
    exit_note: str | None
    blocker: str | None
    next_step: str | None
    snapshot_id_at_start: int | None
    snapshot_id_at_end: int | None
    created_at: str
    updated_at: str
    status: str
    summary: str | None

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.ended_at is None


@dataclass(frozen=True)
class ExitNoteInput:
    """Optional notes provided when ending a session."""

    exit_note: str | None = None
    blocker: str | None = None
    next_step: str | None = None


@dataclass(frozen=True)
class SessionResumeContext:
    """Linked state prepared for a future resume engine."""

    session: WorkSessionRecord
    project_name: str
    project_path: str
    snapshot_at_start: int | None
    snapshot_at_end: int | None
    findings_at_start: int
    findings_at_end: int
    git_branch_at_start: str | None
    git_branch_at_end: str | None
    git_dirty_at_start: bool | None
    git_dirty_at_end: bool | None


@dataclass(frozen=True)
class SessionStatusView:
    """Summary shown by session status CLI."""

    project_name: str
    has_active_session: bool
    active_session: WorkSessionRecord | None
    has_unfinished_session: bool
    last_ended_session: WorkSessionRecord | None
