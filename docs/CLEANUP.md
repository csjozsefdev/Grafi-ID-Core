# Graph-Id storage cleanup

This guide explains why `desktop/src-tauri` can grow very large on disk, what is safe to delete, and how to recover space without breaking the project.

**Typical audit result:** ~8 GB total, with **~98% in `target/`** (Rust/Cargo cache) and **~125 MB in `runtime/`** (intentional embedded Python).

---

## Why `src-tauri` can grow large

The Tauri desktop shell uses **Rust/Cargo**. Every `tauri dev` and `tauri build` run compiles dependencies and stores output under:

```
desktop/src-tauri/target/
```

On an active Windows dev machine, `target/` commonly reaches **several gigabytes** because it contains:

- **Debug builds** (`target/debug/`) — object files (`.o`), libraries (`.rlib`), Windows debug symbols (`.pdb`)
- **Incremental compilation caches** (`target/debug/incremental/`) — rustc reuse data between builds
- **Release builds** (`target/release/`) — optimized binaries, installer staging (MSI/NSIS)
- **Copied embedded Python** inside `target/*/runtime/` during builds (~100–125 MB per copy)

This is **normal Cargo behavior**. It is not application data, logs, or duplicate GrafiTalk content.

A typical audit for this repo found **~7.9 GB** in `src-tauri`, with **~98% in `target/`** and only **~125 MB** in the intentional `runtime/` tree.

---

## What is safe to delete

| Path | Safe? | Notes |
|------|-------|-------|
| `desktop/src-tauri/target/` | **Yes** | Entire Rust build cache. Regenerated on next `cargo` / `tauri` command. |
| `target/debug/` | **Yes** | Largest dev-build footprint. |
| `target/debug/incremental/` | **Yes** | Stale incremental caches. |
| `target/debug/deps/` | **Yes** | Compiled dependencies for debug profile. |
| `target/release/deps/` | **Yes** | Release dependency artifacts (rebuild with `tauri build`). |
| `target/release/build/` | **Yes** | Release build-script output. |
| Installer files under `target/release/bundle/` | **Optional** | Safe to delete if you can rerun `tauri build` to recreate MSI/NSIS. |

### Preferred cleanup command

From `desktop/src-tauri`:

```powershell
cd C:\Projektek\Grap-Id\desktop\src-tauri
cargo clean
```

This removes the whole `target/` directory and typically recovers **~7–8 GB** after heavy dev use.

**Tip:** Close the running Graph-Id app first. If `graf-id-desktop.exe` is still running from `target/release/`, Windows may lock the file and `cargo clean` can fail with “access denied”. Quit the app and run `cargo clean` again.

---

## What to keep

Do **not** casually delete these:

| Path | Why |
|------|-----|
| `desktop/src-tauri/runtime/` | Embedded Python + `grafid` package for packaged builds. Rebuild with `npm run build:runtime` if removed. |
| `desktop/src-tauri/src/` | Rust Tauri bridge source. |
| `desktop/src-tauri/icons/` | App icons for bundling. |
| `desktop/src-tauri/gen/` | Tauri generated config. |
| `desktop/src-tauri/capabilities/` | Tauri security capabilities. |
| `Cargo.toml`, `tauri.conf.json` | Project configuration. |

User data (SQLite, config, logs) lives under **`%LOCALAPPDATA%\Graf-Id`**, not in `src-tauri`.

---

## Expected size after cleanup

| State | Approximate `src-tauri` size |
|-------|------------------------------|
| After `cargo clean` | **~125 MB** (mostly `runtime/`) |
| After `cargo check` | **~1–3 GB** (debug artifacts only) |
| After `tauri dev` / many debug sessions | **3–8 GB** (grows over time) |
| After `tauri build` (release + installers) | **+1–2 GB** on top of debug cache |

Exact numbers depend on how many times you built and which profiles were used.

---

## Expected rebuild cost

After `cargo clean`:

| Command | What happens | Rough time (this machine) |
|---------|----------------|---------------------------|
| `cargo check` | Recompiles dependencies + app (debug) | ~5–10 minutes |
| `npm run tauri:dev` | Debug app + frontend dev server | First run slower after clean |
| `npm run tauri:build` | Full release + embedded runtime + installers | ~10–20+ minutes |

No source or Python application logic is lost. Only compiled cache is removed.

---

## Git ignore

`target/` is already ignored:

- `.gitignore` → `desktop/src-tauri/target/`
- `desktop/.gitignore` → `src-tauri/target/`

`runtime/` is also gitignored (large binaries). Regenerate with:

```powershell
cd C:\Projektek\Grap-Id\desktop
npm run build:runtime
```

---

## Quick checklist

1. Quit Graph-Id if it is running.
2. `cd desktop\src-tauri`
3. `cargo clean`
4. Confirm `runtime/` still exists.
5. `cargo check` or `npm run tauri:dev` to verify rebuild.
6. Optional: measure folder size before/after for your own records.

---

## Related docs

- [HANDOVER.md](HANDOVER.md) — returning to the project after months away
- [CORE_STATUS.md](CORE_STATUS.md) — archive / maintenance status
- [desktop/README.md](../desktop/README.md) — dev and release workflow
- [packaging/README.md](../packaging/README.md) — embedded runtime build
- [README.md](../README.md) — project overview
