"""Tests for workflow artifact detection."""

from __future__ import annotations

from pathlib import Path

from grafid.resume.workflow_artifacts import load_workflow_artifacts, primary_handoff


def test_detects_handoff_file(tmp_path: Path) -> None:
    project = tmp_path / "backend"
    project.mkdir()
    (project / "HANDOFF.md").write_text(
        "# Mesencsi project handoff\n\nFocus area: deployment / QA\n\nNext step: polish admin UI\n",
        encoding="utf-8",
    )
    artifacts = load_workflow_artifacts(str(project))
    handoff = primary_handoff(artifacts)
    assert handoff is not None
    assert handoff.title == "Mesencsi project handoff"
    assert handoff.focus_area == "deployment / QA"
    assert handoff.next_step_line == "polish admin UI"


def test_detects_readme_when_no_handoff(tmp_path: Path) -> None:
    project = tmp_path / "app"
    project.mkdir()
    (project / "README.md").write_text("# App readme\n\nSetup instructions here.\n", encoding="utf-8")
    artifacts = load_workflow_artifacts(str(project))
    assert any(a.kind == "readme" for a in artifacts)
    assert primary_handoff(artifacts) is None


def test_searches_parent_directory(tmp_path: Path) -> None:
    root = tmp_path / "mesencsi"
    backend = root / "backend"
    backend.mkdir(parents=True)
    (root / "HANDOFF.md").write_text("# Parent handoff\n", encoding="utf-8")
    artifacts = load_workflow_artifacts(str(backend))
    assert primary_handoff(artifacts) is not None


def test_allowlist_ignores_unlisted_md_files(tmp_path: Path) -> None:
    project = tmp_path / "app"
    project.mkdir()
    (project / "RANDOM_NOTES.md").write_text("# Should not load\n", encoding="utf-8")
    (project / "docs").mkdir()
    (project / "docs" / "ARCHITECTURE.md").write_text("# Also ignored\n", encoding="utf-8")
    artifacts = load_workflow_artifacts(str(project))
    assert artifacts == ()


def test_detects_exit_note_and_changelog(tmp_path: Path) -> None:
    project = tmp_path / "app"
    project.mkdir()
    (project / "EXIT_NOTE.md").write_text("# Exit\n\nShipped v1.\n", encoding="utf-8")
    (project / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0\n\nInitial release.\n", encoding="utf-8")
    artifacts = load_workflow_artifacts(str(project))
    kinds = {a.kind for a in artifacts}
    assert "exit_note" in kinds
    assert "changelog" in kinds
    assert all(a.priority_tier in {"high", "medium"} for a in artifacts)


def test_high_tier_sorted_before_medium(tmp_path: Path) -> None:
    project = tmp_path / "app"
    project.mkdir()
    (project / "README.md").write_text("# Readme\n\nSetup.\n", encoding="utf-8")
    (project / "NEXT.md").write_text("# Next\n\nDo the thing.\n", encoding="utf-8")
    artifacts = load_workflow_artifacts(str(project))
    assert artifacts[0].kind == "next"
    assert artifacts[0].priority_tier == "high"
    assert any(a.kind == "readme" for a in artifacts)
