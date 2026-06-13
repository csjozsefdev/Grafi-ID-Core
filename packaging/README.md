# Graf-Id Windows packaging (Milestone 10)

English-only notes for preparing a **local-first** desktop `.exe` without requiring users to install Python or use a terminal.

## Recommended strategy: Tauri + embedded Python sidecar

| Approach | Summary |
|----------|---------|
| **Embedded Python runtime** | Ship a private `python.exe` + stdlib + `grafid` package under the install folder (e.g. `runtime/python/`). Tauri spawns it for IPC. |
| **Tauri sidecar** | Same interpreter, registered as a Tauri sidecar binary so the shell resolves it next to the app executable. |

**Recommendation:** Use **one embedded CPython build** (Windows embeddable package or venv freeze) as a **sidecar**. The Tauri app remains the UI shell; Python stays the business-logic backend via `python -m grafid.ipc <subcommand> …`.

### Tradeoffs

| | Embedded / sidecar Python | PyInstaller one-file backend |
|--|---------------------------|------------------------------|
| **Pros** | Reuses existing IPC module tree; fast iteration; clear logs; small Rust shell | Single artifact |
| **Cons** | Larger install folder (~40–80 MB); must bundle deps | Harder debugging; slower cold start; Typer/subprocess quirks |
| **Fit for Graf-Id** | **Best match** (already IPC-based) | Possible later, not MVP |

**Not in scope:** MSI with admin, auto-update, telemetry, background services.

## Release directory layout (target)

```
Graf-Id.exe                 # Tauri frontend
runtime/
  python.exe                # Embedded interpreter
  Lib/                      # grafid + dependencies
  python311._pth            # Path file (embeddable layout)
```

User data **never** lives inside `runtime/`:

```
%LOCALAPPDATA%\Graf-Id\     # or GRAFID_DATA_DIR (portable mode)
  config.json
  grafid.db
  logs/
```

## Environment contract (set by Tauri when spawning IPC)

| Variable | Purpose |
|----------|---------|
| `GRAFID_RUNTIME_MODE` | `development` or `packaged` |
| `GRAFID_DATA_DIR` | Config, SQLite DB, logs (writable) |
| `GRAFID_RESOURCE_ROOT` | Directory on `PYTHONPATH` containing `grafid/` |
| `GRAFID_PYTHON` | Path to embedded `python.exe` |

Development continues to use `.venv` and optional `GRAFID_REPO_ROOT` / `GRAFID_PYTHON` overrides.

## Validation commands

```powershell
# From repo with venv active
graf-id ipc health
graf-id ipc runtime-check
graf-id ipc runtime-check --full
```

`runtime-check` validates directories, config JSON, and database integrity without duplicating business rules in Rust.

## Build checklist

1. `packaging\create_icons.ps1` then `cd desktop && npx tauri icon src-tauri/icons/128x128.png` (generates `icon.ico` for MSI/NSIS)
2. `packaging\build_runtime.ps1` → `desktop\src-tauri\runtime\`
3. `packaging\verify_packaged_runtime.ps1` — IPC smoke without UI
4. `packaging\build_release.ps1` — full build + `verify_release_bundle.ps1`
5. Artifacts: `target\release\graf-id-desktop.exe`, `target\release\bundle\msi\`, `target\release\bundle\nsis\`

See [docs/PACKAGED_USAGE.md](../docs/PACKAGED_USAGE.md).

## Known limitations

- Runtime is **built locally** from your `.venv` base Python (not committed to git).
- Portable mode (`GRAFID_DATA_DIR` next to exe) is supported via env but not default UI.
- Git integration still depends on user having `git` on PATH when opening terminals.

## Python modules

- `grafid/packaging/runtime.py` — mode detection, layout paths
- `grafid/packaging/validation.py` — startup validation report
- `grafid/packaging/bootstrap.py` — IPC-facing helpers

See root `README.md` for developer setup.
