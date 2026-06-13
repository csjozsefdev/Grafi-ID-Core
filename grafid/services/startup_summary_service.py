"""Startup summary flow: load session, generate summary, prepare Grafi payload."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from grafid.core.exceptions import StartupError
from grafid.db.connection import DatabaseConnection
from grafid.db.repositories.project_repository import ProjectRepository
from grafid.db.repositories.session_repository import SessionRepository
from grafid.db.repositories.startup_summary_repository import StartupSummaryRepository
from grafid.models.grafi import GrafiIconState, GrafiSummaryPayload, StartupSummaryPayload
from grafid.models.startup import StartupSummaryRecord
from grafid.resume.generator import ResumeSummaryGenerator, count_open_tasks
from grafid.resume.loader import ResumeDataLoader
from grafid.resume.quality import build_headline, normalize_note, truncate_scroll_content
from grafid.runtime.passive import get_passive_runtime
from grafid.utils.logging_setup import get_logger

logger = get_logger("startup_summary")


class StartupSummaryService:
    """Orchestrate deterministic startup continuity for one primary project."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._loader = ResumeDataLoader(db_path)
        self._generator = ResumeSummaryGenerator()

    def run_flow(self, *, persist: bool = True) -> StartupSummaryPayload:
        """
        Load latest session context, build startup summary, persist, enter passive mode.

        Does not scan filesystem or call git subprocesses.
        """
        logger.info("Running startup summary flow")
        try:
            with DatabaseConnection(self._db_path) as conn:
                project = ProjectRepository(conn).get_primary_for_startup()
                if project is None:
                    return self._empty_payload(persist=persist, conn=conn)

                bundle = self._loader.load(project.id)
                active = SessionRepository(conn).get_active_for_project(project.id)
                has_unfinished = active is not None

                resume = self._generator.generate(
                    bundle, mode="short", purpose="startup"
                )
                exit_note = (
                    normalize_note(bundle.session.exit_note) if bundle.session else None
                )
                blocker = (
                    normalize_note(bundle.session.blocker) if bundle.session else None
                )
                next_step = (
                    normalize_note(bundle.session.next_step) if bundle.session else None
                )
                open_tasks = count_open_tasks(bundle.findings)

                headline = build_headline(
                    project_name=project.name,
                    exit_note=exit_note,
                    blocker=blocker,
                    next_step=next_step,
                    open_task_count=open_tasks,
                    has_unfinished_session=has_unfinished,
                )
                summary_text = headline
                scroll_content = truncate_scroll_content(resume.body, purpose="startup")

                is_empty = (
                    not has_unfinished
                    and exit_note is None
                    and blocker is None
                    and next_step is None
                    and open_tasks == 0
                )
                icon_state = _resolve_icon_state(
                    has_unfinished_session=has_unfinished,
                    exit_note=exit_note,
                    blocker=blocker,
                    next_step=next_step,
                    open_task_count=open_tasks,
                    is_empty=is_empty,
                )

                stored_id: int | None = None
                if persist:
                    record = StartupSummaryRepository(conn).insert(
                        project_id=project.id,
                        session_id=resume.session_id,
                        snapshot_id=resume.snapshot_id,
                        headline=headline,
                        summary_text=summary_text,
                        scroll_content=scroll_content,
                        grifi_icon_state=icon_state,
                    )
                    conn.commit()
                    stored_id = record.id

                grafi = GrafiSummaryPayload(
                    icon_state=icon_state,
                    summary_text=summary_text,
                    scroll_content=scroll_content,
                    is_closable=True,
                    is_dismissed=False,
                    project_id=project.id,
                    project_name=project.name,
                    startup_summary_id=stored_id,
                )

                get_passive_runtime().activate_passive_mode()

                return StartupSummaryPayload(
                    project_id=project.id,
                    project_name=project.name,
                    session_id=resume.session_id,
                    headline=headline,
                    summary_text=summary_text,
                    scroll_content=scroll_content,
                    grafi=grafi,
                    startup_summary_id=stored_id,
                    has_unfinished_session=has_unfinished,
                    is_empty=is_empty,
                )
        except StartupError:
            raise
        except sqlite3.Error as exc:
            raise StartupError(f"Startup summary flow failed: {exc}") from exc

    def dismiss_latest(self, project_id: int) -> StartupSummaryRecord | None:
        """Mark the latest startup summary as dismissed (UI close state)."""
        try:
            with DatabaseConnection(self._db_path) as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    repo = StartupSummaryRepository(conn)
                    latest = repo.get_latest_for_project(project_id)
                    if latest is None:
                        conn.commit()
                        return None
                    updated = repo.mark_dismissed(latest.id)
                    conn.commit()
                    return updated
                except Exception:
                    conn.rollback()
                    raise
        except sqlite3.Error as exc:
            raise StartupError(f"Failed to dismiss startup summary: {exc}") from exc

    def get_latest(self, project_id: int) -> StartupSummaryRecord | None:
        try:
            with DatabaseConnection(self._db_path) as conn:
                return StartupSummaryRepository(conn).get_latest_for_project(project_id)
        except sqlite3.Error as exc:
            raise StartupError(f"Failed to load startup summary: {exc}") from exc

    def _empty_payload(self, *, persist: bool, conn: sqlite3.Connection) -> StartupSummaryPayload:
        headline = "No registered projects yet"
        summary_text = headline
        scroll_content = (
            "Add a project with graf-id add <name> <path>, then run scan and session commands."
        )
        icon_state: GrafiIconState = "idle"
        stored_id: int | None = None
        if persist:
            record = StartupSummaryRepository(conn).insert(
                project_id=None,
                session_id=None,
                snapshot_id=None,
                headline=headline,
                summary_text=summary_text,
                scroll_content=scroll_content,
                grifi_icon_state=icon_state,
            )
            conn.commit()
            stored_id = record.id

        grafi = GrafiSummaryPayload(
            icon_state=icon_state,
            summary_text=summary_text,
            scroll_content=scroll_content,
            is_closable=True,
            is_dismissed=False,
            project_id=None,
            project_name=None,
            startup_summary_id=stored_id,
        )
        get_passive_runtime().activate_passive_mode()
        return StartupSummaryPayload(
            project_id=None,
            project_name=None,
            session_id=None,
            headline=headline,
            summary_text=summary_text,
            scroll_content=scroll_content,
            grafi=grafi,
            startup_summary_id=stored_id,
            has_unfinished_session=False,
            is_empty=True,
        )


def _resolve_icon_state(
    *,
    has_unfinished_session: bool,
    exit_note: str | None,
    blocker: str | None,
    next_step: str | None,
    open_task_count: int,
    is_empty: bool,
) -> GrafiIconState:
    if has_unfinished_session:
        return "attention"
    if is_empty:
        return "idle"
    if blocker or next_step or exit_note or open_task_count > 0:
        return "ready"
    return "idle"
