# Graf-Id Desktop (Tauri shell)

Desktop UI for the Graf-Id Python core. The UI does not access SQLite directly.

## Architecture

```
React UI  --invoke-->  Tauri (Rust)  --subprocess-->  Python `graf-id ipc`
                                                      Services + SQLite
```

- **Frontend** (`desktop/src/`): dashboard, startup card, history, settings placeholder.
- **IPC client** (`desktop/src/ipc/`): typed wrappers for Tauri commands.
- **Rust bridge** (`desktop/src-tauri/src/python.rs`): spawns bundled or dev Python, reads JSON from stdout.
- **Python IPC** (`grafid/ipc/`): reuses existing services (no duplicated business logic).

## Prerequisites (development only)

1. **Python 3.12+** — repo `.venv` with `pip install -e ".[dev]"` from repo root.
2. **Node.js** + **npm**
3. **Rust** — [rustup](https://rustup.rs/) for `tauri dev` / `tauri build`

End users of the **packaged app** do not install Python, Node, or Rust.

## Development workflow

```powershell
cd c:\Projektek\Grap-Id
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

cd desktop
npm install
npm run tauri:dev
```

Use **`npm run tauri:dev`** only (not `npm run dev` alone). If port 1420 is in use, stop any standalone Vite process first.

Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `GRAFID_PYTHON` | Override `python.exe` (dev) |
| `GRAFID_REPO_ROOT` | Repo root when cwd is not `desktop/` |
| `GRAFID_RUNTIME_MODE` | `development` or `packaged` |
| `GRAFID_DATA_DIR` | Writable config/DB/logs directory |
| `GRAFID_RESOURCE_ROOT` | Directory on `PYTHONPATH` containing `grafid/` |

## Packaged / release build

From repo root:

```powershell
packaging\build_release.ps1
```

This builds the embedded runtime, runs IPC smoke tests, produces:

| Artifact | Path |
|----------|------|
| Release binary | `desktop\src-tauri\target\release\graf-id-desktop.exe` |
| MSI installer | `desktop\src-tauri\target\release\bundle\msi\Graf-Id_0.1.0_x64_en-US.msi` |
| NSIS installer | `desktop\src-tauri\target\release\bundle\nsis\Graf-Id_0.1.0_x64-setup.exe` |

Verify without repo `.venv`:

```powershell
packaging\verify_release_bundle.ps1
```

**User data (packaged):** `%LOCALAPPDATA%\Graf-Id` — `config.json`, `graf-id.db`, `logs\` (override with `GRAFID_DATA_DIR`).

See [docs/PACKAGED_USAGE.md](../docs/PACKAGED_USAGE.md) and [packaging/README.md](../packaging/README.md).

## Desktop features (current)

- **Dashboard** — project list with search, category tabs, status filter, resume excerpt.
- **Add / edit project** — register folders and update name, path, category, status, notes.
- **Resume panel** — structured MVP sections, refresh context (scan + summary), technical details collapse.
- **End session** — Exit Note modal (what you did, unfinished, next step, blocker).
- **Actions** — open project (session + editor), **open folder** (Explorer), open terminal, remove project.
- **History** — read-only scan snapshot table.
- **Settings** — default opener, usage journal, debug timing flags.

**Dev vs packaged Python:** `tauri dev` uses the repo `.venv` (latest `grafid` source). Release builds use `desktop/src-tauri/runtime/` — rebuild with `packaging\build_runtime.ps1` after backend changes.

## Python IPC commands (manual test)

```powershell
graf-id ipc health
graf-id ipc runtime-check
graf-id ipc bootstrap
graf-id ipc dashboard
graf-id ipc project-detail 1
graf-id ipc open-project 1
graf-id ipc open-folder 1
graf-id ipc dismiss-startup 0 --summary-id 3
graf-id ipc add-project my-app C:\dev\my-app --category "Client Work"
graf-id ipc update-project 1 --status paused --notes "On hold"
graf-id ipc refresh-resume 1
graf-id ipc close-session 1 --exit-note "Shipped feature" --next-step "Tests"
```

Each command prints one JSON object on stdout.

## Workflow launch (Open project / Open folder)

| Action | Behavior |
|--------|----------|
| **Open folder** | Opens the registered project path in File Explorer (validates path first). |
| **Open project** | Updates `last_opened_at`, starts or resumes a work session, then opens **Cursor** or **VS Code** if configured. Falls back to Explorer with a clear message if the editor is missing. |

Configure editor per project: `graf-id add my-app C:\dev\my-app --ide cursor` (or `vscode`).  
Global default in `config.json`: `"preferred_ide": "cursor"` (or `vscode`, `explorer`).

## Tests

```powershell
# Python (repo root)
.venv\Scripts\pytest grafid\tests -q

# Desktop utilities
cd desktop
npm test
```

## Known limitations

- **Python subprocesses are still used**, but normal navigation is designed to avoid them:
  - App startup runs `ipc_bootstrap` once and caches `app_settings` + per-project `resume_panel` and `history` in memory.
  - Settings open and project select read from cache (no Python spawn).
  - Heavy actions (Open Project, Refresh Context, End session, etc.) still spawn Python on demand.
- **Git** — requires `git` on PATH for git snapshot collection.
- **No Grafi animations, watchers, cloud, or AI.**
