"""Shared CLI runtime bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from grafid.config.manager import ConfigManager
from grafid.services.project_registry import ProjectRegistryService
from grafid.services.startup import StartupService

_runtime_cache: dict[str, CliRuntime] = {}


@dataclass(frozen=True)
class CliRuntime:
    """Initialized config, database, and project registry for CLI commands."""

    database_path: Path
    registry: ProjectRegistryService


def prepare_runtime(config_manager: ConfigManager | None = None) -> CliRuntime:
    """
    Ensure config, logging, database schema, and return a registry service.

    Reuses StartupService for consistent initialization without extra output.
    Cached per config directory within one Python process (IPC subprocess lifetime).
    """
    manager = config_manager or ConfigManager()
    cache_key = str(manager.config_dir.resolve())
    cached = _runtime_cache.get(cache_key)
    if cached is not None:
        return cached

    result = StartupService(config_manager=manager).run()
    runtime = CliRuntime(
        database_path=result.database_path,
        registry=ProjectRegistryService(result.database_path),
    )
    _runtime_cache[cache_key] = runtime
    return runtime


def clear_runtime_cache_for_tests() -> None:
    """Reset in-process runtime cache (tests only)."""
    _runtime_cache.clear()
