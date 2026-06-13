# Graph-Id — Program guide (human language)

This document explains **what Graph-Id is**, **how you use it day to day**, and **how the pieces fit together**—without assuming you already know the codebase.

Graph-Id is a **local-first desktop utility for developers**. It helps you answer one question when you return to a project:

> *Where did I leave off, what was blocking me, and what should I do next?*

It is **not** a task manager, not a note-taking app, not a cloud workspace, and **not an AI assistant**. Everything it shows you is built from **your own files and notes**, in a fixed priority order you can trust.

---

## Table of contents

1. [Who this is for](#who-this-is-for)
2. [The idea in one minute](#the-idea-in-one-minute)
3. [How you typically use it](#how-you-typically-use-it)
4. [Core concepts](#core-concepts)
5. [Where your data lives](#where-your-data-lives)
6. [The desktop app](#the-desktop-app)
7. [How summaries are built](#how-summaries-are-built)
8. [Scanning and context refresh](#scanning-and-context-refresh)
9. [Sessions and exit notes](#sessions-and-exit-notes)
10. [Command line (optional)](#command-line-optional)
11. [Settings](#settings)
12. [Backup, export, and maintenance](#backup-export-and-maintenance)
13. [How the program is built (architecture)](#how-the-program-is-built-architecture)
14. [Development and release](#development-and-release)
15. [What Graph-Id deliberately does not do](#what-graph-id-deliberately-does-not-do)
16. [Troubleshooting](#troubleshooting)
17. [Further reading](#further-reading)

---

## Who this is for

Graph-Id is for people who:

- Work on **several local code projects** and lose thread after days or weeks away
- Already leave traces in **git**, **HANDOFF.md**, **TODO/FIXME** comments, or quick exit notes
- Want a **small utility** they open on demand—not another tab that stays open all day
- Care about **privacy**: data stays on your machine, no account required

---

## The idea in one minute

1. You **register project folders** (paths on disk).
2. When you work, Graph-Id can track a **work session** (start → work → end with optional notes).
3. On demand, it **scans** allowed files (bounded, not the whole internet) and reads **git state**.
4. It assembles a **resume summary**: headline, sections, timeline, and **source tags** (e.g. “from exit note”, “from HANDOFF.md”).
5. You **open the project** in Cursor or VS Code; on success the app can **close**—you continue in your editor.

No background daemon watches your files. No cloud sync. No generated “plans” from an LLM.

---

## How you typically use it

### Short path (desktop)

```
Open Graph-Id → pick a project → read Resume panel → Open project → work in editor → (Graph-Id sleeps in tray) → show/quit when needed
```

When you finish a block of work:

```
End session → optional Exit Note (what you did, what’s next, blocker) → next time, summary reflects that
```

### When you’ve been away a long time

If you haven’t opened a project in a while, you may see a **“Before you continue”** (wake) panel: a short reminder of how long you’ve been away and the most important context. Dismiss it and use the full Resume panel as usual.

### Refresh context

Use **Refresh context** when files on disk changed (new HANDOFF, edited README, new TODOs). This runs a **bounded scan** and updates stored snapshots and the summary. It only runs when **you** click—it never runs silently in the background.

---

## Core concepts

### Project

A **registered folder** on your computer: name, path, category, status (`active` / `archived` / etc.), optional pinned **notes**. Graph-Id does not move or copy your repo; it only remembers the path.

### Work session

A **time box** of work on one project:

- **Started** when you open the project (or explicitly via CLI / IPC)
- **Ended** when you close the session, optionally with an **Exit Note**

Only **one active session per project** at a time. This avoids conflicting “where was I?” state.

Session **status** in the database: `active`, `completed`, or `abandoned` (depending on how the session was closed).

> **Note:** The database also has a legacy `projects.is_active` flag used internally when a session starts. In the UI, prefer **`has_open_session`** (derived from sessions) to mean “there is an unfinished session.”

### Scan snapshot

A **point-in-time record** of what the scanner found: how many files were read, task markers (TODO, FIXME, …), warnings, duration. Git branch/dirty state can be stored with the snapshot. Old snapshots are **trimmed automatically** (by count and age) so the database does not grow forever.

### Resume summary

Human-readable text shown in the dashboard and Resume panel. Built by the **SummaryEngine** from:

1. Session exit note / next step / blocker (highest trust)
2. Workflow files (HANDOFF, NEXT, SESSION notes, etc.)
3. Scan markers and git state (supporting context)

Summaries can be stored in the database (`short` mode by default; `detailed` available via CLI).

### Grafi

A **static helper** in the UI (short text, no chat). It reminds you that summaries are local and source-based—not a conversational agent.

---

## Where your data lives

Everything personal stays under your **data directory**:

| Default (Windows) | Contents |
|-------------------|----------|
| `%LOCALAPPDATA%\Graf-Id\` | All user data |

| File / folder | Purpose |
|---------------|---------|
| `config.json` | Preferences (default editor, compact layout, optional usage journal, debug timings, source weights) |
| `graf-id.db` | SQLite: projects, sessions, scans, summaries |
| `logs\` | Application logs |

Override the location with environment variable **`GRAFID_DATA_DIR`** (useful for portable installs or tests).

The **install folder** (Tauri app + bundled Python) does **not** hold your projects or database.

---

## The desktop app

Built with **Tauri** (Rust shell) + **React** (UI). The UI never opens SQLite directly; it asks the **Python backend** via IPC.

### Main areas

| Area | What you do there |
|------|-------------------|
| **Dashboard** | See all projects, search/filter, select one |
| **Project detail** | Path, git badge, actions, Resume panel |
| **Resume panel** | Context, timeline, blockers, next step, refresh, Grafi helper |
| **History** | Table of past scan snapshots (read-only) |
| **Settings** | Default opener, compact mode, usage journal, debug timing, open data/logs folders |

### Important actions

| Button | What happens |
|--------|----------------|
| **Add project** | Register a folder (dialog) |
| **Open project** | Start/resume session, launch Cursor or VS Code; after a successful editor launch the app hides to the system tray (sleep mode) |
| **Open folder** | Opens project root in File Explorer only (no session side effects from Rust) |
| **Refresh context** | Scan + git + regenerate summary; shows scan health hints if something was skipped |
| **End session** | Dialog for exit note, blocker, next step; ends session and refreshes summary |
| **Remove project** | Removes registry entry (does not delete files on disk) |

### Compact mode

In **Settings**, enable **Compact layout** for tighter spacing on the dashboard and panels. Stored in `config.json` under `extra.compact_mode`.

---

## How summaries are built

Graph-Id uses a **deterministic priority list**. The first strong sources win; weaker sources fill gaps.

Typical order:

1. **Exit note** and session fields (next step, blocker)
2. **High-trust workflow files** (e.g. HANDOFF.md, NEXT.md, session notes)
3. **Medium-trust files** (TODO lists, README, changelog)—only if needed
4. **Scan markers** (TODO/FIXME/BUG in code)
5. **Git** (dirty/clean, branch, modified files)

The **SummaryEngine** produces:

- **Headline** (may include “Away for N days” if you’ve been absent)
- **Body** and **MVP sections** (structured blocks in the Resume panel)
- **Timeline** (last few sessions with date and exit note preview)
- **Attributed lines** (text with a source tag for transparency)
- **Confidence** (`high` / `medium` / `weak`)—weak context shows an honest “not enough context” hint

There is **no** “here’s what you should do today” invented by a model. **Suggested next step** only appears if it came from your note or a workflow file.

---

## Scanning and context refresh

### What gets scanned

- Walks the project tree with **depth and file size limits**
- Skips heavy folders by default (`node_modules`, `.git`, `dist`, `.venv`, …)
- Honors **`.grafidignore`** in the project root (one directory name per line, like a mini ignore list)
- Parses task markers in text files it is allowed to read

### Scan health

After refresh, you may see messages such as:

- Number of warnings or skipped files
- Scan failure (refresh still tries to update what it can)
- Old snapshots pruned by retention policy

### Git-only refresh

The backend supports **`--git-only`** refresh (update git snapshot without a full filesystem walk). Useful for large repos when you only need branch/dirty state. The desktop UI may expose this in a future button; the IPC/CLI already supports it.

### Retention

By default, Graph-Id keeps about **30 snapshots per project** and drops snapshots older than **90 days**. Pruning runs after a successful refresh—not as a background job.

---

## Sessions and exit notes

### Starting a session

Happens automatically when you **Open project**, or manually:

```bash
graf-id session start <project>
# or IPC: graf-id ipc start-session <id>
```

Optional **checkpoint** label (bookmark name) on start via IPC `--checkpoint`.

### Ending a session

**End session** in the UI or:

```bash
graf-id session close <project> --exit-note "..." --next-step "..." --blocker "..."
```

Exit notes are stored on the session and in **exit note history** for a light journal over time.

### Timeline

The Resume panel shows **recent sessions**: when they started/ended, duration if known, and the first line of the exit note.

---

## Command line (optional)

Install from the repo (`pip install -e ".[dev]"`), then use `graf-id`:

| Command | Purpose |
|---------|---------|
| `graf-id startup` | Init config/DB, print startup summary |
| `graf-id add` / `list` / `remove` | Manage registered projects |
| `graf-id scan` | Scan one project and persist snapshot |
| `graf-id session start` / `end` / `status` / `close` | Session lifecycle |
| `graf-id resume` | Generate/show resume text |
| `graf-id history` | List scan history |
| `graf-id export` / `import` | Backup/restore zip bundle |
| `graf-id maintenance vacuum` | Compact SQLite database |
| `graf-id maintenance prune-snapshots` | Apply retention to all projects |
| `graf-id ipc …` | JSON API used by the desktop (one JSON object per stdout line) |

IPC examples:

```bash
graf-id ipc health
graf-id ipc bootstrap
graf-id ipc dashboard
graf-id ipc project-detail 1
graf-id ipc refresh-resume 1
graf-id ipc close-session 1 --exit-note "Done for today"
```

---

## Settings

| Setting | Meaning |
|---------|---------|
| **Open projects with** | System default, Cursor, VS Code, or Explorer-only |
| **Usage journal** | Local-only log of your actions (no telemetry); see `docs/USAGE_OBSERVATION.md` |
| **Debug timing** | Include timing hints in IPC responses for diagnosis |
| **Compact layout** | Denser UI |

Optional in `config.json`:

```json
{
  "source_weights": {
    "handoff": 90,
    "readme": 30
  }
}
```

Higher numbers mean higher priority when ranking workflow sources (advanced tuning).

---

## Backup, export, and maintenance

### Export zip

```bash
graf-id export C:\Backups\graf-id-backup.zip
```

Contains:

- `graf-id.db`
- `config.json` (if present)
- `grafid-export.json` (manifest: schema version, export time)
- `README.md` (short human instructions)

### Import

```bash
graf-id import C:\Backups\graf-id-backup.zip --replace
```

`--replace` overwrites an existing database in the data directory. Use on a **new machine** or after backing up.

See also: [grafid-export-spec.md](grafid-export-spec.md) for interchange with other Grafi-family tools.

### Maintenance

```bash
graf-id maintenance vacuum      # reclaim SQLite space
graf-id maintenance prune-snapshots
```

---

## How the program is built (architecture)

Think of three layers:

```
┌─────────────────────────────────────────┐
│  Desktop UI (React)                     │
│  dashboard, resume, settings, dialogs   │
└─────────────────┬───────────────────────┘
                  │ Tauri invoke (Rust)
┌─────────────────▼───────────────────────┐
│  Rust shell                             │
│  spawn Python, open Explorer, close app │
└─────────────────┬───────────────────────┘
                  │ subprocess: python -m grafid.ipc <subcommand> …
┌─────────────────▼───────────────────────┐
│  Python package (grafid/)               │
│  services, scanner, resume, SQLite      │
└─────────────────────────────────────────┘
```

### Main Python areas

| Folder | Role |
|--------|------|
| `grafid/cli/` | Terminal commands and `ipc` entry |
| `grafid/ipc/` | JSON handlers for the desktop |
| `grafid/db/` | Schema, migrations, repositories |
| `grafid/scanner/` | Bounded filesystem walk, ignore rules |
| `grafid/resume/` | SummaryEngine, human context, workflow artifacts |
| `grafid/services/` | Sessions, snapshots, refresh, export, launch |
| `grafid/git/` | Read-only git metadata |

### Schema version

The database schema is versioned (currently **v10**). Upgrades run automatically on startup via legacy migrators plus `grafid/db/migrations/`.

### Runtime modes

| Mode | When | Python used |
|------|------|-------------|
| **development** | `tauri dev`, local hacking | Repo `.venv` |
| **packaged** | Installed `.exe` | Bundled `desktop/src-tauri/runtime/python.exe` |

After changing Python code, rebuild the bundled runtime before release:

```powershell
packaging\build_runtime.ps1
packaging\verify_packaged_runtime.ps1
```

### IPC contract

Every IPC call returns one JSON object:

```json
{ "ok": true, "data": { ... } }
```

or

```json
{ "ok": false, "error": { "code": "...", "message": "..." } }
```

Heavy actions start a **new Python process** (cold-start cost is mostly interpreter + imports). Normal navigation is designed to avoid spawns by using a one-time bootstrap preload + in-memory cache.

---

## Development and release

### Prerequisites

- Python 3.12+
- Node.js + npm (desktop)
- Rust (Tauri)
- Git on PATH (for git features)

### Quick start

```powershell
cd c:\Projektek\Grap-Id
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

cd desktop
npm install
npm run tauri:dev
```

### Tests

```powershell
# Python (repo root)
.venv\Scripts\pytest

# Desktop unit tests
cd desktop
npm test
```

### Release build

See [packaging/README.md](../packaging/README.md) and [PACKAGED_USAGE.md](PACKAGED_USAGE.md).

---

## What Graph-Id deliberately does not do

To protect its identity as a **lightweight, trustworthy** tool, these are out of scope:

- Cloud sync, accounts, or team workspaces
- Always-on tray icon or file watcher daemon
- AI / LLM summaries or autonomous coding agents
- Full IDE replacement, built-in terminal, or Jira-style task boards
- Automatic scheduled scans without your action
- Mobile app (desktop-first)

If a feature needs **continuous background work**, it probably does not belong in Graph-Id.

---

## Troubleshooting

| Problem | Things to check |
|---------|-----------------|
| Desktop says backend unavailable | Python on PATH or `GRAFID_PYTHON`; `.venv` installed; try `graf-id ipc health` |
| Open project does not launch editor | Cursor/`code` on PATH; Settings → default opener; fallback opens Explorer |
| Summary feels empty | End a session with an exit note; add HANDOFF.md; click Refresh context |
| Scan seems slow | Large repo: use git-only refresh from CLI; add `.grafidignore` for huge folders |
| Packaged app missing new features | Run `packaging\build_runtime.ps1` and rebuild the installer |
| Git always “unknown” | Install git; ensure project folder is a git repo |
| Database errors | `graf-id db check`; restore from `graf-id export` backup |

Logs: `%LOCALAPPDATA%\Graf-Id\logs\` (or your `GRAFID_DATA_DIR`).

---

## Further reading

| Document | Topic |
|----------|--------|
| [README.md](../README.md) | Repo overview and milestone history |
| [desktop/README.md](../desktop/README.md) | Desktop dev workflow and IPC list |
| [packaging/README.md](../packaging/README.md) | Windows packaging and embedded Python |
| [PACKAGED_USAGE.md](PACKAGED_USAGE.md) | End-user packaged install |
| [LAUNCH_BOUNDARIES.md](LAUNCH_BOUNDARIES.md) | Open Folder vs Open Project |
| [grafid-export-spec.md](grafid-export-spec.md) | Export bundle format |
| [USAGE_OBSERVATION.md](USAGE_OBSERVATION.md) | Local usage journal |
| [MVP_RELEASE.md](MVP_RELEASE.md) | MVP release checklist |

---

*Graph-Id / Graf-Id — local workflow continuity. Your machine, your data, your sources.*
