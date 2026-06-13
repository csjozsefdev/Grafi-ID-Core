"""Passive runtime state after startup (no background monitoring)."""

from __future__ import annotations

from grafid.models.grafi import PassiveRuntimeInfo

_manager: "PassiveRuntimeManager | None" = None


class PassiveRuntimeManager:
    """
    In-process flag set after startup summary completes.

    Graf-Id stays passive until the next explicit CLI command; there is no
    hidden watcher or AI worker.
    """

    def __init__(self) -> None:
        self._passive = False

    def activate_passive_mode(self) -> PassiveRuntimeInfo:
        self._passive = True
        return self.info()

    def info(self) -> PassiveRuntimeInfo:
        if self._passive:
            return PassiveRuntimeInfo(
                is_passive=True,
                monitoring_enabled=False,
                ai_enabled=False,
                message=(
                    "Passive mode: Graf-Id will not monitor files or run background "
                    "tasks until you invoke a CLI command."
                ),
            )
        return PassiveRuntimeInfo(
            is_passive=False,
            monitoring_enabled=False,
            ai_enabled=False,
            message="Active CLI invocation (no background monitoring).",
        )


def get_passive_runtime() -> PassiveRuntimeManager:
    global _manager
    if _manager is None:
        _manager = PassiveRuntimeManager()
    return _manager


def reset_passive_runtime_for_tests() -> None:
    """Clear singleton state between pytest cases."""
    global _manager
    _manager = PassiveRuntimeManager()
