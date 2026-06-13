# Stability checkpoint (pre–Reality Audit)

English-only. Lightweight cleanup pass — no feature changes.

## Validation (this checkpoint)

| Check | Result |
|-------|--------|
| `pytest` | 132 passed, 5 skipped |
| `ipc health` | OK (schema 7) |
| `ipc runtime-check` | OK |
| `packaging/verify_packaged_runtime.ps1` | OK (embedded runtime present) |
| `cargo check` (Tauri) | OK |
| `npm run tauri --version` | tauri-cli 2.11.2 |
| Port 1420 | Free at checkpoint time |

## Architecture snapshot

**Backend:** `grafid/` — CLI (Typer), services, SQLite repos, scanner, git (read-only), resume engine, IPC handlers, `observability/` (local journal).

**Desktop:** `desktop/` — React UI → Tauri (`src-tauri/`) → subprocess Python IPC → same services.

**IPC:** JSON line on stdout; commands include `health`, `bootstrap`, `runtime-check`, dashboard/startup handlers.

**Data:** User DB at `%LOCALAPPDATA%\Graf-Id\` (dev); packaged runtime under `desktop/src-tauri/runtime/` (build artifact, gitignored).

## Technical debt (carry forward)

- IPC uses Python subprocesses (on-demand); common UI reads are served from bootstrap cache to avoid spawns
- In-app project registration still CLI-only
- `desktop/src-tauri/target/` large (kept for faster rebuilds)
- Multiple `node` processes common during IDE + prior dev sessions
- Unsigned portable build / AV false positives possible
- Settings UI placeholder

## Cleaned (safe only)

- `.pytest_cache`, `grafid/**/__pycache__`, `grafid.egg-info`, `desktop/dist`

## Preserved

- Source, tests, `.venv`, `config.json`, user SQLite, `%LOCALAPPDATA%\Graf-Id` logs/DB, `desktop/src-tauri/runtime/`, `node_modules`, `target/`

## Reality Audit readiness

**Yes** — stable for a structured Reality Audit (manual desktop pass + packaged smoke already green).
