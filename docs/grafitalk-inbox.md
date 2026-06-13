# GrafiTalk inbox (Graph-Id export)

Read-only folder of project summaries for **GrafiTalk** and other local tools. No cloud sync, no live bus.

## Default location

```
<Graf-Id repo>/grafitalk/
├── README.md
├── manifest.json
└── projects/
    ├── 1-my-app.json
    └── 2-other-project.json
```

On this machine (typical dev checkout):

`c:\Projektek\Grap-Id\grafitalk\`

Override:

- `--out <path>` on export
- `GRAFID_GRAFITALK_DIR` environment variable

## Export (refresh summaries on disk)

```powershell
graf-id export-grafitalk
graf-id export-grafitalk --out D:\GrafiTalk\inbox
graf-id grapitalk status
```

Run after **Refresh context** in the desktop app (or `graf-id resume`) so JSON files match the latest summaries.

## Per-project file (`projects/<id>-<slug>.json`)

| Field | Description |
|-------|-------------|
| `spec_version` | Inbox format version (`1`) |
| `exported_at` | UTC ISO timestamp |
| `project` | Dashboard project row (id, name, path, git, session flags, …) |
| `resume_panel` | Headline, `summary_text`, MVP sections, timeline, sources |

## Manifest (`manifest.json`)

Index for GrafiTalk: `project_count`, `exported_at`, and a `projects[]` list with `file`, `headline`, `path`.

## GrafiTalk integration notes

- Treat files as **read-only** input; Graph-Id owns the database.
- Re-export when the user wants fresh context (no file watcher from Graph-Id).
- Prefer `resume_panel.summary_text` and `resume_panel.headline` for prompts; use `project.path` to correlate with the workspace.

See also [grafid-export-spec.md](grafid-export-spec.md) for full zip backup/migration.
