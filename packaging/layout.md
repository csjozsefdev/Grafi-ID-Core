# Expected release layout (Windows)

```
install/
  Graf-Id.exe
  runtime/
    python.exe
    Lib/site-packages/grafid/...
  (Tauri WebView assets)
```

```
%LOCALAPPDATA%\Graf-Id/
  config.json
  graf-id.db
  logs/
```

Portable option: set `GRAFID_DATA_DIR` to a folder beside the executable (e.g. `.\data`).
