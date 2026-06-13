"""Launch projects in the editor or file manager for workflow continuation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grafid.config.manager import AppConfig
from grafid.config.preferences import opener_to_ide_token
from grafid.core.exceptions import (
    ProjectError,
    SessionError,
    ValidationError,
)
from grafid.models.project import ProjectRecord
from grafid.models.session import WorkSessionRecord
from grafid.services.project_registry import ProjectRegistryService
from grafid.services.project_validation import normalize_project_path
from grafid.services.session_service import SessionService
from grafid.utils.logging_setup import get_logger

logger = get_logger("workflow_launch")

_SUPPORTED_IDES = frozenset({"cursor", "vscode", "explorer"})


def detect_system_editor() -> str | None:
    """Pick the first editor found on PATH (cursor, then VS Code)."""
    if shutil.which("cursor"):
        return "cursor"
    if shutil.which("code"):
        return "vscode"
    return None


def _editor_display_name(ide: str) -> str:
    return "Cursor" if ide == "cursor" else "VS Code"


@dataclass(frozen=True)
class LaunchOutcome:
    """Result of opening a project for continued work."""

    action: str
    editor: str | None
    message: str
    session_id: int | None
    session_started: bool
    fallback_used: bool
    open_explorer: bool

    def to_dict(self) -> dict[str, Any]:
        editor_launched = self.action == "editor" and not self.fallback_used
        return {
            "success": True,
            "message": self.message,
            "editor_launched": editor_launched,
            "explorer_opened": self.open_explorer,
            "fallback_used": self.fallback_used,
            "action": self.action,
            "editor": self.editor,
            "session_id": self.session_id,
            "session_started": self.session_started,
            "open_explorer": self.open_explorer,
        }


class WorkflowLaunchError(ProjectError):
    """User-facing launch failure (missing path, editor, or OS error)."""


def normalize_ide_token(value: str | None) -> str | None:
    """Map config/CLI values to cursor, vscode, explorer, or None."""
    if value is None:
        return None
    token = value.strip().lower()
    if not token or token in {"-", "none", "null"}:
        return None
    aliases = {
        "code": "vscode",
        "vs code": "vscode",
        "vs_code": "vscode",
        "visual studio code": "vscode",
        "folder": "explorer",
        "file explorer": "explorer",
        "explorer": "explorer",
    }
    normalized = aliases.get(token, token)
    if normalized not in _SUPPORTED_IDES:
        raise ValidationError(
            f"Unsupported preferred_ide '{value}'. Use cursor, vscode, or explorer."
        )
    return normalized


def resolve_preferred_ide(
    project: ProjectRecord,
    config: AppConfig,
) -> str | None:
    """Project metadata wins, then default_project_opener, then legacy preferred_ide."""
    if project.preferred_ide:
        return normalize_ide_token(project.preferred_ide)
    opener = config.default_project_opener or "system"
    ide = opener_to_ide_token(opener)
    if ide is None and opener == "system":
        ide = detect_system_editor()
    if ide is not None:
        return ide
    extra = config.extra.get("preferred_ide")
    if extra is None:
        return None
    return normalize_ide_token(str(extra))


class WorkflowLaunchService:
    """Open folders and resume work in a configured editor."""

    def __init__(self, db_path: Path, registry: ProjectRegistryService) -> None:
        self._db_path = db_path
        self._registry = registry
        self._sessions = SessionService(db_path)

    def open_folder(self, raw_path: str) -> dict[str, Any]:
        """
        Open the registered project root in the file manager (CLI / ipc open-folder).

        Uses the stored registry path only — no subfolder guessing.
        """
        folder = normalize_project_path(raw_path)
        open_folder_in_explorer(folder)
        message = f"Opened folder in File Explorer: {folder}"
        logger.info(message)
        return {"path": str(folder), "message": message}

    def open_project(
        self,
        project_id: int,
        *,
        config: AppConfig,
        launch_explorer: bool = True,
    ) -> tuple[ProjectRecord, LaunchOutcome]:
        """
        Resume workflow: last_opened_at, session, editor launch, optional Explorer.

        When launch_explorer is False (desktop IPC), Explorer is not opened here;
        the UI opens the registered project root once via Rust instead.
        """
        updated = self._registry.open_project(str(project_id))
        try:
            folder = normalize_project_path(updated.path)
        except ValidationError as exc:
            raise WorkflowLaunchError(str(exc)) from exc
        session, session_started = self._ensure_work_session(updated.id)
        ide = resolve_preferred_ide(updated, config)

        if ide == "explorer":
            return updated, self._explorer_outcome(
                updated,
                session,
                session_started,
                fallback_used=False,
                editor=None,
                extra_message=f"Opened {updated.name} in File Explorer.",
                launch_explorer=launch_explorer,
                folder=folder,
            )

        if ide in {"cursor", "vscode"}:
            try:
                launch_editor(ide, folder)
                label = _editor_display_name(ide)
                verb = "Started" if session_started else "Resumed"
                return updated, LaunchOutcome(
                    action="editor",
                    editor=ide,
                    message=f"{verb} session and opened {updated.name} in {label}.",
                    session_id=session.id if session else None,
                    session_started=session_started,
                    fallback_used=False,
                    open_explorer=False,
                )
            except WorkflowLaunchError as exc:
                logger.warning("Editor launch failed (%s); falling back to Explorer", exc)
                label = _editor_display_name(ide)
                return updated, self._explorer_outcome(
                    updated,
                    session,
                    session_started,
                    fallback_used=True,
                    editor=ide,
                    extra_message=(
                        f"{label} is not available ({exc}). "
                        f"Opened {updated.name} in File Explorer instead."
                    ),
                    launch_explorer=launch_explorer,
                    folder=folder,
                )

        hint = 'Choose an editor under Settings → "Open projects with".'
        return updated, self._explorer_outcome(
            updated,
            session,
            session_started,
            fallback_used=False,
            editor=None,
            extra_message=(
                f"No editor available for {updated.name}. "
                f"Opened folder in File Explorer. {hint}"
            ),
            launch_explorer=launch_explorer,
            folder=folder,
        )

    def _explorer_outcome(
        self,
        updated: ProjectRecord,
        session: WorkSessionRecord | None,
        session_started: bool,
        *,
        fallback_used: bool,
        editor: str | None,
        extra_message: str,
        launch_explorer: bool,
        folder: Path,
    ) -> LaunchOutcome:
        """Open Explorer once in-process, or defer to desktop Rust (open_explorer=True)."""
        if launch_explorer:
            open_folder_in_explorer(folder)
            open_explorer = False
        else:
            open_explorer = True
        return LaunchOutcome(
            action="explorer",
            editor=editor,
            message=extra_message,
            session_id=session.id if session else None,
            session_started=session_started,
            fallback_used=fallback_used,
            open_explorer=open_explorer,
        )

    def _ensure_work_session(
        self, project_id: int
    ) -> tuple[WorkSessionRecord | None, bool]:
        """Reuse an active session or start a new one for workflow continuity."""
        active = self._sessions.get_active_session(project_id)
        if active is not None:
            return active, False
        try:
            started = self._sessions.start_session(project_id)
            return started, True
        except SessionError as exc:
            logger.warning("Could not start session on open: %s", exc)
            active = self._sessions.get_active_session(project_id)
            if active is not None:
                return active, False
            raise WorkflowLaunchError(str(exc)) from exc


def open_folder_in_explorer(folder: Path) -> None:
    """Open the project root directory in the platform file manager."""
    path = folder.resolve()
    if not path.is_dir():
        raise WorkflowLaunchError(f"Project folder does not exist: {path}")

    try:
        if sys.platform == "win32":
            subprocess.Popen(  # noqa: S603
                ["explorer", str(path)],
                start_new_session=True,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], start_new_session=True)  # noqa: S603
        else:
            subprocess.Popen(["xdg-open", str(path)], start_new_session=True)  # noqa: S603
    except OSError as exc:
        raise WorkflowLaunchError(
            f"Could not open folder in the file manager: {exc}"
        ) from exc


def _find_editor_executable(ide: str) -> str:
    """Resolve cursor or vscode CLI on PATH."""
    candidates: list[str]
    if ide == "cursor":
        candidates = ["cursor", "cursor.cmd"]
    elif ide == "vscode":
        candidates = ["code", "code.cmd"]
    else:
        raise WorkflowLaunchError(f"Unsupported editor: {ide}")

    for name in candidates:
        found = shutil.which(name)
        if found:
            return found

    label = "Cursor" if ide == "cursor" else "VS Code"
    raise WorkflowLaunchError(
        f"{label} was not found on PATH. Install it or add it to PATH, "
        "or set preferred_ide to explorer."
    )


def launch_editor(ide: str, folder: Path) -> None:
    """Launch Cursor or VS Code on a project folder (detached process)."""
    path = folder.resolve()
    if not path.is_dir():
        raise WorkflowLaunchError(f"Project folder does not exist: {path}")

    executable = _find_editor_executable(ide)
    try:
        subprocess.Popen(  # noqa: S603
            [executable, str(path)],
            cwd=str(path),
            start_new_session=True,
        )
    except OSError as exc:
        label = "Cursor" if ide == "cursor" else "VS Code"
        raise WorkflowLaunchError(f"Failed to start {label}: {exc}") from exc

    logger.info("Launched %s for %s", ide, path)
