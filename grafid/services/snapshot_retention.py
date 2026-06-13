"""On-demand snapshot retention (no background daemon)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from grafid.services.retention_policy import RetentionPolicy
from grafid.utils.logging_setup import get_logger

logger = get_logger("snapshot_retention")

DEFAULT_POLICY = RetentionPolicy(max_snapshots_per_project=30, max_age_days=90)


class SnapshotRetentionService:
    """Trim old scan snapshots for one project or all projects."""

    def __init__(self, db_path: Path, *, policy: RetentionPolicy | None = None) -> None:
        self._db_path = db_path
        self._policy = policy or DEFAULT_POLICY

    def apply_for_project(self, project_id: int, *, connection: sqlite3.Connection) -> int:
        """Delete excess snapshots; return number removed."""
        if not self._policy.cleanup_enabled():
            return 0
        removed = 0
        if self._policy.max_snapshots_per_project:
            removed += self._trim_by_count(connection, project_id)
        if self._policy.max_age_days:
            removed += self._trim_by_age(connection, project_id)
        return removed

    def apply_all(self) -> int:
        from grafid.db.connection import DatabaseConnection

        total = 0
        with DatabaseConnection(self._db_path) as conn:
            rows = conn.execute("SELECT id FROM projects").fetchall()
            for row in rows:
                total += self.apply_for_project(int(row["id"]), connection=conn)
            conn.commit()
        return total

    def _trim_by_count(self, conn: sqlite3.Connection, project_id: int) -> int:
        limit = self._policy.max_snapshots_per_project
        if not limit or limit < 1:
            return 0
        rows = conn.execute(
            """
            SELECT id FROM scan_snapshots
            WHERE project_id = ?
            ORDER BY scanned_at DESC, id DESC
            """,
            (project_id,),
        ).fetchall()
        if len(rows) <= limit:
            return 0
        drop_ids = [int(r["id"]) for r in rows[limit:]]
        return self._delete_snapshots(conn, drop_ids)

    def _trim_by_age(self, conn: sqlite3.Connection, project_id: int) -> int:
        days = self._policy.max_age_days
        if not days or days < 1:
            return 0
        cursor = conn.execute(
            """
            DELETE FROM scan_snapshots
            WHERE project_id = ?
              AND scanned_at < datetime('now', ?)
            """,
            (project_id, f"-{int(days)} days"),
        )
        return cursor.rowcount

    def _delete_snapshots(self, conn: sqlite3.Connection, snapshot_ids: list[int]) -> int:
        if not snapshot_ids:
            return 0
        placeholders = ",".join("?" * len(snapshot_ids))
        cursor = conn.execute(
            f"DELETE FROM scan_snapshots WHERE id IN ({placeholders})",
            snapshot_ids,
        )
        return cursor.rowcount
