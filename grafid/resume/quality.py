"""Resume readability helpers (deterministic noise reduction)."""

from __future__ import annotations

from typing import Literal

SummaryPurpose = Literal["resume", "startup"]

# Canonical lowercase phrases treated as empty / skipped (exact match after cleanup).
PLACEHOLDER_PHRASES: frozenset[str] = frozenset(
    {
        "",
        "-",
        ".",
        "nil",
        "null",
        "none",
        "n/a",
        "na",
        "ok",
        "nothing",
        "no",
        "no blocker",
        "no blockers",
        "no next step",
        "no next steps",
        "no note",
        "no notes",
        "no exit note",
        "nothing to report",
        "not applicable",
    }
)

MAX_SCROLL_CHARS_RESUME = 12_000
MAX_SCROLL_CHARS_STARTUP = 6_000
MAX_HEADLINE_CHARS = 160


def canonical_note_text(value: str) -> str:
    """Normalize user text for deterministic placeholder comparison."""
    cleaned = " ".join(value.strip().split()).lower()
    return cleaned.rstrip(".,!?;:")


def is_meaningful_text(value: str | None) -> bool:
    """Return True when text should appear in a user-facing summary."""
    if value is None:
        return False
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return False
    return canonical_note_text(cleaned) not in PLACEHOLDER_PHRASES


def normalize_note(value: str | None) -> str | None:
    """Strip and drop placeholder / low-value notes."""
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    if not is_meaningful_text(cleaned):
        return None
    return cleaned


def build_headline(
    *,
    project_name: str,
    exit_note: str | None,
    blocker: str | None,
    next_step: str | None,
    open_task_count: int,
    has_unfinished_session: bool,
) -> str:
    """One-line startup headline from highest-priority available fact."""
    if has_unfinished_session:
        base = "You have an active session for this project."
    elif blocker:
        base = f"Blocker: {blocker}"
    elif next_step:
        base = f"Next: {next_step}"
    elif exit_note:
        base = f"Last done: {exit_note}"
    elif open_task_count > 0:
        base = f"{open_task_count} open task marker(s) in this project"
    else:
        base = "No prior context recorded yet"

    if len(base) > MAX_HEADLINE_CHARS:
        return base[: MAX_HEADLINE_CHARS - 3].rstrip() + "..."
    return base


def truncate_scroll_content(text: str, *, purpose: SummaryPurpose) -> str:
    """Cap scrollable body size with an explicit truncation marker."""
    limit = (
        MAX_SCROLL_CHARS_STARTUP if purpose == "startup" else MAX_SCROLL_CHARS_RESUME
    )
    if len(text) <= limit:
        return text
    marker = "\n... (truncated for display; full data remains in the database)"
    keep = limit - len(marker)
    return text[:keep].rstrip() + marker


def compact_section_title(title: str) -> str:
    """Shorter section labels for startup summaries."""
    mapping = {
        "Last session note (done)": "Done",
        "Current blocker": "Blocker",
        "Next step": "Next",
        "Unfinished task markers": "Tasks",
        "Last active files": "Files",
        "Modified files": "Modified",
        "Context": "Info",
    }
    return mapping.get(title, title)
