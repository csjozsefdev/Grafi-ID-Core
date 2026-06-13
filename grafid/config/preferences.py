"""User preference keys and validation for config.json."""

from __future__ import annotations

from typing import Any

from grafid.core.exceptions import ConfigError

DEFAULT_PROJECT_OPENER_KEY = "default_project_opener"

_VALID_OPENER_TOKENS = frozenset({"cursor", "vscode", "explorer", "system"})

_UI_OPENER_OPTIONS: tuple[tuple[str, str], ...] = (
    ("system", "System default"),
    ("cursor", "Cursor"),
    ("vscode", "VS Code"),
    ("explorer", "Explorer only"),
)


def list_opener_options() -> list[dict[str, str]]:
    """Options for the Settings UI."""
    return [{"id": token, "label": label} for token, label in _UI_OPENER_OPTIONS]


def normalize_default_project_opener(value: Any) -> str:
    """
    Normalize stored opener preference.

    Returns one of: system, cursor, vscode, explorer.
    Invalid values raise ConfigError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return "system"
    token = str(value).strip().lower()
    aliases = {
        "code": "vscode",
        "vs code": "vscode",
        "vs_code": "vscode",
        "explorer only": "explorer",
        "folder": "explorer",
        "file explorer": "explorer",
    }
    normalized = aliases.get(token, token)
    if normalized not in _VALID_OPENER_TOKENS:
        raise ConfigError(
            f"Invalid {DEFAULT_PROJECT_OPENER_KEY} '{value}'. "
            "Use system, cursor, vscode, or explorer."
        )
    return normalized


def opener_to_ide_token(stored: str | None) -> str | None:
    """
    Map settings value to workflow IDE token (cursor, vscode, explorer).

    system -> None (workflow picks editor if on PATH, else Explorer).
    """
    if stored is None:
        return None
    token = normalize_default_project_opener(stored)
    if token == "system":
        return None
    return token
