mod python;
mod shell;

use serde_json::Value;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Manager};

const TRAY_MENU_SHOW: &str = "tray_show";
const TRAY_MENU_QUIT: &str = "tray_quit";

fn main_webview_window(app: &AppHandle) -> Result<tauri::WebviewWindow, String> {
    app.get_webview_window("main")
        .ok_or_else(|| "main_window_missing".to_string())
}

fn show_main_window_impl(app: &AppHandle) -> Result<(), String> {
    let window = main_webview_window(app)?;
    window.show().map_err(|e| e.to_string())?;
    window.set_focus().map_err(|e| e.to_string())
}

#[tauri::command]
fn hide_main_window(app: AppHandle) -> Result<(), String> {
    main_webview_window(&app)?.hide().map_err(|e| e.to_string())
}

#[tauri::command]
fn show_main_window(app: AppHandle) -> Result<(), String> {
    show_main_window_impl(&app)
}

#[tauri::command]
fn quit_app(app: AppHandle) {
    app.exit(0);
}

fn setup_system_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let show_item = MenuItem::with_id(
        app,
        TRAY_MENU_SHOW,
        "Show Graph-Id",
        true,
        None::<&str>,
    )?;
    let quit_item = MenuItem::with_id(
        app,
        TRAY_MENU_QUIT,
        "Quit Graph-Id",
        true,
        None::<&str>,
    )?;
    let menu = Menu::with_items(app, &[&show_item, &quit_item])?;
    let icon = app
        .default_window_icon()
        .cloned()
        .ok_or("tray_icon_missing")?;

    TrayIconBuilder::new()
        .icon(icon)
        .menu(&menu)
        .tooltip("Graf-Id")
        .on_menu_event(|app, event| match event.id.as_ref() {
            TRAY_MENU_SHOW => {
                let _ = show_main_window_impl(app);
            }
            TRAY_MENU_QUIT => {
                app.exit(0);
            }
            _ => {}
        })
        .build(app)?;

    Ok(())
}

#[tauri::command]
fn ipc_health() -> Result<Value, String> {
    python::run_ipc("health", &[])
}

#[tauri::command]
fn ipc_bootstrap() -> Result<Value, String> {
    python::run_ipc("bootstrap", &[])
}

#[tauri::command]
fn ipc_dashboard() -> Result<Value, String> {
    python::run_ipc("dashboard", &[])
}

#[tauri::command]
fn ipc_project_detail(project_id: u32) -> Result<Value, String> {
    let id = project_id.to_string();
    python::run_ipc("project-detail", &[id.as_str()])
}

#[tauri::command]
fn ipc_project_history(project_id: u32) -> Result<Value, String> {
    let id = project_id.to_string();
    python::run_ipc("project-history", &[id.as_str()])
}

#[tauri::command]
fn ipc_open_project(project_id: u32) -> Result<Value, String> {
    let id = project_id.to_string();
    python::run_ipc("open-project", &[id.as_str()])
}

#[tauri::command]
fn ipc_open_folder(project_id: u32) -> Result<Value, String> {
    let id = project_id.to_string();
    python::run_ipc("open-folder", &[id.as_str()])
}

#[tauri::command]
fn ipc_resume_preview(project_id: u32) -> Result<Value, String> {
    let id = project_id.to_string();
    python::run_ipc("resume-preview", &[id.as_str()])
}

#[tauri::command]
fn ipc_usage_insights() -> Result<Value, String> {
    python::run_ipc("usage-insights", &[])
}

#[tauri::command]
fn ipc_app_settings() -> Result<Value, String> {
    let response = python::run_ipc("app-settings", &[])?;
    python::patch_settings_paths(response)
}

#[tauri::command]
fn ipc_close_session(
    project_id: u32,
    exit_note: Option<String>,
    unfinished: Option<String>,
    blocker: Option<String>,
    next_step: Option<String>,
    skip_notes: bool,
) -> Result<Value, String> {
    let pid = project_id.to_string();
    let mut args: Vec<&str> = vec![pid.as_str()];
    let exit_value;
    if let Some(ref v) = exit_note {
        if !v.trim().is_empty() {
            exit_value = v.clone();
            args.push("--exit-note");
            args.push(exit_value.as_str());
        }
    }
    let unfinished_value;
    if let Some(ref v) = unfinished {
        if !v.trim().is_empty() {
            unfinished_value = v.clone();
            args.push("--unfinished");
            args.push(unfinished_value.as_str());
        }
    }
    let blocker_value;
    if let Some(ref v) = blocker {
        if !v.trim().is_empty() {
            blocker_value = v.clone();
            args.push("--blocker");
            args.push(blocker_value.as_str());
        }
    }
    let next_value;
    if let Some(ref v) = next_step {
        if !v.trim().is_empty() {
            next_value = v.clone();
            args.push("--next-step");
            args.push(next_value.as_str());
        }
    }
    if skip_notes {
        args.push("--skip-notes");
    }
    python::run_ipc("close-session", &args)
}

#[tauri::command]
fn ipc_refresh_resume(project_id: u32, git_only: Option<bool>) -> Result<Value, String> {
    let id = project_id.to_string();
    let mut args: Vec<&str> = vec![id.as_str()];
    if git_only == Some(true) {
        args.push("--git-only");
    }
    python::run_ipc("refresh-resume", &args)
}

