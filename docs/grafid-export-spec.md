# grafid-export.json (v1)

Loose interchange format for Graph-Id ecosystem tools (Grap-h, KeepMeRollin, GrafiTalk).

For **live summary files** (no zip), see [grafitalk-inbox.md](grafitalk-inbox.md) and `graf-id export-grafitalk`.

## Bundle layout

```
export.zip
├── grafid-export.json   # manifest
├── graf-id.db           # SQLite database
├── config.json          # optional user config
└── README.md            # human instructions
```

## Manifest fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | int | Export format version (currently `1`) |
| `schema_version` | int | SQLite schema version at export time |
| `exported_at` | ISO-8601 | UTC timestamp |
| `app` | string | Always `"Graph-Id"` |
| `project_count` | int | Number of registered projects |

## CLI

- `graf-id export <path.zip>` — create bundle
- `graf-id import <path.zip> [--replace]` — restore to local config dir
- `graf-id maintenance vacuum` — SQLite VACUUM
- `graf-id maintenance prune-snapshots` — apply retention policy

## Coupling

Consumers should treat this as **read-only input**. No shared auth, cloud sync, or live bus.
