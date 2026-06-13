"""Configurable source priority weights for workflow artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WEIGHTS: dict[str, int] = {
    "exit_note": 100,
    "handoff": 90,
    "next": 80,
    "session": 75,
    "blocker": 70,
    "todo": 50,
    "notes": 40,
    "readme": 30,
    "changelog": 20,
    "scan": 25,
    "git": 15,
}


@dataclass(frozen=True)
class SourceWeights:
    """Per-kind weights; higher wins in ranking."""

    weights: dict[str, int]

    @classmethod
    def defaults(cls) -> SourceWeights:
        return cls(weights=dict(DEFAULT_WEIGHTS))

    @classmethod
    def from_config_file(cls, config_path: Path) -> SourceWeights:
        if not config_path.is_file():
            return cls.defaults()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls.defaults()
        raw = data.get("source_weights") if isinstance(data, dict) else None
        if not isinstance(raw, dict):
            return cls.defaults()
        merged = dict(DEFAULT_WEIGHTS)
        for key, value in raw.items():
            if isinstance(key, str) and isinstance(value, int):
                merged[key] = value
        return cls(weights=merged)

    def score(self, kind: str) -> int:
        return self.weights.get(kind, 0)
