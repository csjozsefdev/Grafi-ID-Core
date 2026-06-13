"""Startup card and resume preview IPC for the Grafi bubble UI."""

from __future__ import annotations

from typing import Any

from grafid.config.manager import ConfigManager
from grafid.core.exceptions import GrafIdError, ProjectError, StartupError
from grafid.db.connection import DatabaseConnection
from grafid.db.repositories.project_repository import ProjectRepository
from grafid.db.repositories.startup_summary_repository import StartupSummaryRepository
from grafid.ipc.dashboard_handlers import _build_dashboard_item, _build_resume_panel, _item_and_resume_panel
from grafid.ipc.envelope import IpcResponse, failure, success
from grafid.ipc.handlers import _error_code, _startup_summary_to_dict
from grafid.models.grafi import StartupSummaryPayload
from grafid.models.startup import StartupSummaryRecord
from grafid.observability.journal import record_event
from grafid.services.startup_summary_service import StartupSummaryService


def build_startup_card(
    db_path,
    summary: StartupSummaryPayload | None,
    *,
    record: StartupSummaryRecord | None = None,
) -> dict[str, Any]:
    """Merge startup summary payload with resume preview fields for the UI card."""
    if summary is None:
        return {
            "visible": False,
            "is_dismissed": True,
            "reason": "missing_summary",
            "message": "No startup summary available.",
        }

    if summary.project_id is None:
        return {
            "visible": False,
            "is_dismissed": True,
            "reason": "empty_project",
            "message": "Register a project to see startup continuity.",
            "is_empty": True,
        }

    project_id = summary.project_id
    is_dismissed = record.is_dismissed if record else summary.grafi.is_dismissed

    with DatabaseConnection(db_path) as conn:
        project = ProjectRepository(conn).get_by_id(project_id)
        if project is None:
            return {
                "visible": False,
                "is_dismissed": True,
                "reason": "project_missing",
                "message": "Startup project no longer exists in the registry.",
            }
        dash_item, resume_panel = _item_and_resume_panel(conn, db_path, project, project_id)
    scroll = _safe_text(summary.scroll_content)
    if not scroll:
        startup_block = resume_panel.get("startup_summary") or {}
        scroll = (
            startup_block.get("scroll_excerpt")
            or startup_block.get("summary_text")
            or summary.summary_text
            or ""
        )
    if not scroll:
        scroll = "No previous session summary found."

    last_opened = dash_item.get("last_opened_at")
    latest_session = dash_item.get("latest_session")

    startup_block = resume_panel.get("startup_summary") or {}
    headline = _safe_text(summary.headline) or "Where you left off"
    summary_text = _safe_text(summary.summary_text) or ""
    if startup_block.get("headline"):
        headline = _safe_text(startup_block.get("headline")) or headline
    if startup_block.get("summary_text"):
        summary_text = _safe_text(startup_block.get("summary_text")) or summary_text

    return {
        "visible": not is_dismissed,
        "is_dismissed": is_dismissed,
        "reason": None,
        "message": None,
        "project_id": project_id,
        "project_name": summary.project_name,
        "startup_summary_id": summary.startup_summary_id,
        "session_id": summary.session_id,
        "icon_state": summary.grafi.icon_state,
        "headline": headline,
        "summary_text": summary_text,
        "scroll_content": scroll,
        "has_unfinished_session": summary.has_unfinished_session,
        "is_empty": summary.is_empty,
        "latest_session": latest_session,
        "last_opened_at": last_opened,
        "open_task_count": resume_panel.get("open_task_count"),
        "latest_scan_at": resume_panel.get("latest_scan_at"),
        "blocker": resume_panel.get("blocker"),
        "next_step": resume_panel.get("next_step"),
        "exit_note": resume_panel.get("exit_note"),
        "modified_files": resume_panel.get("modified_files") or [],
        "git_status": resume_panel.get("git_status"),
        "startup_summary": resume_panel.get("startup_summary"),
    }


def handle_resume_preview(
    project_id: int,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Resume preview for startup card refresh (reuses dashboard resume panel builder)."""
    try:
        from grafid.cli.runtime import prepare_runtime
        from grafid.ipc.dashboard_handlers import _resolve_by_id

        runtime = prepare_runtime(config_manager)
        project = _resolve_by_id(runtime.registry, project_id)
        with DatabaseConnection(runtime.database_path) as conn:
            _dash_item, resume_panel = _item_and_resume_panel(
                conn, runtime.database_path, project, project_id
            )
        return success({"resume_preview": resume_panel})
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_dismiss_startup(
    project_id: int,
    startup_summary_id: int | None = None,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Persist dismissed state for the startup summary card."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        from grafid.ipc.dashboard_handlers import _resolve_by_id

        _resolve_by_id(runtime.registry, project_id)
        service = StartupSummaryService(runtime.database_path)

        if startup_summary_id is not None:
            updated = _dismiss_by_id(runtime.database_path, startup_summary_id, project_id)
        else:
            updated = service.dismiss_latest(project_id)

        mgr = config_manager or ConfigManager()
        cfg = mgr.load()
        if updated is None:
            record_event(
                "ipc.dismiss_startup",
                config_dir=mgr.config_dir,
                config=cfg,
                project_id=project_id,
                dismissed=False,
            )
            return success(
                {
                    "dismissed": False,
                    "message": "No startup summary found to dismiss.",
                    "project_id": project_id,
                }
            )

        record_event(
            "ipc.dismiss_startup",
            config_dir=mgr.config_dir,
            config=cfg,
            project_id=project_id,
            startup_summary_id=updated.id,
            dismissed=True,
        )
        return success(
            {
                "dismissed": True,
                "startup_summary_id": updated.id,
                "project_id": project_id,
                "is_dismissed": updated.is_dismissed,
            }
        )
    except StartupError as exc:
        return failure("startup_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_startup_card(config_manager: ConfigManager | None = None) -> IpcResponse:
    """Load or build startup card data for the primary project (after runtime init)."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        service = StartupSummaryService(runtime.database_path)
        summary_payload = service.run_flow(persist=True)
        record: StartupSummaryRecord | None = None
        if summary_payload.project_id is not None:
            record = service.get_latest(summary_payload.project_id)
        card = build_startup_card(
            runtime.database_path, summary_payload, record=record
        )
        return success(
            {
                "startup_card": card,
                "startup_summary": _startup_summary_to_dict(
                    summary_payload, record=record
                ),
            }
        )
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def _dismiss_by_id(db_path, summary_id: int, project_id: int) -> StartupSummaryRecord | None:
    with DatabaseConnection(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            repo = StartupSummaryRepository(conn)
            row = repo.get_by_id(summary_id)
            if row is None or row.project_id != project_id:
                conn.commit()
                return None
            updated = repo.mark_dismissed(summary_id)
            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            raise


def _safe_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())
