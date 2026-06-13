"""Build resume context from persisted session links (no scanner/git calls)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from grafid.core.exceptions import SessionError
from grafid.db.connection import DatabaseConnection
from grafid.db.repositories.git_snapshot_repository import GitSnapshotRepository
from grafid.db.repositories.scan_finding_repository import ScanFindingRepository
from grafid.db.repositories.project_repository import ProjectRepository
from grafid.db.repositories.snapshot_repository import SnapshotRepository
from grafid.models.session import SessionResumeContext, WorkSessionRecord


class SessionResumeService:
    """Prepare linked snapshot, finding, and git data for future resume flows."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def build_context(self, session: WorkSessionRecord) -> SessionResumeContext:
        """Assemble resume preparation data from database links only."""
        try:
            with DatabaseConnection(self._db_path) as conn:
                project = ProjectRepository(conn).get_by_id(session.project_id)
                if project is None:
                    raise SessionError(f"Project not found: {session.project_id}")

                start_meta = _snapshot_summary(conn, session.snapshot_id_at_start)
                end_meta = _snapshot_summary(conn, session.snapshot_id_at_end)
        except sqlite3.Error as exc:
            raise SessionError(f"Failed to build resume context: {exc}") from exc

        return SessionResumeContext(
            session=session,
            project_name=project.name,
            project_path=project.path,
            snapshot_at_start=session.snapshot_id_at_start,
            snapshot_at_end=session.snapshot_id_at_end,
            findings_at_start=start_meta["findings"],
            findings_at_end=end_meta["findings"],
            git_branch_at_start=start_meta["branch"],
            git_branch_at_end=end_meta["branch"],
            git_dirty_at_start=start_meta["dirty"],
            git_dirty_at_end=end_meta["dirty"],
        )


def _snapshot_summary(connection: sqlite3.Connection, snapshot_id: int | None) -> dict:
    if snapshot_id is None:
        return {"findings": 0, "branch": None, "dirty": None}

    snapshot = SnapshotRepository(connection).get_by_id(snapshot_id)
    if snapshot is None:
        return {"findings": 0, "branch": None, "dirty": None}

    findings = ScanFindingRepository(connection).count_for_snapshot(snapshot_id)
    git_row = GitSnapshotRepository(connection).get_by_snapshot_id(snapshot_id)
    branch = git_row.current_branch if git_row and git_row.is_git_repo else None
    dirty = git_row.is_dirty if git_row and git_row.is_git_repo else None

    return {"findings": findings, "branch": branch, "dirty": dirty}
