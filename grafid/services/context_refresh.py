"""Bounded project context scan for refresh (no background daemon)."""



from __future__ import annotations



from pathlib import Path



from grafid.core.exceptions import ProjectError, ScanError

from grafid.git import GitReadService

from grafid.scanner import ProjectScannerService

from grafid.services.project_registry import ProjectRegistryService

from grafid.services.refresh_result import RefreshResult, ScanHealthReport

from grafid.services.snapshot_persistence import SnapshotPersistenceService

from grafid.services.snapshot_retention import SnapshotRetentionService

from grafid.utils.logging_setup import get_logger



logger = get_logger("context_refresh")

def refresh_project_scan(

    db_path: Path,

    project_id: int,

    *,

    git_only: bool = False,

) -> RefreshResult:
    """

    Run bounded filesystem scan and/or git snapshot for one project.



    When git_only=True, skips filesystem walk and only persists git state

    against the latest snapshot when possible.

    """

    registry = ProjectRegistryService(db_path)

    record = registry.get_info(str(project_id))

    project_path = Path(record.path)

    if not project_path.is_dir():

        raise ProjectError(f"Project path is not accessible: {record.path}")



    scan_ok = True

    scan_error: str | None = None

    snapshot_id: int | None = None

    warnings_count = 0

    skipped_files_count = 0

    git_ok = True

    git_error: str | None = None



    git_state = None

    try:
        git_state = GitReadService().collect(project_path)

    except Exception as exc:  # noqa: BLE001 — git optional

        git_ok = False

        git_error = str(exc)

        logger.warning("Git collection failed for %s: %s", project_path, exc)



    if git_only:

        from grafid.db.connection import DatabaseConnection

        from grafid.db.repositories.snapshot_repository import SnapshotRepository



        with DatabaseConnection(db_path) as conn:

            latest = SnapshotRepository(conn).list_history_for_project(project_id, limit=1)

        if latest and git_state is not None:

            snapshot_id = latest[0].id

        result = RefreshResult(

            scan_ok=True,

            snapshot_id=snapshot_id,

            git_ok=git_ok,

            git_error=git_error,

            mode="git_only",

        )
        return result



    scanner = ProjectScannerService()

    try:
        scan_result = scanner.scan_project(project_path)

        warnings_count = len(scan_result.warnings)

        skipped_files_count = scan_result.skipped_count

    except ScanError as exc:

        scan_ok = False

        scan_error = str(exc)

        logger.warning("Scan failed for project_id=%s: %s", project_id, exc)

        result = RefreshResult(

            scan_ok=False,

            scan_error=scan_error,

            git_ok=git_ok,

            git_error=git_error,

            mode="full",

        )
        return result



    snapshot = SnapshotPersistenceService(db_path).save_snapshot(

        project_id,

        scan_result,

        git_state=git_state,

    )

    snapshot_id = snapshot.id

    logger.info(

        "Context refresh scan persisted snapshot_id=%s project_id=%s",

        snapshot.id,

        project_id,

    )



    from grafid.db.connection import DatabaseConnection



    pruned = 0

    with DatabaseConnection(db_path) as conn:

        pruned = SnapshotRetentionService(db_path).apply_for_project(

            project_id, connection=conn

        )

        conn.commit()



    result = RefreshResult(

        scan_ok=True,

        snapshot_id=snapshot_id,

        git_ok=git_ok,

        git_error=git_error,

        warnings_count=warnings_count,

        skipped_files_count=skipped_files_count,

        snapshots_pruned=pruned,

        mode="full",

    )
    return result





def build_scan_health_from_refresh(result: RefreshResult) -> ScanHealthReport:

    """Map refresh result to a scan health report for UI."""

    messages: list[str] = []

    if not result.scan_ok and result.scan_error:

        messages.append(result.scan_error)

    if not result.git_ok and result.git_error:

        messages.append(f"Git: {result.git_error}")

    if result.warnings_count:

        messages.append(f"{result.warnings_count} scan warning(s)")

    if result.skipped_files_count:

        messages.append(f"{result.skipped_files_count} file(s) skipped")

    if result.snapshots_pruned:

        messages.append(f"{result.snapshots_pruned} old snapshot(s) pruned")

    return ScanHealthReport(

        warnings_count=result.warnings_count,

        skipped_files_count=result.skipped_files_count,

        messages=messages,

    )

