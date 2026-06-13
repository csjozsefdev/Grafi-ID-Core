# Graph-Id user workflow

Step-by-step journey through the product — and why each step exists.

---

## Overview

```
Open Graph-Id
    ↓
Select Project
    ↓
Read Resume / Refresh Context (scan sources)
    ↓
Generate Summary (deterministic compose)
    ↓
Open IDE
    ↓
Work
    ↓
Exit Note (end session)
    ↓
Next Resume (next time you return)
```

---

## 1. Open Graph-Id

**What you do:** Launch the desktop app (or run `graf-id startup` in terminal).

**Why it exists:** Graph-Id is an **on-demand wake-up tool**, not a background service. You open it when you need continuity context, then return to your editor.

**What happens technically:** Tauri starts → `ipc_bootstrap` loads projects, settings, and cached resume panels into memory.

---

## 2. Select project

**What you do:** Click a project in the sidebar (search/filter by category or status if needed).

**Why it exists:** Continuity is **per project**. Each registered folder has its own sessions, scans, and summary.

**What you see:** Project name, compact preview line, session/git chips, full Resume panel in the main area.

---

## 3. Scan sources (Refresh context)

**What you do:** Click **Refresh context** in the Resume panel when files on disk may have changed.

**Why it exists:** Graph-Id does **not** watch your filesystem continuously. Explicit refresh keeps behavior predictable and bounded — you control when I/O runs.

**What is scanned:**

- Allowlisted workflow files (HANDOFF.md, README.md, NOTES.md, …)
- Code markers (TODO/FIXME) with quality filters
- Git branch, dirty/clean, modified files (if `git` available)

**What is not scanned:** Your entire drive, `node_modules`, or arbitrary paths outside project rules.

---

## 4. Generate summary

**What you do:** Automatic after refresh (or on bootstrap from last known state).

**Why it exists:** Raw scan data is too noisy. The **SummaryEngine** composes a short human-readable resume with tagged sources.

**Priority:** Your exit notes and handoff docs beat generic “recent edits in file X” git text.

**What you see:**

- Where you left off
- Suggested next step
- Session status
- MVP sections (expandable detail)
- Source tags

---

## 5. Open IDE

**What you do:** Click **Open project** (or **Open folder** for Explorer only).

**Why it exists:** Graph-Id is the **bridge**, not the workspace. The goal is to land you in Cursor/VS Code with context already read.

**What happens:**

- `last_opened_at` updated
- Work session started or resumed
- Preferred IDE launched (configurable per project or globally)

---

## 6. Work

**What you do:** Normal development in your editor. Graph-Id can stay open or go to the system tray.

**Why sessions matter:** An **active session** signals “work in progress” in the resume. Without an exit note, the summary may be weaker — that is intentional encouragement to close the loop.

---

## 7. Exit note

**What you do:** Click **End session** → fill optional fields:

- What you did (exit note)
- Unfinished items
- Blocker
- Next step

**Why it exists:** This is the **strongest continuity signal**. It captures intent in your words, not inferred from git noise.

**Skip:** You can end without notes, but future resumes may rely on weaker sources (docs, markers, git).

---

## 8. Next resume

**What you do:** Days or weeks later — open Graph-Id, select the same project, read Resume.

**Why it works:** SQLite persisted your session, scans, and notes. Refresh context if the repo changed since last time.

**Wake panel:** If you have been away a long time, you may see a short “before you continue” reminder — dismiss and use the full Resume panel.

---

## CLI equivalent

| Desktop | CLI |
|---------|-----|
| Add project | `graf-id add <name> <path>` |
| Refresh context | `graf-id scan <name>` + `graf-id resume <name>` |
| Start session | `graf-id session start <name>` |
| End session + exit note | `graf-id session close <name> --done "..." --next "..."` |
| Export for GrafiTalk | `graf-id export-grafitalk` |

---

## Related docs

- [GUIDE.md](GUIDE.md) — fuller narrative
- [ARCHITECTURE.md](ARCHITECTURE.md) — technical pipeline
- [QA_CHECKLIST.md](QA_CHECKLIST.md) — manual verification steps
