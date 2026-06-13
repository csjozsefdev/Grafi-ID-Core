"""CRUD access for git_snapshots."""

from __future__ import annotations

import json
import sqlite3

from grafid.git.models import GitState
from grafid.models.snapshot import GitSnapshotRecord
from grafid.utils.datetime_utils import utc_now_iso


def _loads_list(payload: str) -> list[str]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("Expected JSON list")
    return [str(item) for item in data]


def _loads_commits(payload: str) -> list[dict[str, str]]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("Expected JSON list")
    return data


class GitSnapshotRepository:
    """SQLite repository for Git metadata linked to scan snapshots."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def insert(self, snapshot_id: int, git_state: GitState) -> GitSnapshotRecord:
        collected_at = utc_now_iso()
        commits_payload = [
            {
                "commit_hash": commit.commit_hash,
                "subject": commit.subject,
                "author": commit.author,
                "committed_at": commit.committed_at,
            }
            for commit in git_state.latest_commits
        ]
        warning_message = "; ".join(git_state.warnings) if git_state.warnings else None

        cursor = self._conn.execute(
            """
            INSERT INTO git_snapshots (
                snapshot_id, is_git_repo, current_branch, is_detached_head,
                is_dirty, modified_files_json, staged_files_json,
                latest_commits_json, collected_at, warning_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                int(git_state.is_git_repo),
                git_state.current_branch,
                int(git_state.is_detached_head),
                int(git_state.is_dirty),
                json.dumps(list(git_state.modified_files)),
                json.dumps(list(git_state.staged_files)),
                json.dumps(commits_payload),
                collected_at,
                warning_message,
            ),
        )
        record = self.get_by_snapshot_id(snapshot_id)
        if record is None:
            raise RuntimeError("Failed to load git snapshot after insert")
        return record

    def get_by_snapshot_id(self, snapshot_id: int) -> GitSnapshotRecord | None:
        row = self._conn.execute(
            "SELECT * FROM git_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            return None
        return GitSnapshotRecord(
            id=int(row["id"]),
            snapshot_id=int(row["snapshot_id"]),
            is_git_repo=bool(row["is_git_repo"]),
            current_branch=row["current_branch"],
            is_detached_head=bool(row["is_detached_head"]),
            is_dirty=bool(row["is_dirty"]),
            modified_files=_loads_list(str(row["modified_files_json"])),
            staged_files=_loads_list(str(row["staged_files_json"])),
            latest_commits=_loads_commits(str(row["latest_commits_json"])),
            collected_at=str(row["collected_at"]),
            warning_message=row["warning_message"],
        )

    def get_latest_for_project(self, project_id: int) -> GitSnapshotRecord | None:
        row = self._conn.execute(
            """
            SELECT g.*
            FROM git_snapshots g
            INNER JOIN scan_snapshots s ON s.id = g.snapshot_id
            WHERE s.project_id = ?
            ORDER BY s.scanned_at DESC, s.id DESC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        return GitSnapshotRecord(
            id=int(row["id"]),
            snapshot_id=int(row["snapshot_id"]),
            is_git_repo=bool(row["is_git_repo"]),
            current_branch=row["current_branch"],
            is_detached_head=bool(row["is_detached_head"]),
            is_dirty=bool(row["is_dirty"]),
            modified_files=_loads_list(str(row["modified_files_json"])),
            staged_files=_loads_list(str(row["staged_files_json"])),
            latest_commits=_loads_commits(str(row["latest_commits_json"])),
            collected_at=str(row["collected_at"]),
            warning_message=row["warning_message"],
        )
