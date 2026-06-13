"""Parse read-only git status --porcelain output."""

from __future__ import annotations


def parse_porcelain_status(output: str) -> tuple[list[str], list[str], bool]:
    """
    Parse porcelain status lines into staged paths, modified paths, and dirty flag.

    Follows git status --porcelain v1 format (XY PATH).
    """
    staged: list[str] = []
    modified: list[str] = []
    seen_staged: set[str] = set()
    seen_modified: set[str] = set()

    for raw_line in output.splitlines():
        line = raw_line.rstrip("\r")
        if not line or len(line) < 3:
            continue

        x_status = line[0]
        y_status = line[1]
        path = _extract_path(line[3:])

        if x_status != " " and x_status != "?":
            if path not in seen_staged:
                staged.append(path)
                seen_staged.add(path)

        if y_status != " " and y_status != "?":
            if path not in seen_modified:
                modified.append(path)
                seen_modified.add(path)

    is_dirty = bool(staged or modified)
    return staged, modified, is_dirty


def _extract_path(raw: str) -> str:
    """Extract path from porcelain line, handling quoted paths."""
    text = raw.strip()
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return text
