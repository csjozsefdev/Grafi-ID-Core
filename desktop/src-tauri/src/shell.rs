//! OS shell helpers for opening folders and terminals (no Python required).

use std::path::Path;
use std::process::Command;

/// Resolve to an existing directory and return a shell-safe UTF-8 path string.
fn resolve_directory_path(path: &str) -> Result<String, String> {
    let folder = Path::new(path);
    let canonical = folder.canonicalize().map_err(|e| {
        format!("folder_not_found: path does not exist or is inaccessible: {path} ({e})")
    })?;
    if !canonical.is_dir() {
        return Err(format!("folder_not_found: not a directory: {path}"));
    }
    path_to_shell_string(&canonical)
}

/// Strip Windows verbatim `\\?\` prefix so Explorer receives a normal path.
fn path_to_shell_string(path: &Path) -> Result<String, String> {
    let mut text = path
        .to_str()
        .ok_or_else(|| format!("path_not_utf8: {}", path.display()))?
        .to_string();
    if text.starts_with(r"\\?\UNC\") {
        text = format!(r"\\{}", &text[8..]);
    } else if text.starts_with(r"\\?\") {
        text = text[4..].to_string();
    }
    Ok(text)
}

/// Open the registered project root in the file manager (Open Folder — Rust-only).
pub fn open_folder(path: &str) -> Result<(), String> {
    let shell_path = resolve_directory_path(path)?;

    #[cfg(target_os = "windows")]
    {
        // Plain directory path — `/root,` fails silently with verbatim or Unicode paths.
        Command::new("explorer.exe")
            .arg(&shell_path)
            .spawn()
            .map_err(|e| format!("open_folder_failed: {e}"))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&shell_path)
            .spawn()
            .map_err(|e| format!("open_folder_failed: {e}"))?;
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        Command::new("xdg-open")
            .arg(&shell_path)
            .spawn()
            .map_err(|e| format!("open_folder_failed: {e}"))?;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;

    #[test]
    fn open_folder_rejects_missing_path() {
        let missing = PathBuf::from("C:\\graf-id-nonexistent-test-folder-xyz");
        let err = open_folder(missing.to_str().unwrap()).unwrap_err();
        assert!(err.contains("folder_not_found"));
    }

    #[test]
    fn open_folder_requires_directory() {
        let dir = std::env::temp_dir().join("graf-id-open-folder-test");
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).expect("temp dir");
        let file = dir.join("marker.txt");
        fs::write(&file, b"x").expect("write marker");
        let err = open_folder(file.to_str().unwrap()).unwrap_err();
        assert!(err.contains("not a directory"));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn strips_verbatim_prefix_for_shell() {
        let parsed = Path::new(r"\\?\C:\graf-id-test-strip");
        let text = path_to_shell_string(parsed).unwrap_or_else(|_| parsed.display().to_string());
        assert!(!text.starts_with(r"\\?\"));
    }
}

/// Open a terminal at the project path.
pub fn open_terminal(path: &str) -> Result<(), String> {
    let shell_path = resolve_directory_path(path)?;

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args([
                "/C",
                "start",
                "",
                "cmd",
                "/K",
                &format!("cd /d \"{shell_path}\""),
            ])
            .spawn()
            .map_err(|e| format!("open_terminal_failed: {e}"))?;
    }

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            "tell application \"Terminal\" to do script \"cd '{}'\"",
            shell_path.replace('\'', "'\\''")
        );
        Command::new("osascript")
            .args(["-e", &script])
            .spawn()
            .map_err(|e| format!("open_terminal_failed: {e}"))?;
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        Command::new("x-terminal-emulator")
            .args(["--working-directory", &shell_path])
            .spawn()
            .or_else(|_| {
                Command::new("gnome-terminal")
                    .args(["--working-directory", &shell_path])
                    .spawn()
                    .map_err(|e| format!("open_terminal_failed: {e}"))
            })?;
    }

    Ok(())
}
