"""Dashboard IPC — aggregate existing DB/services for the desktop UI."""

from __future__ import annotations

from typing import Any

from grafid.resume.models import ResumeSummaryRecord
from grafid.models.startup import StartupSummaryRecord

from grafid.config.manager import ConfigManager
from grafid.core.exceptions import GrafIdError, ProjectError, ValidationError
from grafid.db.connection import DatabaseConnection
from grafid.db.repositories.git_snapshot_repository import GitSnapshotRepository
from grafid.db.repositories.scan_finding_repository import ScanFindingRepository
from grafid.db.repositories.session_repository import SessionRepository
from grafid.db.repositories.snapshot_repository import SnapshotRepository
from grafid.db.repositories.startup_summary_repository import StartupSummaryRepository
from grafid.ipc.envelope import IpcResponse, failure, success
from grafid.ipc.handlers import _error_code, _project_to_dict
from grafid.models.session import WorkSessionRecord
from grafid.models.snapshot import GitSnapshotRecord, SnapshotHistoryEntry
from grafid.resume.generator import count_open_tasks
from grafid.resume.summary_engine import SummaryEngine
from grafid.resume.human_display import humanize_stored_body, pick_headline_from_body
from grafid.resume.quality import normalize_note
from grafid.utils.logging_setup import get_logger

logger = get_logger("ipc.dashboard")
from grafid.resume.session_signals import resolve_summary_session_fields
from grafid.resume.workflow_artifacts import load_workflow_artifacts
from grafid.services.project_registry import ProjectRegistryService
from grafid.services.resume_service import ResumeService
from grafid.services.snapshot_persistence import SnapshotPersistenceService
from grafid.services.startup_summary_service import StartupSummaryService
from grafid.services.workflow_launch import WorkflowLaunchError, WorkflowLaunchService

RESUME_EXCERPT_CHARS = 400
MODIFIED_FILES_LIMIT = 5
HISTORY_LIMIT_DEFAULT = 15

ALLOWED_SCAN_MARKERS = frozenset({"TODO", "FIXME", "BUG", "NEXT", "HACK"})
TASK_MARKER_PREVIEW_LIMIT = 3


def _top_task_marker_lines(db_path, project_id: int, limit: int = TASK_MARKER_PREVIEW_LIMIT) -> tuple[str, ...]:
    """Clean, grouped lines from latest scan markers (not raw code fragments)."""
    from grafid.scanner.marker_quality import format_markers_for_summary
    from grafid.scanner.models import TaskFinding

    with DatabaseConnection(db_path) as conn:
        entries = SnapshotRepository(conn).list_history_for_project(project_id, limit=1)
        if not entries:
            return ()
        raw = ScanFindingRepository(conn).list_for_snapshot(entries[0].snapshot_id)

    findings: list[TaskFinding] = []
    seen: set[tuple[str, int, str]] = set()
    for row in raw:
        if row.marker not in ALLOWED_SCAN_MARKERS:
            continue
        key = (row.file_path, row.line_number, row.marker)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            TaskFinding(
                file_path=row.file_path,
                line_number=row.line_number,
                marker=row.marker,
                text=row.text,
                severity="low",
                created_at="",
            )
        )

    return format_markers_for_summary(findings, limit=limit, low_confidence=False)


