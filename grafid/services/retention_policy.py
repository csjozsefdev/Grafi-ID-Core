"""Placeholder retention rules for future snapshot cleanup."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetentionPolicy:
    """
    Future automatic cleanup configuration (not active in Milestone 2C).

    When cleanup is implemented, this policy will cap snapshot count or age
    per project without changing scanner or persistence APIs.
    """

    max_snapshots_per_project: int | None = None
    max_age_days: int | None = None

    def cleanup_enabled(self) -> bool:
        """True when at least one retention rule is configured."""
        return bool(
            (self.max_snapshots_per_project and self.max_snapshots_per_project > 0)
            or (self.max_age_days and self.max_age_days > 0)
        )


DEFAULT_RETENTION_POLICY = RetentionPolicy(
    max_snapshots_per_project=30,
    max_age_days=90,
)
