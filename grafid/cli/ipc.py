"""IPC CLI commands — JSON on stdout for Tauri desktop shell."""

from __future__ import annotations

import typer

from grafid.ipc.envelope import emit_response
from grafid.ipc.stdio_config import configure_ipc_stdio_utf8
from grafid.ipc.dashboard_handlers import (
    handle_dashboard,
    handle_open_folder,
    handle_open_project,
    handle_project_detail,
    handle_project_history,
    handle_refresh_resume,
)
from grafid.ipc.handlers import (
    handle_bootstrap,
    handle_health,
    handle_list_projects,
    handle_runtime_check,
)
from grafid.ipc.settings_handlers import (
    handle_get_app_settings,
    handle_reset_app_settings,
    handle_save_app_settings,
    handle_set_default_project_opener,
)
from grafid.ipc.usage_handlers import handle_usage_insights
from grafid.ipc.project_handlers import (
    handle_add_project,
    handle_remove_project,
    handle_update_project,
)
from grafid.ipc.session_handlers import (
    handle_close_session,
    handle_end_session,
    handle_session_timeline,
    handle_start_session,
)
from grafid.ipc.startup_handlers import (
    handle_dismiss_startup,
    handle_resume_preview,
    handle_startup_card,
)

ipc_app = typer.Typer(
    help="Machine-readable JSON IPC for the desktop shell (stdout only).",
    no_args_is_help=True,
)


@ipc_app.callback()
def _ipc_entry() -> None:
    configure_ipc_stdio_utf8()


@ipc_app.command("health")
def ipc_health_cmd() -> None:
    """Emit health JSON (config paths readable)."""
    emit_response(handle_health())


@ipc_app.command("usage-insights")
def ipc_usage_insights_cmd() -> None:
    """Emit local usage journal summary JSON (no telemetry)."""
    emit_response(handle_usage_insights())


@ipc_app.command("app-settings")
def ipc_app_settings_cmd() -> None:
    """Emit app settings for the desktop Settings page."""
    emit_response(handle_get_app_settings())


@ipc_app.command("save-app-settings")
def ipc_save_app_settings_cmd(
    opener: str = typer.Option("system", "--opener", help="system, cursor, vscode, explorer."),
    usage_journal: str = typer.Option("false", "--usage-journal", help="true or false."),
    debug_timing: str = typer.Option("false", "--debug-timing", help="true or false."),
    compact_mode: str = typer.Option("false", "--compact-mode", help="true or false."),
) -> None:
    """Persist app settings to config.json."""
    emit_response(
        handle_save_app_settings(opener, usage_journal, debug_timing, compact_mode)
    )


@ipc_app.command("reset-app-settings")
def ipc_reset_app_settings_cmd() -> None:
    """Reset app settings to defaults."""
    emit_response(handle_reset_app_settings())


@ipc_app.command("set-default-project-opener")
def ipc_set_default_project_opener_cmd(
    opener: str = typer.Argument(help="system, cursor, vscode, or explorer."),
) -> None:
    """Persist default_project_opener in config.json."""
    emit_response(handle_set_default_project_opener(opener))


@ipc_app.command("runtime-check")
def ipc_runtime_check_cmd(
    full: bool = typer.Option(
        False,
        "--full",
        help="Run full StartupService (config, logging, DB init).",
    ),
) -> None:
    """Emit packaging validation JSON (paths, config, database)."""
    emit_response(handle_runtime_check(run_full_startup=full))


@ipc_app.command("bootstrap")
def ipc_bootstrap_cmd(
    skip_summary: bool = typer.Option(
        False,
        "--skip-summary",
        help="Skip startup summary generation during bootstrap.",
    ),
) -> None:
    """Emit bootstrap JSON: init DB, verify integrity, list projects, startup summary."""
    emit_response(handle_bootstrap(run_startup_summary=not skip_summary))


@ipc_app.command("list-projects")
def ipc_list_projects_cmd() -> None:
    """Emit project list JSON after runtime initialization."""
    emit_response(handle_list_projects())


@ipc_app.command("add-project")
def ipc_add_project_cmd(
    name: str = typer.Argument(help="Unique project name."),
    path: str = typer.Argument(help="Absolute project directory path."),
    category: str = typer.Option(
        "Personal Projects",
        "--category",
        help="Project category (Personal Projects, Freelance Work, Client Work, Archived).",
    ),
) -> None:
    """Register a project directory for workflow continuity."""
    emit_response(handle_add_project(name, path, category=category))


