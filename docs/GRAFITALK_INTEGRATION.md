# GrafiTalk integration

How Graph-Id shares project context with **GrafiTalk** without coupling databases or live services.

---

## Principle

| Rule | Detail |
|------|--------|
| Graph-Id **exports** | Writes read-only JSON files |
| GrafiTalk **consumes** | Reads those files |
| **No direct DB coupling** | GrafiTalk never opens `graf-id.db` |
| **No live bus** | Re-export when user wants fresh context |

GrafiTalk is a **separate project**. Do not merge repos or share SQLite schemas.

---

## Preferred flow

```
Graph-Id (desktop or CLI)
        ↓
  refresh context / resume
        ↓
  graf-id export-grafitalk
        ↓
  grafitalk/projects/<id>-<slug>.json
  grafitalk/manifest.json
        ↓
  GrafiTalk reads inbox
        ↓
  AI conversation with project context (optional)
```

Conceptually each per-project file is a **project context document** — one JSON file per registered project.

---

## Export command

```powershell
graf-id export-grafitalk
graf-id export-grafitalk --out D:\GrafiTalk\inbox
graf-id grapitalk status
```

**When to run:** After Refresh context in the desktop app (or `graf-id resume`) so JSON matches latest summaries.

**Default output (dev checkout):**

```
<Graf-Id repo>/grafitalk/
├── README.md
├── manifest.json
└── projects/
    ├── 1-my-app.json
    └── 2-other-project.json
```

**Overrides:**

- `--out <path>`
- `GRAFID_GRAFITALK_DIR` environment variable

---

## Manifest schema (`manifest.json`)

```json
{
  "spec_version": 1,
  "exported_at": "2026-05-22T20:00:00+00:00",
  "app": "Graph-Id",
  "project_count": 2,
  "projects": [
    {
      "id": 1,
      "name": "my-app",
      "file": "projects/1-my-app.json",
      "headline": "Continue sidebar regression fix",
      "path": "C:\\dev\\my-app"
    }
  ]
}
```

---

## Per-project file schema (`projects/<id>-<slug>.json`)

```json
{
  "spec_version": 1,
  "exported_at": "2026-05-22T20:00:00+00:00",
  "project": {
    "id": 1,
    "name": "my-app",
    "path": "C:\\dev\\my-app",
    "category": "Client Work",
    "status": "active",
    "last_opened_at": "2026-05-22T18:30:00+00:00",
    "git_status": {
      "state": "dirty",
      "label": "Dirty",
      "branch": "main",
      "is_git_repo": true,
      "is_dirty": true
    },
    "summary_preview": {
      "headline": "sidebar regression fix",
      "summary_text": "Where you left off: ...\nSuggested next step: ..."
    },
    "latest_session": {
      "id": 12,
      "is_active": false,
      "exit_note": "Fixed source priority",
      "next_step": "Run QA checklist"
    }
  },
  "resume_panel": {
    "startup_summary": {
      "headline": "sidebar regression fix",
      "summary_text": "Where you left off: ...",
      "source": "summary_engine",
      "sources_used": ["HANDOVER.md", "exit note"],
      "mvp_sections": [
        { "title": "Where you left off", "body": "..." }
      ]
    },
    "blocker": null,
    "next_step": "Run QA checklist",
    "exit_note": "Fixed source priority",
    "modified_files": ["desktop/src/utils/continuity.ts"],
    "workflow_files": ["HANDOVER.md", "README.md"]
  }
}
```

**GrafiTalk should prefer:**

- `resume_panel.startup_summary.summary_text` or `summary_preview.summary_text` for prompts
- `resume_panel.startup_summary.headline` for short titles
- `project.path` to correlate with workspace
- `resume_panel.sources_used` for transparency

---

## Full zip export (migration / backup)

Separate from GrafiTalk inbox — for backup and migration:

```powershell
graf-id export backup.zip
graf-id import backup.zip
```

Spec: [grafid-export-spec.md](grafid-export-spec.md) (`grafid-export.json` manifest inside zip).

---

## Integration status

| Item | Status |
|------|--------|
| `export-grafitalk` CLI | **Implemented** |
| Per-project JSON + manifest | **Implemented** |
| GrafiTalk auto-watch | **Not in Graph-Id** (GrafiTalk responsibility) |
| Live sync | **Out of scope** |

---

## Related docs

- [grafitalk-inbox.md](grafitalk-inbox.md) — original inbox notes
- [grafid-export-spec.md](grafid-export-spec.md) — zip bundle format
- [DECISIONS.md](DECISIONS.md) — why file-based export
