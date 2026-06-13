# Release build verification (Windows)

English-only. Records the automated checks for packaged Graf-Id.

## Build

```powershell
packaging\build_release.ps1
```

Requires: Node.js, npm, Rust (cargo), and a local `.venv` used only to **build** the embedded runtime (not required to **run** the release app).

## Automated smoke

```powershell
packaging\verify_packaged_runtime.ps1   # IPC via runtime/ only
packaging\verify_release_bundle.ps1     # release layout + UI launch
```

`verify_release_bundle.ps1` checks:

- `target/release/graf-id-desktop.exe` exists
- `target/release/runtime/python.exe` works in `packaged` mode
- `health`, `runtime-check`, `bootstrap`, `dashboard` IPC
- `dismiss-startup` when a card is present
- Isolated `GRAFID_DATA_DIR` (config + SQLite created)
- Release `.exe` launch creates a database without repo `.venv`

## Output paths

| Artifact | Path |
|----------|------|
| Release binary | `desktop\src-tauri\target\release\graf-id-desktop.exe` |
| MSI | `desktop\src-tauri\target\release\bundle\msi\Graf-Id_0.1.0_x64_en-US.msi` |
| NSIS setup | `desktop\src-tauri\target\release\bundle\nsis\Graf-Id_0.1.0_x64-setup.exe` |

## Runtime paths (packaged)

| Item | Default location |
|------|------------------|
| Embedded Python | Next to app: `runtime\python.exe` (also under `resources\` when installed) |
| Config | `%LOCALAPPDATA%\Graf-Id\config.json` |
| Database | `%LOCALAPPDATA%\Graf-Id\graf-id.db` |
| App log | `%LOCALAPPDATA%\Graf-Id\logs\graf-id.log` |
| Desktop backend log | `%LOCALAPPDATA%\Graf-Id\logs\desktop-backend.log` |

Override with `GRAFID_DATA_DIR` for portable or test profiles.

## Manual checks (recommended)

1. Install NSIS or MSI on a machine without the repo checkout.
2. Confirm dashboard loads with an existing project database.
3. Dismiss startup card in the UI.
4. **Open folder** on a registered project path.
5. Confirm no Python install is required on PATH.

Open folder is not automated in the script (OS shell action).
