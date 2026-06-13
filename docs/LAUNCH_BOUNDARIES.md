# Launch boundaries (Open Folder vs Open Project)

English-only. Stabilization reference — not a feature milestone.

## Open Folder — show the directory

| Property | Value |
|----------|--------|
| Purpose | Open the **registered project root** in File Explorer |
| Desktop path | `openProjectFolderPath(path)` → Tauri `open_project_folder` → Rust `explorer` |
| Python IPC | **Not used** by the desktop Open Folder button |
| DB / session | **None** |
| Path | Exact `projects.path` from registry (no subfolders, no guessing) |

## Open Project — resume the workflow

| Property | Value |
|----------|--------|
| Purpose | Update workflow state and launch editor or Explorer |
| Desktop path | `openProjectWorkflow(id)` → Python `ipc open-project` |
| State | `last_opened_at`, work session start/resume |
| Editor | `preferred_ide` on project or `config.json` |
| Explorer | **At most once** — Python defers (`launch_explorer=False`); UI calls Rust when `launch.open_explorer` is true |

## CLI

- `graf-id ipc open-folder` — Python opens Explorer (CLI only).
- `graf-id open` — Python may open Explorer in-process (`launch_explorer=True`).

## Regression tests

`grafid/tests/test_folder_open_regression.py`
