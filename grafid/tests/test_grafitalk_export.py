"""GrafiTalk inbox export."""

from __future__ import annotations

import json
from pathlib import Path

from grafid.services.grafitalk_export import export_grafitalk_inbox


def test_export_grafitalk_inbox(tmp_path: Path, db_path, project_id: int) -> None:
    out = tmp_path / "grafitalk"
    inbox = export_grafitalk_inbox(db_path=db_path, output_dir=out, config_dir=tmp_path)
    assert inbox == out.resolve()
    manifest = json.loads((inbox / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["project_count"] >= 1
    assert manifest["spec_version"] == 1
    projects_dir = inbox / "projects"
    files = list(projects_dir.glob("*.json"))
    assert files
    body = json.loads(files[0].read_text(encoding="utf-8"))
    assert "resume_panel" in body
    assert "project" in body
    assert body["project"]["id"] == project_id
