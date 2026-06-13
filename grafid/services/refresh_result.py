"""Structured refresh outcome for IPC and UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class RefreshResult:
    """Result of a project context refresh (scan + optional git)."""

    scan_ok: bool
    snapshot_id: int | None = None
    scan_error: str | None = None
    git_ok: bool = True
    git_error: str | None = None
    warnings_count: int = 0
    skipped_files_count: int = 0
    snapshots_pruned: int = 0
    mode: str = "full"  # full | git_only

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ScanHealthReport:
    """Diagnostics surfaced in settings / refresh response."""

    warnings_count: int = 0
    skipped_files_count: int = 0
    scanned_files_count: int = 0
    findings_count: int = 0
    duration_seconds: float = 0.0
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
