"""Deterministic workflow artifact detection — MVP allowlist only."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# kind -> sort order within tier (lower = higher priority)
KIND_ORDER: dict[str, int] = {
    "handoff": 0,
    "next": 1,
    "session": 2,
    "exit_note": 3,
    "todo": 4,
    "notes": 5,
    "readme": 6,
    "changelog": 7,
}

# MVP allowlist: (filename, kind, tier). No other files are read.
ALLOWED_WORKFLOW_FILES: tuple[tuple[str, str, str], ...] = (
    # Highest priority
    ("HANDOFF.md", "handoff", "high"),
    ("handoff.md", "handoff", "high"),
    ("PROJECT_HANDOFF.md", "handoff", "high"),
    ("HANDOVER.md", "handoff", "high"),
    ("handover.md", "handoff", "high"),
    ("NEXT.md", "next", "high"),
    ("SESSION.md", "session", "high"),
    ("EXIT_NOTE.md", "exit_note", "high"),
    # Medium priority
    ("TODO.md", "todo", "medium"),
    ("NOTES.md", "notes", "medium"),
    ("README.md", "readme", "medium"),
    ("CHANGELOG.md", "changelog", "medium"),
)

ALLOWED_LINK_TARGETS = frozenset(name for name, _kind, tier in ALLOWED_WORKFLOW_FILES if tier == "high")

MAX_READ_BYTES = 12_000
MAX_PREVIEW_LINES = 4
MAX_LINE_CHARS = 160

NEXT_STEP_PATTERNS = (
    re.compile(r"^next step\s*:\s*(.+)$", re.I),
    re.compile(r"^next\s*:\s*(.+)$", re.I),
)
FOCUS_PATTERNS = (
    re.compile(r"^focus area\s*:\s*(.+)$", re.I),
    re.compile(r"^focus\s*:\s*(.+)$", re.I),
    re.compile(r"^current focus\s*:\s*(.+)$", re.I),
    re.compile(r"^current work\s*:\s*(.+)$", re.I),
    re.compile(r"^in progress\s*:\s*(.+)$", re.I),
    re.compile(r"^working on\s*:\s*(.+)$", re.I),
)

BLOCKER_PATTERNS = (
    re.compile(r"^blockers?\s*:\s*(.+)$", re.I),
    re.compile(r"^blocked on\s*:\s*(.+)$", re.I),
    re.compile(r"^open issue\s*:\s*(.+)$", re.I),
)

UNFINISHED_PATTERNS = (
    re.compile(r"^remaining work\s*:\s*(.+)$", re.I),
    re.compile(r"^unfinished\s*:\s*(.+)$", re.I),
)

MILESTONE_HEADING_RE = re.compile(
    r"^##\s+Milestone\s+(\d+)\s*[—\-:]\s*(.+?)\s*$",
    re.I,
)

WORKFLOW_SECTION_HEADING_RE = re.compile(r"^#{1,3}\s+(.+)$")
WORKFLOW_SECTION_KEYWORDS = (
    "current focus",
    "current work",
    "in progress",
    "remaining",
    "unfinished",
    "blocker",
    "next step",
    "open issue",
    "polish",
    "refactor",
    "milestone",
)

MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
POINTER_LINE = re.compile(r"^\s*(see|refer to|read)\b.*\[.+\]\(.+\)", re.I)


@dataclass(frozen=True)
class WorkflowArtifact:
    """A workflow context file found on disk."""

    filename: str
    relative_path: str
    kind: str
    priority_tier: str
    title: str | None
    preview_lines: tuple[str, ...]
    focus_area: str | None
    next_step_line: str | None
    recent_work: str | None = None
    unfinished_items: tuple[str, ...] = ()
    blocker_items: tuple[str, ...] = ()


def load_workflow_artifacts(project_path: str) -> tuple[WorkflowArtifact, ...]:
    """Load only MVP allowlisted workflow files (project root + parent folder)."""
    root = Path(project_path).resolve()
    search_roots = _search_roots(root)
    allowlist = {name.lower(): (name, kind, tier) for name, kind, tier in ALLOWED_WORKFLOW_FILES}

    picked: list[Path] = []
    seen: set[str] = set()
    for base in search_roots:
        if not base.is_dir():
            continue
        for filename, kind, tier in ALLOWED_WORKFLOW_FILES:
            path = base / filename
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            picked.append(path)

    artifacts: list[WorkflowArtifact] = []
    for path in picked:
        parsed = _parse_artifact(path, root, allowlist)
        if parsed is not None:
            artifacts.append(parsed)

    artifacts.extend(_follow_allowlisted_links(picked, root, allowlist, seen))
    artifacts.extend(_discover_root_pattern_files(root, allowlist, seen))

    artifacts.sort(
        key=lambda item: (
            0 if item.priority_tier == "high" else 1,
            KIND_ORDER.get(item.kind, 99),
            item.filename.lower(),
        )
    )
    return tuple(artifacts)


def artifacts_for_tier(
    artifacts: tuple[WorkflowArtifact, ...], tier: str
) -> tuple[WorkflowArtifact, ...]:
    return tuple(a for a in artifacts if a.priority_tier == tier)


def primary_handoff(artifacts: tuple[WorkflowArtifact, ...]) -> WorkflowArtifact | None:
    for artifact in artifacts:
        if artifact.kind == "handoff":
            return artifact
    return None


def _follow_allowlisted_links(
    picked: list[Path],
    project_root: Path,
    allowlist: dict[str, tuple[str, str, str]],
    seen: set[str],
) -> list[WorkflowArtifact]:
    """Resolve links from README/CHANGELOG to high-priority allowlisted files only."""
    extras: list[WorkflowArtifact] = []
    for path in picked:
        if path.name.lower() not in {"readme.md", "changelog.md"}:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")[:MAX_READ_BYTES]
        except OSError:
            continue
        for _label, target_raw in MARKDOWN_LINK.findall(raw):
            target_name = Path(target_raw).name
            if target_name not in ALLOWED_LINK_TARGETS:
                continue
            target = (path.parent / target_raw).resolve()
            key = str(target)
            if key in seen or not target.is_file():
                continue
            seen.add(key)
            parsed = _parse_artifact(target, project_root, allowlist)
            if parsed is not None:
                extras.append(parsed)
    return extras


_ROOT_NOTE_PATTERNS = (
    "NOTE.md",
    "NOTES.md",
    "*HANDOFF*.md",
    "*HANDOVER*.md",
    "*TODO*.md",
    "PROJECT_NOTES.md",
)


def _discover_root_pattern_files(
    root: Path,
    allowlist: dict[str, tuple[str, str, str]],
    seen: set[str],
) -> list[WorkflowArtifact]:
    """Discover extra note/handoff markdown files in the project root only."""
    extras: list[WorkflowArtifact] = []
    if not root.is_dir():
        return extras
    for pattern in _ROOT_NOTE_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen or path.name.lower() in allowlist:
                continue
            seen.add(key)
            kind = "notes"
            tier = "medium"
            lower = path.name.lower()
            if "handoff" in lower or "handover" in lower:
                kind = "handoff"
                tier = "high"
            elif "todo" in lower:
                kind = "todo"
            dynamic_allowlist = {
                path.name.lower(): (path.name, kind, tier),
            }
            parsed = _parse_artifact(path, root, dynamic_allowlist)
            if parsed is not None:
                extras.append(parsed)
    return extras


def _search_roots(root: Path) -> list[Path]:
    roots = [root]
    parent = root.parent
    if parent != root and parent.is_dir():
        roots.append(parent)
    return roots


def _parse_artifact(
    path: Path,
    project_root: Path,
    allowlist: dict[str, tuple[str, str, str]],
) -> WorkflowArtifact | None:
    meta = allowlist.get(path.name.lower())
    if meta is None:
        return None
    _canonical_name, kind, tier = meta

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")[:MAX_READ_BYTES]
    except OSError:
        return None

    lines = [line.rstrip() for line in raw.splitlines()]
    title = _extract_title(lines)
    focus_area = _extract_labeled(lines, FOCUS_PATTERNS)
    next_step = _extract_labeled(lines, NEXT_STEP_PATTERNS)
    preview = _meaningful_preview(lines, title)
    recent_work = _extract_latest_milestone(lines) if kind == "readme" else None
    if not recent_work:
        recent_work = _extract_section_lead(lines)
    unfinished = tuple(_extract_bullets_for_sections(lines)[:3])
    blockers = tuple(_extract_labeled_all(lines, BLOCKER_PATTERNS)[:2])

    if (
        not preview
        and not title
        and not focus_area
        and not next_step
        and not recent_work
        and not unfinished
    ):
        return None

    try:
        rel = path.relative_to(project_root).as_posix()
    except ValueError:
        rel = path.name

    return WorkflowArtifact(
        filename=path.name,
        relative_path=rel,
        kind=kind,
        priority_tier=tier,
        title=title,
        preview_lines=preview,
        focus_area=focus_area,
        next_step_line=next_step,
        recent_work=recent_work,
        unfinished_items=unfinished,
        blocker_items=blockers,
    )


def _extract_title(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:MAX_LINE_CHARS]
    return None


def _extract_labeled(lines: list[str], patterns: tuple[re.Pattern[str], ...]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in patterns:
            match = pattern.match(stripped)
            if match:
                return match.group(1).strip()[:MAX_LINE_CHARS]
    return None


def _extract_labeled_all(
    lines: list[str], patterns: tuple[re.Pattern[str], ...]
) -> list[str]:
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        for pattern in patterns:
            match = pattern.match(stripped)
            if match:
                text = match.group(1).strip()[:MAX_LINE_CHARS]
                if text:
                    out.append(text)
    return out


def _extract_latest_milestone(lines: list[str]) -> str | None:
    candidates: list[tuple[int, str]] = []
    for line in lines:
        match = MILESTONE_HEADING_RE.match(line.strip())
        if match:
            candidates.append((int(match.group(1)), match.group(2).strip()[:MAX_LINE_CHARS]))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def _extract_section_lead(lines: list[str]) -> str | None:
    current_heading: str | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        heading_match = WORKFLOW_SECTION_HEADING_RE.match(stripped)
        if heading_match:
            current_heading = heading_match.group(1).strip()
            continue
        if stripped.startswith(("-", "*")) and current_heading:
            if not _heading_is_workflow(current_heading):
                continue
            bullet = stripped.lstrip("-* ").strip()
            if bullet:
                return bullet[:MAX_LINE_CHARS]
    return None


def _extract_bullets_for_sections(lines: list[str]) -> list[str]:
    current_heading: str | None = None
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        heading_match = WORKFLOW_SECTION_HEADING_RE.match(stripped)
        if heading_match:
            current_heading = heading_match.group(1).strip()
            continue
        if not stripped.startswith(("-", "*")) or not current_heading:
            continue
        lower = current_heading.lower()
        if not (
            _heading_is_workflow(current_heading)
            or any(w in lower for w in ("todo", "remaining", "unfinished", "fixme"))
        ):
            continue
        bullet = stripped.lstrip("-* ").strip()
        if bullet:
            out.append(bullet[:MAX_LINE_CHARS])
    return out


def _heading_is_workflow(heading: str) -> bool:
    lower = heading.lower()
    return any(keyword in lower for keyword in WORKFLOW_SECTION_KEYWORDS)


def _meaningful_preview(lines: list[str], title: str | None) -> tuple[str, ...]:
    out: list[str] = []
    title_lower = title.lower() if title else None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("-", "*", ">")):
            stripped = stripped.lstrip("-*> ").strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if title_lower and lower == title_lower:
            continue
        if any(p.match(stripped) for p in (*NEXT_STEP_PATTERNS, *FOCUS_PATTERNS)):
            continue
        if lower.startswith("```"):
            continue
        if POINTER_LINE.match(stripped):
            continue
        if _markdown_link_density(stripped) > 0.5:
            continue
        cleaned = _plain_text(stripped)
        if not cleaned:
            continue
        out.append(cleaned[:MAX_LINE_CHARS])
        if len(out) >= MAX_PREVIEW_LINES:
            break
    return tuple(out)


def _plain_text(line: str) -> str:
    text = MARKDOWN_LINK.sub(r"\1", line)
    text = re.sub(r"[*_`#>|]", "", text)
    return " ".join(text.split()).strip()


def _markdown_link_density(line: str) -> float:
    if not line.strip():
        return 0.0
    link_chars = sum(len(m.group(0)) for m in MARKDOWN_LINK.finditer(line))
    return link_chars / max(len(line), 1)
