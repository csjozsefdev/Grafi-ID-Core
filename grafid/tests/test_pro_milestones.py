"""PRO milestone regression tests."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from grafid.core.constants import SCHEMA_VERSION
from grafid.db.connection import DatabaseConnection
from grafid.db.migrations import run_pending_migrations
from grafid.db.schema import apply_schema, get_schema_version
from grafid.scanner.grafidignore import load_grafidignore
from grafid.services.retention_policy import DEFAULT_RETENTION_POLICY
from grafid.services.snapshot_retention import SnapshotRetentionService


def test_schema_version_is_pro_ten() -> None:
    assert SCHEMA_VERSION == 10


def test_migration_runner_reaches_v10(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    with DatabaseConnection(db) as conn:
        apply_schema(conn)
        version = get_schema_version(conn)
    assert version == 10


def test_retention_policy_enabled_by_default() -> None:
    assert DEFAULT_RETENTION_POLICY.cleanup_enabled() is True


def test_grafidignore_loads_patterns(tmp_path: Path) -> None:
    (tmp_path / ".grafidignore").write_text("# comment\n.next\ndist\n", encoding="utf-8")
    names = load_grafidignore(tmp_path)
    assert "dist" in names or ".next" in names


def test_export_bundle_manifest(tmp_path: Path, config_manager) -> None:
    from grafid.services.db_init import DatabaseInitService
    from grafid.services.portability import export_bundle

    config = config_manager.load()
    db_path = config.resolved_database_path(config_manager.config_dir)
    DatabaseInitService(db_path).initialize(verify=False)
    zip_path = tmp_path / "bundle.zip"
    export_bundle(db_path=db_path, config_path=config_manager.config_path, output_zip=zip_path)
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as zf:
        assert "grafid-export.json" in zf.namelist()
        manifest = json.loads(zf.read("grafid-export.json"))
        assert manifest["schema_version"] == SCHEMA_VERSION


def test_summary_engine_away_label() -> None:
    from grafid.resume.summary_engine import compute_away_label

    label = compute_away_label(
        last_opened_at="2020-01-01T12:00:00+00:00",
        last_session_ended_at=None,
    )
    assert label is not None
    assert "Away" in label
