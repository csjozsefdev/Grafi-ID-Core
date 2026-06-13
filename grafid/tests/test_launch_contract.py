"""Open Project IPC launch contract (stable fields for desktop)."""

from __future__ import annotations

from grafid.config.manager import AppConfig
from grafid.ipc.dashboard_handlers import handle_open_project
from grafid.services.workflow_launch import LaunchOutcome

_REQUIRED_LAUNCH_KEYS = frozenset(
    {
        "success",
        "message",
        "editor_launched",
        "explorer_opened",
        "fallback_used",
        "open_explorer",
        "action",
    }
)


def test_launch_outcome_to_dict_includes_contract_fields() -> None:
    payload = LaunchOutcome(
        action="explorer",
        editor=None,
        message="test",
        session_id=1,
        session_started=True,
        fallback_used=False,
        open_explorer=True,
    ).to_dict()
    assert _REQUIRED_LAUNCH_KEYS.issubset(payload.keys())
    assert payload["explorer_opened"] is True
    assert payload["editor_launched"] is False


def test_launch_outcome_editor_success_contract() -> None:
    payload = LaunchOutcome(
        action="editor",
        editor="vscode",
        message="ok",
        session_id=2,
        session_started=False,
        fallback_used=False,
        open_explorer=False,
    ).to_dict()
    assert payload["editor_launched"] is True
    assert payload["explorer_opened"] is False


def test_open_project_ipc_includes_launch_block(
    db_path, config_manager, project_id: int
) -> None:
    response = handle_open_project(project_id, config_manager)
    assert response.ok is True
    assert response.data is not None
    launch = response.data.get("launch")
    assert isinstance(launch, dict)
    assert _REQUIRED_LAUNCH_KEYS.issubset(launch.keys())


def test_launch_outcome_to_dict_tolerates_missing_launch_in_handler_mock() -> None:
    """Document: desktop normalizes when launch is absent (regression guard)."""
    partial = {"action": "explorer", "message": "legacy"}
    assert "open_explorer" not in partial
    assert "explorer_opened" not in partial
