"""IPC handlers for app settings (config.json)."""

from __future__ import annotations

from grafid.config.manager import AppConfig, ConfigManager
from grafid.config.preferences import (
    DEFAULT_PROJECT_OPENER_KEY,
    list_opener_options,
    normalize_default_project_opener,
)
from grafid.core.exceptions import ConfigError, GrafIdError
from grafid.ipc.envelope import IpcResponse, failure, success
from grafid.ipc.handlers import _error_code
from grafid.observability.settings import debug_timing_enabled, usage_journal_enabled


def _parse_bool_flag(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _default_settings_payload(
    manager: ConfigManager,
    config: AppConfig | None = None,
) -> dict[str, object]:
    """Stable settings shape with safe defaults when config is missing or invalid."""
    cfg = config or AppConfig()
    data_dir = manager.config_dir
    logs_dir = cfg.resolved_log_dir(data_dir)
    opener = getattr(cfg, "default_project_opener", None) or "system"
    extra = getattr(cfg, "extra", {}) or {}
    compact = bool(extra.get("compact_mode", False))
    return {
        "data_dir": str(data_dir),
        "logs_dir": str(logs_dir),
        "config_dir": str(data_dir),
        "config_path": str(manager.config_path),
        DEFAULT_PROJECT_OPENER_KEY: opener,
        "usage_journal_enabled": usage_journal_enabled(cfg),
        "debug_timing_enabled": debug_timing_enabled(cfg),
        "compact_mode": compact,
        "opener_options": list_opener_options(),
    }


def _load_config_safe(manager: ConfigManager) -> AppConfig:
    try:
        return manager.load()
    except ConfigError:
        return AppConfig()


def handle_get_app_settings(
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Return user-facing settings for the desktop UI."""
    try:
        manager = config_manager or ConfigManager()
        config = _load_config_safe(manager)
        payload = _default_settings_payload(manager, config)
        return success(payload)
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_save_app_settings(
    opener: str,
    usage_journal: str | bool,
    debug_timing: str | bool,
    compact_mode: str | bool | None = None,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Persist app settings to config.json."""
    try:
        manager = config_manager or ConfigManager()
        normalized_opener = normalize_default_project_opener(opener)
        current = _load_config_safe(manager)
        extra = dict(current.extra)
        if compact_mode is not None:
            extra["compact_mode"] = _parse_bool_flag(compact_mode)
        updated = AppConfig(
            database_path=current.database_path,
            log_level=current.log_level,
            usage_journal=_parse_bool_flag(usage_journal),
            debug_timing=_parse_bool_flag(debug_timing),
            default_project_opener=normalized_opener,
            extra=extra,
        )
        manager.save(updated)
        payload = _default_settings_payload(manager, updated)
        payload["message"] = "Settings saved."
        return success(payload)
    except ConfigError as exc:
        return failure("config_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_reset_app_settings(
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Reset settings to application defaults."""
    try:
        manager = config_manager or ConfigManager()
        current = _load_config_safe(manager)
        defaults = AppConfig(
            database_path=current.database_path,
            log_level="INFO",
            usage_journal=False,
            debug_timing=False,
            default_project_opener="system",
            extra={},
        )
        manager.save(defaults)
        payload = _default_settings_payload(manager, defaults)
        payload["message"] = "Settings reset to defaults."
        return success(payload)
    except ConfigError as exc:
        return failure("config_error", str(exc))
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))


def handle_set_default_project_opener(
    opener: str,
    config_manager: ConfigManager | None = None,
) -> IpcResponse:
    """Persist default_project_opener only (legacy IPC)."""
    try:
        manager = config_manager or ConfigManager()
        current = _load_config_safe(manager)
        return handle_save_app_settings(
            opener,
            current.usage_journal,
            current.debug_timing,
            config_manager=manager,
        )
    except GrafIdError as exc:
        return failure(_error_code(exc), str(exc))
