# Graf-Id MVP — release readiness (Milestone 11)

English-only product. Local-first desktop utility. **Not** an AI assistant, cloud sync, or live monitor.

## Architecture (summary)

```
React UI  →  Tauri (Rust)  →  Python IPC subprocess  →  Services  →  SQLite
```

- **User data:** `%LOCALAPPDATA%\Graf-Id` (or `GRAFID_DATA_DIR`) — `config.json`, `graf-id.db`, `logs/`
- **Packaged runtime:** `runtime/python.exe` next to the app binary (built by `packaging/build_runtime.ps1`, not committed to git)
- **Schema version:** 7

## Startup instructions

### End users (packaged app)

1. Install from `Graf-Id_0.1.0_x64-setup.exe` (NSIS) or `Graf-Id_0.1.0_x64_en-US.msi`, or run `graf-id-desktop.exe` from the release folder.
2. No separate Python install is required.
3. Register projects via CLI on first setup: `graf-id add <name> <path>` (or reuse an existing `%LOCALAPPDATA%\Graf-Id` database from dev).
4. Dismiss the “Where you left off” card when done; state stays in local SQLite.

### Developers

```powershell
cd c:\Projektek\Grap-Id
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
packaging\build_runtime.ps1
packaging\verify_packaged_runtime.ps1
cd desktop
npm install
npm run tauri:dev
```

### Release build + verification

```powershell
packaging\build_release.ps1
packaging\verify_release_bundle.ps1
```

Outputs:

- `desktop\src-tauri\target\release\graf-id-desktop.exe`
- `desktop\src-tauri\target\release\bundle\msi\Graf-Id_0.1.0_x64_en-US.msi`
- `desktop\src-tauri\target\release\bundle\nsis\Graf-Id_0.1.0_x64-setup.exe`

## Known limitations

| Area | Limitation |
|------|------------|
| Onboarding | No in-app project registration; CLI `graf-id add` required |
| Workflow | Scan and session start/close are CLI-only; desktop is read-mostly |
| Packaging | Embedded runtime is built locally (~large); not stored in git |
| Git | Requires `git` on PATH for git snapshot collection |
| Scans | Read-only snapshots; no live file watcher |
| Startup card | New summary row per app launch until dismissed |
| Settings UI | Placeholder; edit `config.json` manually |
| Updates | No auto-update; installers are unsigned |
| AI / cloud | Out of scope |

## Stability summary (M11)

- Fixed `is_empty` flag on startup summaries (correct empty-project UX).
- Removed redundant DB integrity pass on bootstrap (still verified during `StartupService`).
- IPC `resume-preview` avoids double runtime bootstrap per request.
- In-process runtime cache for multi-step handlers in one subprocess.
- Quieter logs when database already exists (DEBUG vs INFO).
- Config `log_level` validated on load.
- Desktop: clearer errors, loading spinner, dismiss feedback, retry on panels.

## Technical debt (practical)

| Item | Impact | Suggested later |
|------|--------|-----------------|
| IPC uses Python subprocesses | Cold-start latency when a subprocess is required | Keep on-demand subprocesses; avoid background daemon creep. Mitigate with bootstrap preload + in-memory cache for common UI reads. |
| `startup_summaries` grows each launch | Table size | Dedup or “one active card” policy |
| `retention_policy.py` unused | None today | Wire or remove in cleanup milestone |
| CLI `_exit_with_error` duplicated | Maintenance | Small shared helper module |
| Log rotation absent | Disk growth | Rotating file handler |
| Layering: IPC imports `cli.runtime` | Coupling | Move `prepare_runtime` to `services` |

## MVP readiness

| Gate | Status |
|------|--------|
| Core CLI + SQLite | **Ready** |
| Desktop dashboard + Grafi card | **Ready** |
| pytest suite | **Ready** (132+ tests) |
| Packaged runtime (IPC smoke) | **PASS** — `packaging\verify_packaged_runtime.ps1` |
| Release binary + installers | **PASS** — `packaging\build_release.ps1` (on build machine with Rust/Node) |
| Release smoke (no `.venv`) | **PASS** — `packaging\verify_release_bundle.ps1` |
| Code signing / store distribution | **Deferred** |

## Final release risks

1. **CLI-heavy first run** — Empty DB requires `graf-id add` unless onboarding UI is added.
2. **Corrupt `config.json`** — User must fix or delete file (app surfaces a clear message).
3. **Unsigned installers** — Antivirus may flag; code signing deferred.
4. **Large bundle size** — Embedded Python increases download size (~25–37 MB installers).
5. **Git optional** — Git features degrade if `git` is not on PATH.

## Lightweight philosophy checklist

- No background polling loops in Python or React.
- Passive runtime after startup summary (no watchers).
- IPC on demand only (no standing server in MVP).
- Minimal dependencies in `pyproject.toml`.
