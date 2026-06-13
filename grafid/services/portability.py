"""Export/import zip bundle for backup and machine migration."""

from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from grafid.core.constants import SCHEMA_VERSION
from grafid.core.exceptions import DatabaseError, ValidationError
from grafid.db.schema import get_schema_version
from grafid.utils.logging_setup import get_logger

logger = get_logger("portability")

EXPORT_SPEC_VERSION = 1
MANIFEST_NAME = "grafid-export.json"
BUNDLE_DB_NAME = "graf-id.db"
BUNDLE_CONFIG_NAME = "config.json"


def _export_manifest(*, project_count: int) -> dict[str, object]:
    return {
        "spec_version": EXPORT_SPEC_VERSION,
        "schema_version": SCHEMA_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "app": "Graph-Id",
        "project_count": project_count,
    }


def export_bundle(
    *,
    db_path: Path,
    config_path: Path,
    output_zip: Path,
) -> Path:
    """Create a portable zip: database, config, manifest, readme."""
    if not db_path.is_file():
        raise ValidationError(f"Database not found: {db_path}")
    output_zip = output_zip.expanduser().resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with DatabaseConnection_ro(db_path) as conn:
        version = get_schema_version(conn)
        if version is None or version > SCHEMA_VERSION:
            raise DatabaseError(f"Unsupported schema version in database: {version}")
        project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]

    manifest = _export_manifest(project_count=int(project_count))
    readme = (
        "# Graph-Id export bundle\n\n"
        "Import with: graf-id import <path.zip>\n"
        f"Schema version: {SCHEMA_VERSION}\n"
    )

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, BUNDLE_DB_NAME)
        if config_path.is_file():
            zf.write(config_path, BUNDLE_CONFIG_NAME)
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2))
        zf.writestr("README.md", readme)

    logger.info("Exported bundle to %s", output_zip)
    return output_zip


def import_bundle(
    *,
    zip_path: Path,
    config_dir: Path,
    replace: bool = False,
) -> Path:
    """Restore database and config from an export zip."""
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file():
        raise ValidationError(f"Export file not found: {zip_path}")

    config_dir.mkdir(parents=True, exist_ok=True)
    db_dest = config_dir / BUNDLE_DB_NAME
    config_dest = config_dir / BUNDLE_CONFIG_NAME

    if db_dest.exists() and not replace:
        raise ValidationError(
            f"Database already exists at {db_dest}. Use --replace to overwrite."
        )

    with zipfile.ZipFile(zip_path, "r") as zf:
        if MANIFEST_NAME not in zf.namelist():
            raise ValidationError(f"Invalid bundle: missing {MANIFEST_NAME}")
        manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
        schema = manifest.get("schema_version")
        if isinstance(schema, int) and schema > SCHEMA_VERSION:
            raise ValidationError(
                f"Bundle schema {schema} is newer than this app ({SCHEMA_VERSION})"
            )
        if BUNDLE_DB_NAME not in zf.namelist():
            raise ValidationError(f"Invalid bundle: missing {BUNDLE_DB_NAME}")
        zf.extract(BUNDLE_DB_NAME, config_dir)
        if BUNDLE_CONFIG_NAME in zf.namelist():
            zf.extract(BUNDLE_CONFIG_NAME, config_dir)

    from grafid.services.db_init import DatabaseInitService

    DatabaseInitService(db_dest).initialize(verify=True)
    logger.info("Imported bundle into %s", config_dir)
    return db_dest


class DatabaseConnection_ro:
    """Minimal read-only connection for export."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(self, *args: object) -> None:
        if self._conn:
            self._conn.close()


def vacuum_database(db_path: Path) -> None:
    """Run SQLite VACUUM maintenance."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("VACUUM")
        conn.commit()
    finally:
        conn.close()
