"""
CRUD access for startup_summaries.

Write methods do not commit — StartupSummaryService owns commits.
"""

from __future__ import annotations

import sqlite3

from grafid.models.grafi import GrafiIconState
from grafid.models.startup import StartupSummaryRecord
from grafid.utils.datetime_utils import utc_now_iso


class StartupSummaryRepository:
    """SQLite repository for startup summary history."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def insert(
        self,
        *,
        project_id: int | None,
        session_id: int | None,
        snapshot_id: int | None,
        headline: str,
        summary_text: str,
        scroll_content: str,
        grifi_icon_state: GrafiIconState,
    ) -> StartupSummaryRecord:
        generated_at = utc_now_iso()
        cursor = self._conn.execute(
            """
            INSERT INTO startup_summaries (
                project_id, session_id, snapshot_id,
                headline, summary_text, scroll_content,
                grifi_icon_state, generated_at, dismissed_at, is_dismissed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)
            """,
            (
                project_id,
                session_id,
                snapshot_id,
                headline,
                summary_text,
                scroll_content,
                grifi_icon_state,
                generated_at,
            ),
        )
        record = self.get_by_id(int(cursor.lastrowid))
        if record is None:
            raise RuntimeError("Failed to load startup summary after insert")
        return record

    def get_by_id(self, summary_id: int) -> StartupSummaryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM startup_summaries WHERE id = ?", (summary_id,)
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_latest_for_project(
        self, project_id: int
    ) -> StartupSummaryRecord | None:
        row = self._conn.execute(
            """
            SELECT * FROM startup_summaries
            WHERE project_id = ?
            ORDER BY generated_at DESC, id DESC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_latest_global(self) -> StartupSummaryRecord | None:
        row = self._conn.execute(
            """
            SELECT * FROM startup_summaries
            ORDER BY generated_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        return _row_to_record(row) if row else None

    def mark_dismissed(self, summary_id: int) -> StartupSummaryRecord | None:
        dismissed_at = utc_now_iso()
        self._conn.execute(
            """
            UPDATE startup_summaries
            SET is_dismissed = 1, dismissed_at = ?
            WHERE id = ?
            """,
            (dismissed_at, summary_id),
        )
        return self.get_by_id(summary_id)


def _row_to_record(row: sqlite3.Row) -> StartupSummaryRecord:
    return StartupSummaryRecord(
        id=int(row["id"]),
        project_id=row["project_id"],
        session_id=row["session_id"],
        snapshot_id=row["snapshot_id"],
        headline=str(row["headline"]),
        summary_text=str(row["summary_text"]),
        scroll_content=str(row["scroll_content"]),
        grifi_icon_state=str(row["grifi_icon_state"]),
        generated_at=str(row["generated_at"]),
        dismissed_at=row["dismissed_at"],
        is_dismissed=bool(row["is_dismissed"]),
    )
