/** IPC types mirroring Python grafid.ipc envelope (English-only). */

export type GrafiIconState = "idle" | "attention" | "ready" | "paused";

export type GitStateKind = "unknown" | "not_repo" | "clean" | "dirty";

export type NavSection = "dashboard" | "history" | "settings";

export interface OpenerOption {
  id: string;
  label: string;
}

export interface AppSettingsData {
  data_dir: string;
  logs_dir: string;
  config_dir: string;
  config_path: string;
  default_project_opener: string;
  usage_journal_enabled: boolean;
  debug_timing_enabled: boolean;
  compact_mode?: boolean;
  opener_options: OpenerOption[];
}

export interface IpcError {
  code: string;
  message: string;
}

export interface IpcResponse<T = Record<string, unknown>> {
  ok: boolean;
  data?: T;
  error?: IpcError;
}

export interface GitStatus {
  state: GitStateKind;
  label: string;
  is_git_repo: boolean;
  is_dirty: boolean;
  branch: string | null;
}

export interface SessionSummary {
  id: number;
  started_at: string;
  ended_at: string | null;
  is_active: boolean;
  status: string;
  summary: string | null;
  exit_note: string | null;
  blocker: string | null;
  next_step: string | null;
}

export interface SummaryPreview {
  headline: string;
  summary_text: string;
  generated_at: string;
}

export interface WorkflowLaunchResult {
  success: boolean;
  message: string;
  editor_launched: boolean;
  /** When true, desktop opens Explorer once via Rust (registered project root). */
  explorer_opened: boolean;
  fallback_used: boolean;
  action: "editor" | "explorer";
  editor: string | null;
  session_id: number | null;
  session_started: boolean;
  /** Alias for explorer_opened (legacy backend field). */
  open_explorer: boolean;
}

export interface OpenProjectResult {
  project: DashboardProject;
  launch: WorkflowLaunchResult;
}

export interface OpenFolderResult {
  project_id: number;
  path: string;
  message: string;
}

export interface SessionTimelineEntry {
  session_id: number;
  started_at: string;
  ended_at: string | null;
  status: string;
  exit_note_preview: string | null;
  duration_label: string | null;
}

export interface AttributedLine {
  text: string;
  source: string;
}

export interface ScanHealth {
  warnings_count: number;
  skipped_files_count: number;
  scanned_files_count?: number;
  findings_count?: number;
  duration_seconds?: number;
  messages: string[];
}

export interface RefreshContract {
  scan_ok: boolean;
  snapshot_id: number | null;
  scan_error?: string | null;
  git_ok: boolean;
  mode: string;
  snapshots_pruned?: number;
}

export interface DashboardProject {
  id: number;
  name: string;
  path: string;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
  preferred_ide: string | null;
  is_active: boolean;
  has_open_session?: boolean;
  category: string;
  status: string;
  notes: string | null;
  last_refreshed_at: string | null;
  latest_session: SessionSummary | null;
  summary_preview: SummaryPreview | null;
  git_status: GitStatus;
  has_resume: boolean;
  open_task_count: number | null;
  latest_scan_at: string | null;
  /** Cached panel to avoid IPC on project selection. */
  resume_panel?: ResumePanelData;
  /** Cached scan history to avoid IPC on History tab open. */
  history?: HistoryRow[];
}

export interface GrafiPayload {
  icon_state: GrafiIconState;
  summary_text: string;
  scroll_content: string;
  is_closable: boolean;
  is_dismissed: boolean;
  project_id: number | null;
  project_name: string | null;
  startup_summary_id: number | null;
}

export interface DismissStartupResult {
  dismissed: boolean;
  startup_summary_id?: number;
  project_id: number;
  is_dismissed?: boolean;
  message?: string;
}

export interface StartupSummaryData {
  project_id: number | null;
  project_name: string | null;
  session_id: number | null;
  headline: string;
  summary_text: string;
  scroll_content: string;
  startup_summary_id: number | null;
  has_unfinished_session: boolean;
  is_empty: boolean;
  grafi: GrafiPayload;
}

export interface PassiveRuntimeData {
  is_passive: boolean;
  monitoring_enabled: boolean;
  ai_enabled: boolean;
  message: string;
}

export interface StartupCardData {
  visible: boolean;
  is_dismissed: boolean;
  reason: string | null;
  message: string | null;
  project_id: number | null;
  project_name: string | null;
  startup_summary_id: number | null;
  session_id: number | null;
  icon_state: GrafiIconState;
  headline: string;
  summary_text: string;
  scroll_content: string;
  has_unfinished_session: boolean;
  is_empty: boolean;
  latest_session: SessionSummary | null;
  last_opened_at: string | null;
  open_task_count: number | null;
  latest_scan_at: string | null;
  blocker: string | null;
  next_step: string | null;
  exit_note: string | null;
  modified_files: string[];
  git_status?: GitStatus;
  startup_summary?: StartupSummaryBlock | null;
}

export interface BootstrapData {
  config_dir: string;
  config_path: string;
  database_path: string;
  schema_version: number;
  projects: DashboardProject[];
  /** Cached settings to avoid IPC on Settings open. */
  app_settings?: AppSettingsData | null;
  startup_summary: StartupSummaryData | null;
  startup_card: StartupCardData | null;
  passive_runtime: PassiveRuntimeData;
}

export interface MvpSection {
  title: string;
  body: string;
}

export interface StartupSummaryBlock {
  headline: string;
  summary_text: string;
  scroll_excerpt: string | null;
  generated_at: string;
  grifi_icon_state: GrafiIconState;
  source?: string;
  sources_used?: string[];
  attributed_lines?: AttributedLine[];
  timeline?: SessionTimelineEntry[];
  away_label?: string | null;
  workflow_files?: string[];
  confidence?: string;
  mvp_sections?: MvpSection[];
}

export interface ResumePanelData {
  startup_summary: StartupSummaryBlock | null;
  blocker: string | null;
  next_step: string | null;
  exit_note: string | null;
  modified_files: string[];
  stored_resume_excerpt: string | null;
  git_status: GitStatus;
  has_stored_resume: boolean;
  latest_session: SessionSummary | null;
  last_opened_at: string | null;
  open_task_count: number | null;
  latest_scan_at: string | null;
  last_refreshed_at?: string | null;
  workflow_files?: string[];
  sources_used?: string[];
  timeline?: SessionTimelineEntry[];
  attributed_lines?: AttributedLine[];
  away_label?: string | null;
  confidence?: string;
  mvp_sections?: MvpSection[];
}

export interface HistoryRow {
  snapshot_id: number;
  scanned_at: string;
  findings_count: number;
  scanned_files_count: number;
  duration_seconds: number;
  git_branch: string | null;
  git_dirty: boolean | null;
  is_git_repo: boolean;
}

export interface ProjectDetailData {
  project: DashboardProject;
  resume_panel: ResumePanelData;
  /** Loaded via `project-history` when the History tab is opened. */
  history?: HistoryRow[];
}

export type AppLoadState =
  | { status: "loading" }
  | { status: "ready"; bootstrap: BootstrapData }
  | { status: "error"; title: string; message: string; code?: string };