#[tauri::command]
fn ipc_start_session(project_id: u32, checkpoint: Option<String>) -> Result<Value, String> {
    let id = project_id.to_string();
    let mut args: Vec<&str> = vec![id.as_str()];
    let checkpoint_value;
    if let Some(ref c) = checkpoint {
        if !c.trim().is_empty() {
            checkpoint_value = c.clone();
            args.push("--checkpoint");
            args.push(checkpoint_value.as_str());
        }
    }
    python::run_ipc("start-session", &args)
}

#[tauri::command]
fn ipc_session_timeline(project_id: u32, limit: Option<u32>) -> Result<Value, String> {
    let id = project_id.to_string();
    let mut args: Vec<&str> = vec![id.as_str()];
    let limit_value;
    if let Some(n) = limit {
        limit_value = n.to_string();
        args.push("--limit");
        args.push(limit_value.as_str());
    }
    python::run_ipc("session-timeline", &args)
}

#[tauri::command]
fn ipc_set_default_project_opener(opener: String) -> Result<Value, String> {
    python::run_ipc("set-default-project-opener", &[opener.as_str()])
}

#[tauri::command]
fn ipc_save_app_settings(
    opener: String,
    usage_journal: bool,
    debug_timing: bool,
    compact_mode: bool,
) -> Result<Value, String> {
    let uj = if usage_journal { "true" } else { "false" };
    let dt = if debug_timing { "true" } else { "false" };
    let cm = if compact_mode { "true" } else { "false" };
    python::run_ipc(
        "save-app-settings",
        &[
            "--opener",
            opener.as_str(),
            "--usage-journal",
            uj,
            "--debug-timing",
            dt,
            "--compact-mode",
            cm,
        ],
    )
}

#[tauri::command]
fn ipc_reset_app_settings() -> Result<Value, String> {
    python::run_ipc("reset-app-settings", &[])
}

#[tauri::command]
fn ipc_dismiss_startup(project_id: u32, startup_summary_id: Option<u32>) -> Result<Value, String> {
    let pid = project_id.to_string();
    let mut args: Vec<&str> = vec![pid.as_str()];
    let summary_id;
    if let Some(id) = startup_summary_id {
        summary_id = id.to_string();
        args.push("--summary-id");
        args.push(summary_id.as_str());
    }
    python::run_ipc("dismiss-startup", &args)
}

#[tauri::command]
fn ipc_add_project(name: String, path: String, category: Option<String>) -> Result<Value, String> {
    let mut args: Vec<&str> = vec![name.as_str(), path.as_str()];
    let category_value;
    if let Some(ref cat) = category {
        if !cat.trim().is_empty() {
            category_value = cat.clone();
            args.push("--category");
            args.push(category_value.as_str());
        }
    }
    python::run_ipc("add-project", &args)
}

#[tauri::command]
fn ipc_remove_project(project_id: u32) -> Result<Value, String> {
    let pid = project_id.to_string();
    python::run_ipc("remove-project", &[pid.as_str()])
}

#[tauri::command]
fn ipc_update_project(
    project_id: u32,
    name: Option<String>,
    path: Option<String>,
    category: Option<String>,
    status: Option<String>,
    notes: Option<String>,
) -> Result<Value, String> {
    let pid = project_id.to_string();
    let mut args: Vec<&str> = vec![pid.as_str()];
    let name_value;
    if let Some(ref n) = name {
        if !n.trim().is_empty() {
            name_value = n.clone();
            args.push("--name");
            args.push(name_value.as_str());
        }
    }
    let path_value;
    if let Some(ref p) = path {
        if !p.trim().is_empty() {
            path_value = p.clone();
            args.push("--path");
            args.push(path_value.as_str());
        }
    }
    let category_value;
    if let Some(ref c) = category {
        if !c.trim().is_empty() {
            category_value = c.clone();
            args.push("--category");
            args.push(category_value.as_str());
        }
    }
    let status_value;
    if let Some(ref s) = status {
        if !s.trim().is_empty() {
            status_value = s.clone();
            args.push("--status");
            args.push(status_value.as_str());
        }
    }
    let notes_value;
    if let Some(ref n) = notes {
        notes_value = n.clone();
        args.push("--notes");
        args.push(notes_value.as_str());
    }
    python::run_ipc("update-project", &args)
}

/// Open Folder boundary: show the registered project root in Explorer only.
/// Rust-only — no Python IPC, no DB/session updates, no subfolder navigation.
#[tauri::command]
fn open_project_folder(path: String) -> Result<(), String> {
    shell::open_folder(&path)
}

#[tauri::command]
fn open_project_terminal(path: String) -> Result<(), String> {
    shell::open_terminal(&path)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if let Ok(resource_dir) = app.path().resource_dir() {
                std::env::set_var("GRAFID_RESOURCE_DIR", resource_dir.to_string_lossy().to_string());
            }
            setup_system_tray(app.handle())?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            hide_main_window,
            show_main_window,
            quit_app,
            ipc_health,
            ipc_bootstrap,
            ipc_dashboard,
            ipc_project_detail,
            ipc_project_history,
            ipc_open_project,
            ipc_open_folder,
            ipc_resume_preview,
            ipc_dismiss_startup,
            ipc_usage_insights,
            ipc_app_settings,
            ipc_refresh_resume,
            ipc_start_session,
            ipc_session_timeline,
            ipc_close_session,
            ipc_set_default_project_opener,
            ipc_save_app_settings,
            ipc_reset_app_settings,
            ipc_add_project,
            ipc_remove_project,
            ipc_update_project,
            open_project_folder,
            open_project_terminal,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Graf-Id desktop");
}
