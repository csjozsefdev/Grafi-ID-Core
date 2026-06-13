"""IPC handlers — delegate to existing services (no duplicate business logic)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from grafid.config.manager import ConfigManager
from grafid.core.constants import SCHEMA_VERSION
from grafid.core.exceptions import (
    ConfigError,
    DatabaseError,
    GrafIdError,
    PermissionError as GrafPermissionError,
    StartupError,
)
from grafid.ipc.envelope import IpcResponse, failure, success
from grafid.models.grafi import GrafiSummaryPayload, PassiveRuntimeInfo, StartupSummaryPayload
from grafid.runtime.passive import get_passive_runtime
from grafid.services.project_registry import ProjectRegistryService
from grafid.observability.journal import record_event
from grafid.observability.timing import new_timing_collector, timed_block
from grafid.packaging.bootstrap import describe_layout
from grafid.packaging.validation import report_to_dict, validate_runtime
from grafid.services.startup import StartupService
from grafid.services.startup_summary_service import StartupSummaryService


def handle_health() -> IpcResponse:
    """Lightweight check that the Python runtime can load config paths."""
    try:
        manager = ConfigManager()
        config = manager.load()
        config_dir = manager.config_dir
        db_path = config.resolved_database_path(config_dir)
        layout_info = describe_layout()
        return success(
            {
                "app": "graf-id",
                "schema_version": SCHEMA_VERSION,
                "config_dir": str(config_dir),
                "database_path": str(db_path),
                "config_readable": True,
                "runtime_mode": layout_info["mode"],
                "data_dir": layout_info["data_dir"],
                "resource_root": layout_info["resource_root"],
            }
        )
    except (ConfigError, GrafPermissionError) as exc:
        return failure("config_error", str(exc))
    except GrafIdError as exc:
        return failure("runtime_error", str(exc))


def handle_runtime_check(*, run_full_startup: bool = False) -> IpcResponse:
    """Packaging-oriented validation: paths, config JSON, database integrity."""
    report = validate_runtime(run_full_startup=run_full_startup)
    payload = report_to_dict(report)
    if report.ok:
        return success(payload)
    return failure(
        "runtime_validation_failed",
        "; ".join(report.issues) if report.issues else "Runtime validation failed",
        data=payload,
    )


def handle_bootstrap(
    *,
    run_startup_summary: bool = True,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """
    Initialize config + database, verify integrity, list projects, optional startup summary.

    Mirrors CLI startup without Typer output.
    """
    manager = config_manager or ConfigManager()
    config = manager.bootstrap_defaults()
    timing = new_timing_collector(config)
    try:
        with timed_block("startup", timing):
            startup = StartupService(config_manager=manager).run()
        registry = ProjectRegistryService(startup.database_path)
        project_records = registry.list_projects()
        from grafid.ipc.dashboard_handlers import build_bootstrap_projects
        from grafid.ipc.settings_handlers import handle_get_app_settings

        with timed_block("dashboard_projects", timing, count=len(project_records)):
            projects = build_bootstrap_projects(startup.database_path, project_records)

        settings_resp = handle_get_app_settings(manager)
        app_settings = settings_resp.data if settings_resp.ok else None

        startup_payload: dict[str, Any] | None = None
        startup_card: dict[str, Any] | None = None
        if run_startup_summary:
            from grafid.ipc.startup_handlers import build_startup_card

            summary_service = StartupSummaryService(startup.database_path)
            with timed_block("startup_summary", timing):
                summary = summary_service.run_flow(persist=True)
            record = (
                summary_service.get_latest(summary.project_id)
                if summary.project_id is not None
                else None
            )
            startup_payload = _startup_summary_to_dict(summary, record=record)
            startup_card = build_startup_card(
                startup.database_path, summary, record=record
            )
            record_event(
                "startup.summary_generated",
                config_dir=manager.config_dir,
                config=config,
                project_id=summary.project_id,
                is_empty=summary.is_empty,
                visible=bool(startup_card.get("visible")),
            )
            if summary.is_empty:
                record_event(
                    "startup.summary_empty",
                    config_dir=manager.config_dir,
                    config=config,
                    project_id=summary.project_id,
                )

        passive: PassiveRuntimeInfo = get_passive_runtime().info()

        payload: dict[str, Any] = {
            "config_dir": str(startup.config_dir),
            "config_path": str(startup.config_path),
            "database_path": str(startup.database_path),
            "schema_version": SCHEMA_VERSION,
            "projects": projects,
            "app_settings": app_settings,
            "startup_summary": startup_payload,
            "startup_card": startup_card,
            "passive_runtime": asdict(passive),
        }
        if timing.enabled:
            payload["debug_timings"] = timing.as_list()

        record_event(
            "ipc.bootstrap",
            config_dir=manager.config_dir,
            config=config,
            project_count=len(projects),
            startup_visible=bool(startup_card and startup_card.get("visible")),
        )
        return success(payload)
    except (StartupError, ConfigError, DatabaseError, GrafPermissionError) as exc:
        record_event(
            "ipc.bootstrap_failed",
            config_dir=manager.config_dir,
            config=config,
            error=_error_code(exc),
        )
        return failure(_error_code(exc), str(exc))
    except GrafIdError as exc:
        return failure("runtime_error", str(exc))


def handle_list_projects(
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Return registered projects after the same runtime bootstrap as CLI commands."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        projects = [
            _project_to_dict(record) for record in runtime.registry.list_projects()
        ]
        return success(
            {
                "database_path": str(runtime.database_path),
                "projects": projects,
            }
        )
    except (ConfigError, DatabaseError, StartupError, GrafPermissionError) as exc:
        return failure(_error_code(exc), str(exc))
    except GrafIdError as exc:
        return failure("runtime_error", str(exc))


def _project_to_dict(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "name": record.name,
        "path": record.path,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "last_opened_at": record.last_opened_at,
        "preferred_ide": record.preferred_ide,
        "is_active": record.is_active,
        "category": record.category,
        "status": record.status,
        "notes": record.notes,
        "last_refreshed_at": record.last_refreshed_at,
    }


def _startup_summary_to_dict(
    payload: StartupSummaryPayload,
    *,
    record: Any | None = None,
) -> dict[str, Any]:
    grafi: GrafiSummaryPayload = payload.grafi
    is_dismissed = record.is_dismissed if record is not None else grafi.is_dismissed
    return {
        "project_id": payload.project_id,
        "project_name": payload.project_name,
        "session_id": payload.session_id,
        "headline": payload.headline,
        "summary_text": payload.summary_text,
        "scroll_content": payload.scroll_content,
        "startup_summary_id": payload.startup_summary_id,
        "has_unfinished_session": payload.has_unfinished_session,
        "is_empty": payload.is_empty,
        "is_dismissed": is_dismissed,
        "grafi": {**asdict(grafi), "is_dismissed": is_dismissed},
    }


def _error_code(exc: Exception) -> str:
    mapping = {
        StartupError: "startup_error",
        ConfigError: "config_error",
        DatabaseError: "database_error",
        GrafPermissionError: "permission_error",
    }
    for exc_type, code in mapping.items():
        if isinstance(exc, exc_type):
            return code
    return "runtime_error"
