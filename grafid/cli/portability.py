"""Export, import, and maintenance CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from grafid.config.manager import ConfigManager
from grafid.core.exceptions import ConfigError, DatabaseError, GrafIdError, ValidationError
from grafid.core.exceptions import PermissionError as GrafPermissionError
from grafid.services.portability import export_bundle, import_bundle, vacuum_database
from grafid.services.snapshot_retention import SnapshotRetentionService

def _paths() -> tuple[Path, Path, Path]:
    manager = ConfigManager()
    config = manager.load()
    config_dir = manager.config_dir
    db_path = config.resolved_database_path(config_dir)
    return config_dir, db_path, manager.config_path


def export_cmd(
    output: Path = typer.Argument(help="Output .zip path."),
) -> None:
    """Export database + config to a portable zip."""
    try:
        config_dir, db_path, config_path = _paths()
        out = output if output.suffix else output.with_suffix(".zip")
        path = export_bundle(db_path=db_path, config_path=config_path, output_zip=out)
    except (ValidationError, DatabaseError, ConfigError, GrafPermissionError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Exported to {path}")


def import_cmd(
    bundle: Path = typer.Argument(help="Path to export .zip."),
    replace: bool = typer.Option(False, "--replace", help="Overwrite existing database."),
) -> None:
    """Import a portable zip into the local config directory."""
    try:
        config_dir, _, _ = _paths()
        db_path = import_bundle(zip_path=bundle, config_dir=config_dir, replace=replace)
    except (ValidationError, DatabaseError, ConfigError, GrafPermissionError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Imported database: {db_path}")


maintenance_app = typer.Typer(help="Local database maintenance.")


@maintenance_app.command("vacuum")
def vacuum_cmd() -> None:
    """Run SQLite VACUUM on the local database."""
    try:
        _, db_path, _ = _paths()
        vacuum_database(db_path)
    except (ConfigError, GrafPermissionError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Vacuum complete: {db_path}")


@maintenance_app.command("prune-snapshots")
def prune_snapshots_cmd() -> None:
    """Apply snapshot retention policy for all projects."""
    try:
        _, db_path, _ = _paths()
        removed = SnapshotRetentionService(db_path).apply_all()
    except (ConfigError, DatabaseError, GrafPermissionError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Pruned {removed} snapshot(s)")
