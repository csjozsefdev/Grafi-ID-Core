# Graph-Id design decisions

Major architectural and product choices — recorded so future work does not accidentally undo them.

---

## Local-first

**Decision:** All user data stays on the machine (`%LOCALAPPDATA%\Graf-Id` by default).

**Why:** Privacy, offline use, no account friction, predictable ownership. Graph-Id is a personal utility, not a hosted service.

**Implication:** No sync, no multi-device state, no cloud backup built-in (zip export exists for manual backup).

---

## English internal data

**Decision:** UI copy, CLI messages, summary labels, and documentation are **English-only** for MVP.

**Why:** Single locale reduces test surface and keeps deterministic summary templates stable.

**Implication:** i18n is a future concern, not a silent addition.

---

## Optional AI (not in core)

**Decision:** The summary engine is **fully deterministic** — no LLM in the compose path.

**Why:** Explainability. Users must see *which source* produced each line. AI summaries are hard to trust for “where did I leave off.”

**Implication:** AI may exist in **ecosystem tools** (e.g. GrafiTalk) that consume exports — not inside Graph-Id’s core loop.

---

## AI only at startup (ecosystem)

**Decision:** If AI is used, it belongs in **downstream consumers** reading exported context at conversation start — not as a continuous monitor inside Graph-Id.

**Why:** Avoids creep toward “always-on agent” behavior that conflicts with explicit refresh philosophy.

---

## Deterministic core

**Decision:** `compose_workflow_summary()` uses a **fixed priority order** for signals.

**Why:** Same project state → same summary. Debuggable. Testable. No model drift.

**Implication:** Source priority changes are deliberate product decisions (see regression fix: docs beat git fallback).

---

## Exit Note concept

**Decision:** Sessions can end with structured human input: exit note, blocker, next step.

**Why:** The best continuity signal is what **you** write when pausing — not inferred git filenames.

**Implication:** UI encourages end session; weak summaries often mean missing exit note (by design nudge).

---

## JSON export for GrafiTalk

**Decision:** GrafiTalk integration is **file-based export** (`graf-id export-grafitalk`), not shared database or live API.

**Why:** Loose coupling. Graph-Id and GrafiTalk are separate repos/products. Read-only JSON inbox is easy to version and audit.

**See:** [GRAFITALK_INTEGRATION.md](GRAFITALK_INTEGRATION.md)

---

## No cloud dependency

**Decision:** No auth, no remote API, no telemetry pipeline required for core function.

**Why:** Aligns with local-first and “small utility” scope.

**Optional:** Usage journal is opt-in local logging only.

---

## No continuous AI monitoring

**Decision:** No background agent watching repos, no automatic “insights” push.

**Why:** Scope control, CPU trust, and user intent — refresh is explicit.

---

## Project continuity first

**Decision:** Product center is **resume / wake-up**, not task tracking or doc editing.

**Why:** Differentiated from PM tools and AI IDEs. Graph-Id answers one question well.

**UI reflection:** Resume panel is primary; technical metadata is behind “More details.”

---

## Explicit refresh (no file watcher)

**Decision:** Scans run on **Refresh context** or CLI scan — not on filesystem events.

**Why:** Bounded work, reproducible behavior, no daemon.

**See:** [PERFORMANCE_ARCHITECTURE.md](PERFORMANCE_ARCHITECTURE.md)

---

## Tauri + Python sidecar

**Decision:** Desktop UI in React/Tauri; business logic in Python subprocess IPC.

**Why:** Reuse CLI/core logic. Avoid duplicating scanner/resume in Rust.

**Trade-off:** Cold-start cost per IPC call — mitigated by bootstrap cache.

---

## Embedded Python for releases

**Decision:** Packaged app ships `runtime/python.exe` + stdlib + `grafid` — built by `packaging/build_runtime.ps1`.

**Why:** End users should not install Python.

**Trade-off:** Large build artifacts; `runtime/` gitignored; rebuild after backend changes.

---

## SQLite as single store

**Decision:** One `graf-id.db` for projects, sessions, scans, resumes.

**Why:** Simple, local, sufficient for MVP scale.

**Implication:** GrafiTalk does not attach to this DB — export only.

---

## Related docs

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [CORE_STATUS.md](CORE_STATUS.md)