@ipc_app.command("remove-project")
def ipc_remove_project_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
) -> None:
    """Remove a project from the Graf-Id registry (files stay on disk)."""
    emit_response(handle_remove_project(project_id))


@ipc_app.command("update-project")
def ipc_update_project_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    name: str | None = typer.Option(None, "--name"),
    path: str | None = typer.Option(None, "--path"),
    category: str | None = typer.Option(None, "--category"),
    status: str | None = typer.Option(None, "--status", help="active, paused, archived."),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Update project metadata."""
    emit_response(
        handle_update_project(
            project_id,
            name=name,
            path=path,
            category=category,
            status=status,
            notes=notes,
        )
    )


@ipc_app.command("dashboard")
def ipc_dashboard_cmd() -> None:
    """Emit enriched project dashboard rows."""
    emit_response(handle_dashboard())


@ipc_app.command("project-detail")
def ipc_project_detail_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
) -> None:
    """Emit resume panel and history for one project."""
    emit_response(handle_project_detail(project_id))


@ipc_app.command("project-history")
def ipc_project_history_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    limit: int = typer.Option(15, help="Maximum history rows."),
) -> None:
    """Emit scan history for one project."""
    emit_response(handle_project_history(project_id, limit=limit))


@ipc_app.command("open-folder")
def ipc_open_folder_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
) -> None:
    """Open the project directory in the file manager."""
    emit_response(handle_open_folder(project_id))


@ipc_app.command("open-project")
def ipc_open_project_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
) -> None:
    """Resume workflow: session, editor launch, or Explorer fallback."""
    emit_response(handle_open_project(project_id))


@ipc_app.command("resume-preview")
def ipc_resume_preview_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
) -> None:
    """Emit resume preview fields for the startup card."""
    emit_response(handle_resume_preview(project_id))


@ipc_app.command("refresh-resume")
def ipc_refresh_resume_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    git_only: bool = typer.Option(False, "--git-only", help="Skip filesystem scan."),
) -> None:
    """Regenerate stored resume and return updated project detail."""
    emit_response(handle_refresh_resume(project_id, git_only=git_only))


@ipc_app.command("start-session")
def ipc_start_session_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    checkpoint: str | None = typer.Option(None, "--checkpoint", help="Optional bookmark label."),
) -> None:
    """Start a work session for one project."""
    emit_response(handle_start_session(project_id, checkpoint=checkpoint))


@ipc_app.command("session-timeline")
def ipc_session_timeline_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    limit: int = typer.Option(10, help="Maximum sessions to return."),
) -> None:
    """Emit recent session timeline for one project."""
    emit_response(handle_session_timeline(project_id, limit=limit))


@ipc_app.command("end-session")
def ipc_end_session_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    exit_note: str | None = typer.Option(None, "--exit-note"),
    unfinished: str | None = typer.Option(None, "--unfinished"),
    blocker: str | None = typer.Option(None, "--blocker"),
    next_step: str | None = typer.Option(None, "--next-step"),
    skip_notes: bool = typer.Option(False, "--skip-notes"),
) -> None:
    """End the active session (alias of close-session)."""
    emit_response(
        handle_end_session(
            project_id,
            exit_note=exit_note,
            unfinished=unfinished,
            blocker=blocker,
            next_step=next_step,
            skip_notes=skip_notes,
        )
    )


@ipc_app.command("close-session")
def ipc_close_session_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    exit_note: str | None = typer.Option(None, "--exit-note", help="What was done today."),
    unfinished: str | None = typer.Option(None, "--unfinished", help="What is still unfinished."),
    blocker: str | None = typer.Option(None, "--blocker"),
    next_step: str | None = typer.Option(None, "--next-step"),
    skip_notes: bool = typer.Option(False, "--skip-notes"),
) -> None:
    """End the active session and save exit notes."""
    emit_response(
        handle_close_session(
            project_id,
            exit_note=exit_note,
            unfinished=unfinished,
            blocker=blocker,
            next_step=next_step,
            skip_notes=skip_notes,
        )
    )


@ipc_app.command("dismiss-startup")
def ipc_dismiss_startup_cmd(
    project_id: int = typer.Argument(help="Registered project id."),
    summary_id: int | None = typer.Option(
        None, "--summary-id", help="Specific startup_summaries row id."
    ),
) -> None:
    """Mark the startup summary card as dismissed."""
    emit_response(handle_dismiss_startup(project_id, summary_id))


@ipc_app.command("startup-card")
def ipc_startup_card_cmd() -> None:
    """Emit startup card JSON (run flow + Grafi payload)."""
    emit_response(handle_startup_card())
