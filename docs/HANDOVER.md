# Graph-Id handover

*Read this if you are opening the repo six months from now — or onboarding cold.*

**Time to read:** under 10 minutes.

---

## What this project is

**Graph-Id** is a **project continuity tool for developers**. It helps you remember where you left off on local code projects.

It is **not** a task manager, PM tool, AI coding assistant, or documentation platform.

When you return to a repo after a break, Graph-Id shows a **resume summary** built from:

- Your **exit notes** (best signal)
- **HANDOFF / README / NOTES** files in the project
- **Git status** and modified files (fallback only)
- **TODO/FIXME markers** from a bounded scan

Everything is **local** (`%LOCALAPPDATA%\Graf-Id`). No cloud. No background watcher. You click **Refresh context** when you want an update.

---

## How it works (60 seconds)

```
React desktop UI  →  Tauri (Rust)  →  Python IPC  →  SQLite + disk scan
```

1. Register project folders
2. Select a project → read Resume panel
3. Refresh context → scan + compose summary
4. Open project in Cursor/VS Code
5. End session with exit note when pausing
6. Next time: summary remembers

Full journey: [WORKFLOW.md](WORKFLOW.md)

---

## Where important files are

| What | Where |
|------|-------|
| Python core | `grafid/` |
| Desktop UI | `desktop/src/` |
| Tauri / Rust bridge | `desktop/src-tauri/` |
| Embedded Python (release) | `desktop/src-tauri/runtime/` (gitignored — rebuild) |
| Rust build cache (huge) | `desktop/src-tauri/target/` (gitignored — `cargo clean`) |
| Packaging scripts | `packaging/` |
| User database (runtime) | `%LOCALAPPDATA%\Graf-Id\graf-id.db` |
| User config | `%LOCALAPPDATA%\Graf-Id\config.json` |
| GrafiTalk export inbox | `grafitalk/` (JSON files, optional) |
| Tests | `grafid/tests/`, `desktop/src/**/*.test.ts` |

**Do not confuse with GrafiTalk** — separate product; integration is JSON export only.

---

## How to run it (dev)

```powershell
cd C:\Projektek\Grap-Id
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

cd desktop
npm install
npm run tauri:dev
```

Use **`tauri:dev`**, not `npm run dev` alone.

---

## How to build installers

```powershell
cd C:\Projektek\Grap-Id\desktop
npm run build:runtime
npm run tauri:build
```

If `build:runtime` fails about base Python: recreate `.venv` from system Python (not bundled runtime). See [CLEANUP.md](CLEANUP.md).

---

## How to test

```powershell
.venv\Scripts\pytest grafid\tests -q
cd desktop && npm test
```

Manual smoke: [QA_CHECKLIST.md](QA_CHECKLIST.md)

---

## Where NOT to touch things

| Avoid | Reason |
|-------|--------|
| `C:\Projektek\Grafitalk` (external repo) | Separate product |
| Coupling GrafiTalk to SQLite | Use `export-grafitalk` JSON only |
| Adding background file watchers | Against explicit-refresh philosophy |
| LLM inside `summary_composition.py` | Deterministic core decision |
| Committing `target/` or `runtime/` | Large generated artifacts — gitignored |
| Deleting `runtime/` before release build | Rebuild with `npm run build:runtime` |

Safe to delete: **`desktop/src-tauri/target/`** via `cargo clean` (~GB recovered). See [CLEANUP.md](CLEANUP.md).

---

## Key code paths (if you need to debug)

| Feature | Start here |
|---------|------------|
| Refresh context | `grafid/ipc/dashboard_handlers.py` → `handle_refresh_resume` |
| Summary priority | `grafid/resume/summary_composition.py` |
| Workflow files | `grafid/resume/workflow_artifacts.py` |
| Desktop refresh button | `desktop/src/components/AppShell.tsx` |
| Sidebar preview | `desktop/src/utils/continuity.ts` |
| IPC spawn | `desktop/src-tauri/src/python.rs` |
| Bootstrap cache | `grafid/ipc/handlers.py` → `handle_bootstrap` |

---

## What was planned but not built (future)

- History UI polish
- Project favorites / tags
- Spec cards
- In-app “clean build cache” action
- Deeper GrafiTalk automation (watch inbox)
- Non-Windows release validation

See [CORE_STATUS.md](CORE_STATUS.md).

---

## Project status

**MVP complete.** The product is documented for archive or light maintenance. New features should be scoped as explicit milestones.

---

## Documentation map

| Doc | Use when |
|-----|----------|
| [README.md](../README.md) | Overview + quick start |
| [GUIDE.md](GUIDE.md) | Long-form user guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [DECISIONS.md](DECISIONS.md) | Why we chose X |
| [GRAFITALK_INTEGRATION.md](GRAFITALK_INTEGRATION.md) | Export format |
| [QA_CHECKLIST.md](QA_CHECKLIST.md) | Before release |

---

## One-line summary

**Graph-Id is a local Windows desktop utility that scans your project folders on demand and shows a deterministic “where you left off” resume — then gets out of your way so you can code.**
