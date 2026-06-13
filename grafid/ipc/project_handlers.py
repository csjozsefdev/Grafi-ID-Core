"""IPC handlers for project registration and removal."""

from __future__ import annotations

from grafid.config.manager import ConfigManager
from grafid.core.exceptions import (
    ConfigError,
    DatabaseError,
    DuplicateProjectError,
    GrafIdError,
    PermissionError as GrafPermissionError,
    ProjectError,
    StartupError,
    ValidationError,
)
from grafid.db.connection import DatabaseConnection
from grafid.ipc.dashboard_handlers import _build_dashboard_item, _public_dashboard_item
from grafid.ipc.envelope import IpcResponse, failure, success
from grafid.ipc.handlers import _error_code


def handle_add_project(
    name: str,
    path: str,
    *,
    category: str | None = None,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Register a project directory and return an enriched dashboard row."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        record = runtime.registry.add(name, path, category=category)
        with DatabaseConnection(runtime.database_path) as conn:
            project_item = _public_dashboard_item(
                _build_dashboard_item(conn, runtime.database_path, record)
            )
        return success(
            {
                "project": project_item,
                "message": f"Added project '{record.name}'.",
            }
        )
    except DuplicateProjectError as exc:
        return failure("duplicate_project", str(exc))
    except ValidationError as exc:
        return failure("validation_error", str(exc))
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except (StartupError, ConfigError, DatabaseError, GrafPermissionError) as exc:
        return failure(_error_code(exc), str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_remove_project(
    project_id: int,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Remove a project from the Graf-Id registry only (files stay on disk)."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        record = runtime.registry.remove(str(project_id))
        return success(
            {
                "project_id": record.id,
                "project_name": record.name,
                "message": f"Removed '{record.name}' from Graf-Id.",
            }
        )
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except ValidationError as exc:
        return failure("validation_error", str(exc))
    except (StartupError, ConfigError, DatabaseError, GrafPermissionError) as exc:
        return failure(_error_code(exc), str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_update_project(
    project_id: int,
    *,
    name: str | None = None,
    path: str | None = None,
    category: str | None = None,
    status: str | None = None,
    notes: str | None = None,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Update project metadata and return an enriched dashboard row."""
    try:
        from grafid.cli.runtime import prepare_runtime

        runtime = prepare_runtime(config_manager)
        record = runtime.registry.update(
            project_id,
            name=name,
            raw_path=path,
            category=category,
            status=status,
            notes=notes,
        )
        with DatabaseConnection(runtime.database_path) as conn:
            project_item = _public_dashboard_item(
                _build_dashboard_item(conn, runtime.database_path, record)
            )
        return success(
            {
                "project": project_item,
                "message": f"Updated project '{record.name}'.",
            }
        )
    except DuplicateProjectError as exc:
        return failure("duplicate_project", str(exc))
    except ValidationError as exc:
        return failure("validation_error", str(exc))
    except ProjectError as exc:
        return failure("project_error", str(exc))
    except (StartupError, ConfigError, DatabaseError, GrafPermissionError) as exc:
        return failure(_error_code(exc), str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))
