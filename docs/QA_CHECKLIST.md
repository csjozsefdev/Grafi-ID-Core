# Graph-Id manual QA checklist

Use before release or after significant changes. All steps are **manual** — no automated substitute for desktop smoke testing.

**Environment:** Windows, `npm run tauri:dev` from `desktop/`, or packaged `.exe`.

---

## Setup

- [ ] Repo `.venv` exists with `pip install -e ".[dev]"`
- [ ] `cd desktop && npm install`
- [ ] App launches without console errors

---

## Create project

- [ ] **Add project** dialog registers a valid folder
- [ ] Project appears in sidebar with name and preview
- [ ] CLI `graf-id add <name> <path>` also works (optional cross-check)
- [ ] Invalid path shows clear error (not silent failure)

---

## Select project

- [ ] Clicking sidebar row selects project (highlight active)
- [ ] Main area shows project name and Resume panel
- [ ] Switching projects updates content without app restart
- [ ] Search/filter/category tabs narrow list correctly

---

## Scan / refresh context

- [ ] **Refresh context** button runs (shows refreshing state)
- [ ] `last_refreshed_at` updates in Resume panel
- [ ] Summary reflects project files (HANDOFF/README) when present
- [ ] With only dirty git and no docs, git fallback still appears (expected)
- [ ] With docs + dirty git, human docs win over git file list
- [ ] Scan health notice appears if scan had warnings (when applicable)

---

## Summary generation

- [ ] Resume panel shows structured MVP sections or primary context block
- [ ] Sources listed match expected files (exit note, HANDOFF, git, etc.)
- [ ] Sidebar preview is short and readable (not multi-line blob)
- [ ] **More details** collapsed by default; expands with path, session, git, markers

---

## Open project

- [ ] **Open project** updates last opened and starts/resumes session
- [ ] Cursor or VS Code opens when configured (or clear fallback message)
- [ ] **Open folder** opens Explorer at project path

---

## Settings

- [ ] Settings page loads from bootstrap cache
- [ ] Default opener / journal toggles save (if exposed in UI)
- [ ] `config.json` under `%LOCALAPPDATA%\Graf-Id` updates when settings change

---

## History

- [ ] History tab loads scan rows for selected project
- [ ] History is read-only (no accidental delete in UI)
- [ ] Retry works if history fetch failed

---

## Exit note

- [ ] **End session** opens modal
- [ ] Submitting exit note + next step closes active session
- [ ] After refresh, summary includes exit note content
- [ ] Skip/end without notes still closes session (weaker summary acceptable)

---

## Restart app / persistence

- [ ] Quit and relaunch — projects still listed
- [ ] Last selected project / session state persisted in SQLite
- [ ] Exit note from previous session still in summary after restart
- [ ] User data remains in `%LOCALAPPDATA%\Graf-Id` (not install dir)

---

## Packaged build (release QA)

- [ ] `npm run build:runtime` succeeds
- [ ] `npm run tauri:build` produces `.exe` + installers
- [ ] Packaged app runs **without** repo `.venv`
- [ ] Refresh context works in packaged build
- [ ] `packaging\verify_release_bundle.ps1` passes (optional)

---

## GrafiTalk export (optional)

- [ ] `graf-id export-grafitalk` writes `grafitalk/manifest.json` + `projects/*.json`
- [ ] JSON contains `resume_panel` and `project` keys

---

## Regression spots

- [ ] Sidebar selection does not break History or Settings nav
- [ ] `cargo clean` + rebuild — app still runs (see [CLEANUP.md](CLEANUP.md))
- [ ] No GrafiTalk repo files modified from Graph-Id work

---

## Sign-off

| Field | Value |
|-------|-------|
| Tester | |
| Date | |
| Build | dev / packaged version |
| Result | PASS / FAIL |
| Notes | |
