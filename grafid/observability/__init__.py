"""Local-only usage observation (no network telemetry)."""

from grafid.observability.journal import (
    journal_path_for,
    record_event,
    summarize_journal,
)
from grafid.observability.settings import debug_timing_enabled, usage_journal_enabled
from grafid.observability.timing import TimingCollector, timed_block

__all__ = [
    "TimingCollector",
    "debug_timing_enabled",
    "journal_path_for",
    "record_event",
    "summarize_journal",
    "timed_block",
    "usage_journal_enabled",
]
