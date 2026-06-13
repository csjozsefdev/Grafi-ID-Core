/**
 * Launch API boundaries (English-only).
 *
 * Open Folder — "show the directory"
 * - Use openProjectFolderPath(path) → Tauri open_project_folder (Rust explorer).
 * - No Python IPC, no workflow state, opens the registered project root exactly.
 *
 * Open Project — "resume the workflow"
 * - Use openProjectWorkflow(projectId) → Python ipc open-project.
 * - Updates last_opened_at and session; may launch editor.
 * - When launch.explorer_opened is true, call openProjectFolderPath once (deduped Explorer).
 *
 * CLI: graf-id ipc open-folder / graf-id open (Python may open Explorer in-process).
 */

export {};
