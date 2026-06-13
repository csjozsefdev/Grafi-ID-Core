"""Export project summaries to a GrafiTalk-readable inbox folder."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from grafid.db.connection import DatabaseConnection
from grafid.ipc.dashboard_handlers import _project_detail_payload
from grafid.services.project_registry import ProjectRegistryService
from grafid.utils.logging_setup import get_logger

logger = get_logger("grafitalk_export")

GRAFITALK_SPEC_VERSION = 1
PROJECTS_SUBDIR = "projects"
MANIFEST_NAME = "manifest.json"
README_NAME = "README.md"


def resolve_grafid_repo_root() -> Path | None:
    """Repository root (folder containing ``pyproject.toml`` / ``grafid/``)."""
    if raw := os.environ.get("GRAFID_REPO_ROOT"):
        candidate = Path(raw).expanduser()
        if candidate.is_dir():
            return candidate.resolve()

    here = Path(__file__).resolve()
    candidates = [here.parents[2], *here.parents]
    seen: set[Path] = set()
    for base in candidates:
        if base in seen:
            continue
        seen.add(base)
        if (base / "pyproject.toml").is_file() or (base / "grafid" / "__init__.py").is_file():
            return base
    return None


def default_grafitalk_dir(config_dir: Path | None = None) -> Path:
    """
    Default inbox: ``<Graf-Id repo>/grafitalk/``.

    Override with ``GRAFID_GRAFITALK_DIR``. Falls back to data dir only if repo root is unknown.
    """
    if raw := os.environ.get("GRAFID_GRAFITALK_DIR"):
        return Path(raw).expanduser().resolve()
    repo = resolve_grafid_repo_root()
    if repo is not None:
        return repo / "grafitalk"
    if config_dir is not None:
        return config_dir / "grafitalk"
    return Path.cwd() / "grafitalk"


def _safe_project_filename(project_id: int, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        slug = "project"
    return f"{project_id}-{slug[:60]}.json"


def _readme_text(inbox: Path) -> str:
    return (
        "# GrafiTalk inbox (Graph-Id)\n\n"
        "Read-only export of project resume summaries for GrafiTalk and other local tools.\n\n"
        "## Layout\n\n"
        f"- `{MANIFEST_NAME}` — index of exported projects\n"
        f"- `{PROJECTS_SUBDIR}/` — one JSON file per project\n\n"
        "## Refresh\n\n"
        "From a terminal with Graf-Id installed:\n\n"
        "```powershell\n"
        "graf-id export-grafitalk\n"
        "```\n\n"
        f"Default output folder: `{inbox}`\n"
    )


def export_grafitalk_inbox(
    *,
    db_path: Path,
    output_dir: Path | None = None,
    config_dir: Path | None = None,
) -> Path:
    """
    Write per-project summary JSON files for GrafiTalk consumption.

    Each file includes ``project`` metadata and ``resume_panel`` (headline, summary_text, sections).
    """
    if config_dir is None:
        config_dir = db_path.parent
    inbox = (output_dir or default_grafitalk_dir(config_dir)).expanduser().resolve()
    projects_dir = inbox / PROJECTS_SUBDIR
    projects_dir.mkdir(parents=True, exist_ok=True)

    exported_at = datetime.now(UTC).isoformat()
    registry = ProjectRegistryService(db_path)
    project_records = registry.list_projects()

    manifest_projects: list[dict[str, object]] = []

    with DatabaseConnection(db_path) as conn:
        for record in project_records:
            payload = _project_detail_payload(conn, db_path, record)
            filename = _safe_project_filename(int(record.id), str(record.name))
            file_path = projects_dir / filename

            project_export = {
                "spec_version": GRAFITALK_SPEC_VERSION,
                "exported_at": exported_at,
                "project": payload["project"],
                "resume_panel": payload["resume_panel"],
            }
            file_path.write_text(
                json.dumps(project_export, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            panel = payload.get("resume_panel") or {}
            manifest_projects.append(
                {
                    "project_id": int(record.id),
                    "name": record.name,
                    "path": str(record.path),
                    "file": f"{PROJECTS_SUBDIR}/{filename}",
                    "headline": panel.get("headline"),
                }
            )

    manifest = {
        "spec_version": GRAFITALK_SPEC_VERSION,
        "app": "Graph-Id",
        "exported_at": exported_at,
        "project_count": len(manifest_projects),
        "projects": manifest_projects,
    }
    (inbox / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (inbox / README_NAME).write_text(_readme_text(inbox), encoding="utf-8")

    logger.info("GrafiTalk inbox exported to %s (%s projects)", inbox, len(manifest_projects))
    return inbox
