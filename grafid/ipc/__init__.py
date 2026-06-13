"""JSON IPC layer for desktop shell (Tauri) integration."""

from grafid.ipc.envelope import IpcError, IpcResponse, emit_response
from grafid.ipc.handlers import (
    handle_bootstrap,
    handle_health,
    handle_list_projects,
    handle_runtime_check,
)

__all__ = [
    "IpcError",
    "IpcResponse",
    "emit_response",
    "handle_bootstrap",
    "handle_health",
    "handle_list_projects",
    "handle_runtime_check",
]