def _build_human_summary_block(
    item: dict[str, Any],
    db_path,
    *,
    timeline_sessions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Human-facing summary for dashboard/resume panel (unified SummaryEngine)."""
    session = item.get("latest_session") or {}
    project_id = int(item["id"])
    with DatabaseConnection(db_path) as conn:
        session_signals = resolve_summary_session_fields(conn, project_id)
    git = item.get("git_status") or {}
    git_label = git.get("label")
    if git.get("branch"):
        git_label = f"{git_label} — branch {git['branch']}"

    artifacts = load_workflow_artifacts(str(item.get("path", "")))
    task_markers = _top_task_marker_lines(db_path, int(item["id"]))
    modified_files = _modified_files_from_git(db_path, int(item["id"]))
    last_session_label = _format_last_session_label(session)
    if timeline_sessions is None:
        with DatabaseConnection(db_path) as conn:
            timeline_sessions = [
                _session_dict(s, is_active=s.ended_at is None)
                for s in SessionRepository(conn).list_for_project(int(item["id"]), limit=3)
            ]
    git = item.get("git_status") or {}
    engine = SummaryEngine()
    result = engine.build_dashboard(
        project_name=str(item.get("name", "")),
        project_notes=item.get("notes"),
        last_session_label=last_session_label,
        modified_files=modified_files,
        exit_note=session_signals.exit_note,
        blocker=session_signals.blocker,
        next_step=session_signals.next_step,
        has_active_session=session_signals.has_active_session,
        artifacts=artifacts,
        open_task_count=item.get("open_task_count"),
        has_scan=item.get("latest_scan_at") is not None,
        git_label=git_label,
        task_markers=task_markers,
        timeline_sessions=timeline_sessions,
        last_opened_at=item.get("last_opened_at"),
        last_session_ended_at=session_signals.last_session_ended_at
        or session.get("ended_at"),
        session_started_at=session_signals.session_started_at,
        last_refreshed_at=item.get("last_refreshed_at"),
        git_state=git.get("state"),
        git_branch=git.get("branch"),
        git_is_repo=bool(git.get("is_git_repo")),
    )
    return {
        "headline": result.headline,
        "summary_text": result.body,
        "scroll_excerpt": result.body,
        "generated_at": item.get("updated_at"),
        "grifi_icon_state": "ready",
        "source": "summary_engine",
        "sources_used": result.sources_used,
        "attributed_lines": result.attributed_lines,
        "timeline": result.to_dict()["timeline"],
        "away_label": result.away_label,
        "workflow_files": [a.filename for a in artifacts],
        "task_markers": list(task_markers),
        "confidence": result.confidence,
        "mvp_sections": result.mvp_sections,
    }


def _modified_files_from_git(db_path, project_id: int) -> tuple[str, ...]:
    try:
        with DatabaseConnection(db_path) as conn:
            git = GitSnapshotRepository(conn).get_latest_for_project(project_id)
    except Exception:  # noqa: BLE001
        return ()
    if git is None:
        return ()
    return tuple(git.modified_files[:5])


def _format_last_session_label(session: dict[str, Any]) -> str | None:
    if not session:
        return None
    if session.get("is_active"):
        started = session.get("started_at", "")
        return f"Active session since {started}" if started else "Active session"
    ended = session.get("ended_at")
    if ended:
        return f"Ended {ended}"
    return None


def _resume_headline(body: str) -> str:
    return pick_headline_from_body(body)


def _block_from_startup_record(startup: StartupSummaryRecord) -> dict[str, Any]:
    return {
        "headline": startup.headline,
        "summary_text": startup.summary_text,
        "scroll_excerpt": _excerpt(startup.scroll_content, 600),
        "generated_at": startup.generated_at,
        "grifi_icon_state": startup.grifi_icon_state,
        "source": "startup_summaries",
    }


def _block_from_stored_resume(stored: ResumeSummaryRecord) -> dict[str, Any]:
    display_body = humanize_stored_body(stored.summary_body)
    excerpt = _excerpt(display_body, 600) or ""
    return {
        "headline": _resume_headline(stored.summary_body),
        "summary_text": excerpt,
        "scroll_excerpt": excerpt,
        "generated_at": stored.generated_at,
        "grifi_icon_state": "ready",
        "source": "resume_summaries",
    }


def _choose_summary_block(
    stored: ResumeSummaryRecord | None,
    startup: StartupSummaryRecord | None,
) -> dict[str, Any] | None:
    """Prefer the newer of startup_summaries vs resume_summaries for UI-visible text."""
    if stored is None and startup is None:
        return None
    if stored is None:
        return _block_from_startup_record(startup)  # type: ignore[arg-type]
    if startup is None:
        return _block_from_stored_resume(stored)
    if stored.generated_at >= startup.generated_at:
        return _block_from_stored_resume(stored)
    return _block_from_startup_record(startup)


def handle_dashboard(config_manager: ConfigManager | None = None) -> IpcResponse:
    """Project list with session, summary, and git status for the dashboard."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        with DatabaseConnection(runtime.database_path) as conn:
            items = [
                _public_dashboard_item(
                    _build_dashboard_item(conn, runtime.database_path, record)
                )
                for record in runtime.registry.list_projects()
            ]
        return success(
            {
                "database_path": str(runtime.database_path),
                "projects": items,
            }
        )
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_project_detail(
    project_id: int,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Resume panel and detail view for one selected project."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        record = _resolve_by_id(runtime.registry, project_id)

        with DatabaseConnection(runtime.database_path) as conn:
            item = _build_dashboard_item(conn, runtime.database_path, record)
            summary_block = item.pop("_summary_block", None)
            resume_panel = _build_resume_panel(
                runtime.database_path,
                project_id,
                item,
                startup_block=summary_block,
            )

        return success(
            {
                "project": item,
                "resume_panel": resume_panel,
            }
        )
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_refresh_resume(
    project_id: int,
    config_manager: ConfigManager | None = None,
    *,
    git_only: bool = False,
) -> IpcResponse:
    """Re-scan project sources, regenerate resume, return fresh detail."""
    try:
        from grafid.cli.runtime import prepare_runtime
        from grafid.observability.timing import new_timing_collector, timed_block
        from grafid.services.context_refresh import (
            build_scan_health_from_refresh,
            refresh_project_scan,
        )
        from grafid.utils.datetime_utils import utc_now_iso

        manager = config_manager or ConfigManager()
        timing = new_timing_collector(manager.bootstrap_defaults())
        runtime = prepare_runtime(manager)
        record = _resolve_by_id(runtime.registry, project_id)

        with timed_block(
            "ipc.refresh_resume",
            timing,
            project_id=project_id,
            git_only=git_only,
        ):
            refresh_result = refresh_project_scan(
                runtime.database_path, project_id, git_only=git_only
            )

            refreshed_at = utc_now_iso()
            with DatabaseConnection(runtime.database_path) as conn:
                from grafid.db.repositories.project_repository import ProjectRepository

                ProjectRepository(conn).set_last_refreshed(project_id, refreshed_at)
                conn.commit()

            ResumeService(runtime.database_path).generate_resume(
                project_id, mode="short", persist=True, replace_latest_short=True
            )
            record = _resolve_by_id(runtime.registry, project_id)
            with DatabaseConnection(runtime.database_path) as conn:
                item = _build_dashboard_item(conn, runtime.database_path, record)
                summary_block = item.pop("_summary_block", None)
                resume_panel = _build_resume_panel(
                    runtime.database_path,
                    project_id,
                    item,
                    startup_block=summary_block,
                )

            scan_health = build_scan_health_from_refresh(refresh_result)

            payload: dict[str, Any] = {
                "project": item,
                "resume_panel": resume_panel,
                "last_refreshed_at": refreshed_at,
                "refresh": refresh_result.to_dict(),
                "scan_health": scan_health.to_dict(),
            }
            if timing.enabled:
                payload["debug_timings"] = timing.as_list()
            return success(payload)
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_project_history(
    project_id: int,
    *,
    limit: int = HISTORY_LIMIT_DEFAULT,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Scan history rows for the history section."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        _resolve_by_id(runtime.registry, project_id)
        entries = SnapshotPersistenceService(runtime.database_path).list_history(
            project_id, limit=limit
        )
        return success(
            {
                "project_id": project_id,
                "history": _history_rows(entries),
            }
        )
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_open_folder(
    project_id: int,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Open the registered project directory in the file manager (CLI/IPC)."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        record = _resolve_by_id(runtime.registry, project_id)
        launcher = WorkflowLaunchService(runtime.database_path, runtime.registry)
        payload = launcher.open_folder(record.path)
        return success({"project_id": project_id, **payload})
    except WorkflowLaunchError as exc:
        return failure("launch_failed", str(exc))
    except ValidationError as exc:
        return failure("launch_failed", str(exc))
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_open_project(
    project_id: int,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Resume workflow: session, editor launch, or Explorer fallback."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        manager = config_manager or ConfigManager()
        config = manager.load()
        launcher = WorkflowLaunchService(runtime.database_path, runtime.registry)
        # Desktop opens Explorer via Rust; avoid duplicate Explorer from Python.
        updated, outcome = launcher.open_project(
            project_id, config=config, launch_explorer=False
        )
        with DatabaseConnection(runtime.database_path) as conn:
            project_item = _public_dashboard_item(
                _build_dashboard_item(conn, runtime.database_path, updated)
            )
        return success(
            {
                "project": project_item,
                "launch": outcome.to_dict(),
            }
        )
    except WorkflowLaunchError as exc:
        return failure("launch_failed", str(exc))
    except ValidationError as exc:
        return failure("launch_failed", str(exc))
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def _public_dashboard_item(item: dict[str, Any]) -> dict[str, Any]:
    """Drop internal-only fields before JSON IPC responses."""
    public = dict(item)
    public.pop("_summary_block", None)
    return public


def _item_and_resume_panel(
    conn,
    db_path,
    record,
    project_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build dashboard row + resume panel without duplicate summary work."""
    item = _build_dashboard_item(conn, db_path, record)
    summary_block = item.pop("_summary_block", None)
    resume_panel = _build_resume_panel(
        db_path, project_id, item, startup_block=summary_block
    )
    return item, resume_panel


def _project_detail_payload(conn, db_path, record) -> dict[str, Any]:
    """Preload project detail for desktop without extra IPC calls."""
    item, resume_panel = _item_and_resume_panel(conn, db_path, record, int(record.id))
    history = _history_rows(
        SnapshotPersistenceService(db_path).list_history(
            int(record.id), limit=HISTORY_LIMIT_DEFAULT
        )
    )
    return {
        "project": _public_dashboard_item(item),
        "resume_panel": resume_panel,
        "history": history,
    }


def build_bootstrap_projects(db_path, projects: list) -> list[dict[str, Any]]:
    """Bootstrap payload: include per-project cached detail (panel + history)."""
    with DatabaseConnection(db_path) as conn:
        out: list[dict[str, Any]] = []
        for record in projects:
            payload = _project_detail_payload(conn, db_path, record)
            out.append({**payload["project"], "resume_panel": payload["resume_panel"], "history": payload["history"]})
        return out


def build_dashboard_projects(
    db_path,
    projects: list,
) -> list[dict[str, Any]]:
    """Build dashboard rows inside an existing connection context."""
    with DatabaseConnection(db_path) as conn:
        return [
            _public_dashboard_item(_build_dashboard_item(conn, db_path, record))
            for record in projects
        ]


def _resolve_by_id(registry: ProjectRegistryService, project_id: int):
    try:
        return registry.get_info(str(project_id))
    except ProjectError as exc:
        raise ProjectError(f"Project not found: {project_id}") from exc


def _build_dashboard_item(conn, db_path, record) -> dict[str, Any]:
    project = _project_to_dict(record)
    session = _latest_session(conn, record.id)
    git = GitSnapshotRepository(conn).get_latest_for_project(record.id)
    resume = ResumeService(db_path).get_latest_stored_summary(record.id, mode="short")
    scan_ctx = _scan_context(conn, record.id)

    git_status = _git_status_dict(git)
    scan_ctx = _scan_context(conn, record.id)
    item_ctx = {
        **project,
        "latest_session": session,
        "git_status": git_status,
        "open_task_count": scan_ctx["open_task_count"],
        "latest_scan_at": scan_ctx["latest_scan_at"],
    }
    summary_block = _build_human_summary_block(item_ctx, db_path)
    summary_preview: dict[str, Any] | None = None
    if summary_block:
        summary_preview = {
            "headline": summary_block["headline"],
            "summary_text": summary_block["summary_text"],
            "generated_at": summary_block.get("generated_at"),
            "source": summary_block.get("source"),
        }

    return {
        **project,
        "has_open_session": bool(session and session.get("is_active")),
        "latest_session": session,
        "summary_preview": summary_preview,
        "git_status": git_status,
        "has_resume": resume is not None,
        "open_task_count": scan_ctx["open_task_count"],
        "latest_scan_at": scan_ctx["latest_scan_at"],
        "_summary_block": summary_block,
    }


def _build_resume_panel(
    db_path,
    project_id: int,
    item: dict[str, Any],
    *,
    startup_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = item.get("latest_session") or {}
    stored = ResumeService(db_path).get_latest_stored_summary(project_id, mode="short")
    startup = StartupSummaryService(db_path).get_latest(project_id)

    with DatabaseConnection(db_path) as conn:
        session_signals = resolve_summary_session_fields(conn, project_id)

    blocker = session_signals.blocker
    next_step = session_signals.next_step
    exit_note = session_signals.exit_note

    modified_files: list[str] = []
    with DatabaseConnection(db_path) as conn:
        git = GitSnapshotRepository(conn).get_latest_for_project(project_id)
        if git is not None:
            modified_files = list(git.modified_files[:MODIFIED_FILES_LIMIT])

    if startup_block is None:
        startup_block = _build_human_summary_block(item, db_path)

    scan_ctx = _scan_context_from_item(item)

    return {
        "startup_summary": startup_block,
        "workflow_files": startup_block.get("workflow_files", []),
        "sources_used": startup_block.get("sources_used", []),
        "blocker": blocker,
        "next_step": next_step,
        "exit_note": exit_note,
        "modified_files": modified_files,
        "stored_resume_excerpt": _excerpt(
            humanize_stored_body(stored.summary_body) if stored else None
        ),
        "git_status": item.get("git_status"),
        "has_stored_resume": stored is not None,
        "latest_session": session if session else None,
        "last_opened_at": item.get("last_opened_at"),
        "open_task_count": scan_ctx["open_task_count"],
        "latest_scan_at": scan_ctx["latest_scan_at"],
        "last_refreshed_at": item.get("last_refreshed_at"),
        "confidence": startup_block.get("confidence"),
        "mvp_sections": startup_block.get("mvp_sections", []),
        "timeline": startup_block.get("timeline", []),
        "attributed_lines": startup_block.get("attributed_lines", []),
        "away_label": startup_block.get("away_label"),
    }


def _scan_context(conn, project_id: int) -> dict[str, Any]:
    """Latest scan task-marker count (deterministic, DB-only)."""
    entries = SnapshotRepository(conn).list_history_for_project(project_id, limit=1)
    if not entries:
        return {"open_task_count": None, "latest_scan_at": None}
    entry = entries[0]
    findings = ScanFindingRepository(conn).list_for_snapshot(entry.snapshot_id)
    return {
        "open_task_count": count_open_tasks(tuple(findings)),
        "latest_scan_at": entry.scanned_at,
    }


def _scan_context_from_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "open_task_count": item.get("open_task_count"),
        "latest_scan_at": item.get("latest_scan_at"),
    }


def _latest_session(conn, project_id: int) -> dict[str, Any] | None:
    repo = SessionRepository(conn)
    active = repo.get_active_for_project(project_id)
    if active is not None:
        return _session_dict(active, is_active=True)
    ended = repo.get_last_ended_for_project(project_id)
    if ended is not None:
        return _session_dict(ended, is_active=False)
    return None


def _session_dict(session: WorkSessionRecord, *, is_active: bool) -> dict[str, Any]:
    return {
        "id": session.id,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "is_active": is_active,
        "status": session.status,
        "summary": session.summary,
        "exit_note": normalize_note(session.exit_note),
        "blocker": normalize_note(session.blocker),
        "next_step": normalize_note(session.next_step),
    }


def _git_status_dict(git: GitSnapshotRecord | None) -> dict[str, Any]:
    if git is None:
        return {
            "state": "unknown",
            "label": "No scan yet",
            "is_git_repo": False,
            "is_dirty": False,
            "branch": None,
        }
    if not git.is_git_repo:
        return {
            "state": "not_repo",
            "label": "Not a git repository",
            "is_git_repo": False,
            "is_dirty": False,
            "branch": None,
        }
    state = "dirty" if git.is_dirty else "clean"
    label = "Dirty" if git.is_dirty else "Clean"
    branch = git.current_branch or "unknown"
    return {
        "state": state,
        "label": label,
        "is_git_repo": True,
        "is_dirty": git.is_dirty,
        "branch": branch,
    }


def _history_rows(entries: list[SnapshotHistoryEntry]) -> list[dict[str, Any]]:
    return [
        {
            "snapshot_id": entry.snapshot_id,
            "scanned_at": entry.scanned_at,
            "findings_count": entry.findings_count,
            "scanned_files_count": entry.scanned_files_count,
            "duration_seconds": entry.duration_seconds,
            "git_branch": entry.git_branch,
            "git_dirty": entry.git_dirty,
            "is_git_repo": entry.is_git_repo,
        }
        for entry in entries
    ]


def _excerpt(text: str | None, limit: int = RESUME_EXCERPT_CHARS) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
