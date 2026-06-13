"""Directory ignore rules for filesystem scanning."""

from __future__ import annotations

import sys
from pathlib import Path

# Default folder names skipped anywhere in the project tree.
# Generated, vendor, cache, and build folders pollute workflow continuity
# signals (TODO/FIXME counts, resume summaries, startup headlines).
DEFAULT_IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".pytest_cache",
        ".cursor",
        "coverage",
        ".mypy_cache",
        ".tauri",
        ".next",
        "cache",
        "tmp",
        "temp",
    }
)

# Embedded/runtime paths where the directory name alone is too broad
# (e.g. keep grafid/runtime/ source but skip Tauri bundled Python trees).
DEFAULT_IGNORED_RELATIVE_PREFIXES: frozenset[str] = frozenset(
    {
        "desktop/src-tauri/runtime",
        "desktop/src-tauri/target",
        "desktop/dist",
        "desktop/node_modules",
    }
)


def _normalized_dir_name(name: str) -> str:
    return name.lower() if sys.platform == "win32" else name


def _normalize_relative_token(path: str) -> str:
    token = path.replace("\\", "/").strip("/")
    return token.lower() if sys.platform == "win32" else token


def build_ignore_lookup(dir_names: frozenset[str]) -> frozenset[str]:
    """Build a lookup set for fast directory name checks."""
    return frozenset(_normalized_dir_name(name) for name in dir_names)


def build_prefix_lookup(prefixes: frozenset[str]) -> frozenset[str]:
    """Normalize relative path prefixes for case-insensitive matching."""
    return frozenset(_normalize_relative_token(prefix) for prefix in prefixes)


def _relative_posix(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def should_ignore_dir(
    path: Path,
    ignored_lookup: frozenset[str],
    *,
    root: Path | None = None,
    ignored_prefix_lookup: frozenset[str] | None = None,
) -> bool:
    """Return True when a directory should be skipped entirely."""
    if _normalized_dir_name(path.name) in ignored_lookup:
        return True
    if root is None or not ignored_prefix_lookup:
        return False
    rel = _relative_posix(path, root)
    if rel is None:
        return False
    rel_norm = _normalize_relative_token(rel)
    for prefix in ignored_prefix_lookup:
        if rel_norm == prefix or rel_norm.startswith(f"{prefix}/"):
            return True
    return False
