"""Tests for startup card IPC (Milestone 9)."""

from __future__ import annotations

from grafid.ipc.handlers import handle_bootstrap
from grafid.ipc.startup_handlers import (
    build_startup_card,
    handle_dismiss_startup,
    handle_resume_preview,
)
from grafid.services.startup_summary_service import StartupSummaryService


def test_bootstrap_includes_startup_card(db_path, config_manager, project_id: int) -> None:
    response = handle_bootstrap(config_manager=config_manager)
    assert response.ok is True
    card = response.data["startup_card"]
    assert card is not None
    assert card["project_id"] == project_id
    assert "scroll_content" in card
    assert "blocker" in card
    assert card["visible"] is True


def test_dismiss_startup_hides_card(db_path, config_manager, project_id: int) -> None:
    service = StartupSummaryService(db_path)
    summary = service.run_flow(persist=True)
    assert summary.project_id == project_id

    dismiss = handle_dismiss_startup(project_id, summary.startup_summary_id, config_manager)
    assert dismiss.ok is True
    assert dismiss.data["dismissed"] is True

    record = service.get_latest(project_id)
    assert record is not None
    assert record.is_dismissed is True

    card = build_startup_card(db_path, summary, record=record)
    assert card["visible"] is False
    assert card["is_dismissed"] is True


def test_resume_preview_ipc(db_path, config_manager, project_id: int) -> None:
    response = handle_resume_preview(project_id, config_manager)
    assert response.ok is True
    preview = response.data["resume_preview"]
    assert "blocker" in preview
    assert "modified_files" in preview


def test_build_startup_card_empty_when_no_projects(db_path, config_manager) -> None:
    service = StartupSummaryService(db_path)
    summary = service.run_flow(persist=True)
    card = build_startup_card(db_path, summary)
    assert card["visible"] is False
    assert card["reason"] == "empty_project"


def test_startup_card_visible_flag_matches_record(db_path, config_manager, project_id: int) -> None:
    service = StartupSummaryService(db_path)
    summary = service.run_flow(persist=True)
    record = service.get_latest(project_id)
    card = build_startup_card(db_path, summary, record=record)
    assert card["visible"] == (record is not None and not record.is_dismissed)
