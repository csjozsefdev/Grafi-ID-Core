# Graph-Id core status

**Status: complete beyond MVP** — suitable for archive or maintenance mode with documented future ideas.

Version: **0.1.0** (see `pyproject.toml`)

---

## Completed features

### Desktop (Tauri + React)

- [x] Sidebar project list with search, category tabs, status filter
- [x] Compact resume preview per project row
- [x] Selected project view with Resume panel
- [x] **More details** collapsible technical metadata (UX-3)
- [x] Refresh context (bounded scan + summary rebuild)
- [x] Add / edit / remove project in UI
- [x] Open project (IDE launch + session)
- [x] Open folder (Explorer)
- [x] End session with exit note modal
- [x] History tab (scan snapshots)
- [x] Settings (app settings via IPC)
- [x] Startup / wake card flow
- [x] Bootstrap cache for fast navigation
- [x] Dark theme, Grafi green accents

### Python core

- [x] Project registry + SQLite persistence (schema v7)
- [x] Bounded filesystem scanner + marker quality filters
- [x] Read-only git snapshots
- [x] Work sessions (start / end / active)
- [x] Deterministic summary engine with source priority
- [x] Workflow artifact allowlist (HANDOFF, README, NOTES, …)
- [x] Human context composition (docs beat git fallback)
- [x] CLI (`graf-id`) full command set
- [x] JSON IPC for desktop
- [x] GrafiTalk inbox export (`export-grafitalk`)
- [x] Zip export/import for backup
- [x] Usage journal (opt-in)
- [x] Packaged embedded Python runtime

### Packaging

- [x] `build_runtime.ps1` with venv/base-Python resolution fix
- [x] MSI + NSIS installers via `tauri build`
- [x] Release verification scripts
- [x] Documentation for disk cleanup (`CLEANUP.md`)

### Tests

- [x] Python pytest suite (130+ tests)
- [x] Desktop vitest utilities

---

## Known limitations

| Area | Limitation |
|------|------------|
| Platform | Windows-first for packaged desktop |
| Git | Requires `git` on PATH |
| Refresh | Manual only — no file watcher |
| Installers | Unsigned; possible AV warnings |
| Disk | `src-tauri/target/` can grow to several GB during dev |
| i18n | English UI only |
| Cloud | None by design |
| AI | Not in core summary path |
| Auto-update | None |
| Onboarding | Assumes developer comfort with local folders |

---

## Future ideas (not committed)

These are **planned directions**, not MVP scope:

- **Better history readability** — richer timeline, diff hints between scans
- **Project tags / favorites** — pin frequent projects in sidebar
- **Spec cards** — structured cards for milestones or acceptance criteria
- **Ecosystem integrations** — deeper GrafiTalk, export consumers, Grap-h
- **Cache cleanup brush action** — one-click “clean Rust target” from UI or docs link
- **Settings polish** — more in-app config, less `config.json` editing
- **macOS / Linux** — Tauri cross-platform potential, not validated for release

---

## Archive statement

Graph-Id MVP goals are met:

- Local project continuity tool for developers
- Deterministic resume from human sources
- Desktop app with packaging
- Documented architecture, workflow, QA, and handover

Further work should be **explicit new milestones**, not implicit scope creep.

---

## Related docs

- [HANDOVER.md](HANDOVER.md) — resume work after months away
- [QA_CHECKLIST.md](QA_CHECKLIST.md) — verification
- [MVP_RELEASE.md](MVP_RELEASE.md) — original release notes (some items superseded by UI work)
