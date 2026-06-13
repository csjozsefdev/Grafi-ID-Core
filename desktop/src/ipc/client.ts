/**
 * Frontend IPC client — Tauri commands only (no direct DB or Python imports).
 *
 * See launch.ts for Open Folder vs Open Project boundaries.
 */

import { invoke } from "@tauri-apps/api/core";
import { formatUserError, parseErrorCode } from "./errors";
import { normalizeOpenProjectResult } from "./launchNormalize";
import type {
  AppSettingsData,
  BootstrapData,
  DashboardProject,
  DismissStartupResult,
  IpcResponse,
  OpenFolderResult,
  OpenProjectResult,
  ProjectDetailData,
  HistoryRow,
  RefreshContract,
  ResumePanelData,
  ScanHealth,
} from "./types";

/** In-memory bootstrap payload (one Python subprocess per app session). */
let bootstrapCache: BootstrapData | null = null;

function debugTimingEnabled(): boolean {
  return bootstrapCache?.app_settings?.debug_timing_enabled === true;
}

function traceUi(action: string, detail: Record<string, unknown>): void {
  if (!debugTimingEnabled()) {
    return;
  }
  console.debug(`[grafid-ui] ${action}`, detail);
}

async function invokeIpc<T>(
  action: string,
  command: string,
  args?: Record<string, unknown>
): Promise<T> {
  const started = performance.now();
  traceUi(action, { phase: "start", invoke: command, spawned_python: true });
  try {
    const result = (await invoke(command, args)) as T;
    traceUi(action, {
      phase: "end",
      invoke: command,
      spawned_python: true,
      elapsed_ms: Math.round(performance.now() - started),
    });
    return result;
  } catch (err) {
    traceUi(action, {
      phase: "error",
      invoke: command,
      spawned_python: true,
      elapsed_ms: Math.round(performance.now() - started),
    });
    throw err;
  }
}

function assertOk<T>(response: IpcResponse<T>): T {
  if (!response.ok || response.data === undefined) {
    const message = response.error?.message ?? "Backend request failed";
    const code = response.error?.code ?? "ipc_error";
    const err = new Error(`${code}: ${message}`);
    throw err;
  }
  return response.data;
}

/** User-facing message from a thrown IPC/client error. */
export function getUserErrorMessage(err: unknown): string {
  return formatUserError(err);
}

export { parseErrorCode };

export async function fetchAppSettings(): Promise<AppSettingsData> {
  const started = performance.now();
  const bootstrap = await fetchBootstrap();
  const cached = bootstrap.app_settings;
  if (cached) {
    traceUi("settings.open", {
      phase: "end",
      spawned_python: false,
      source: "bootstrap_cache",
      elapsed_ms: Math.round(performance.now() - started),
    });
    return cached;
  }
  // Fallback for older backends; should not happen in the packaged app.
  const raw = await invokeIpc<IpcResponse<AppSettingsData>>(
    "settings.open",
    "ipc_app_settings"
  );
  return assertOk(raw);
}

export async function saveDefaultProjectOpener(
  opener: string
): Promise<{ default_project_opener: string; message: string }> {
  const raw = await invoke<
    IpcResponse<{ default_project_opener: string; message: string }>
  >("ipc_set_default_project_opener", { opener });
  return assertOk(raw);
}

export interface SaveAppSettingsResult extends AppSettingsData {
  message: string;
}

export async function saveAppSettings(input: {
  default_project_opener: string;
  usage_journal_enabled: boolean;
  debug_timing_enabled: boolean;
  compact_mode?: boolean;
}): Promise<SaveAppSettingsResult> {
  const raw = await invoke<IpcResponse<SaveAppSettingsResult>>("ipc_save_app_settings", {
    opener: input.default_project_opener,
    usageJournal: input.usage_journal_enabled,
    debugTiming: input.debug_timing_enabled,
    compactMode: input.compact_mode ?? false,
  });
  return assertOk(raw);
}

export async function resetAppSettings(): Promise<SaveAppSettingsResult> {
  const raw = await invoke<IpcResponse<SaveAppSettingsResult>>("ipc_reset_app_settings");
  return assertOk(raw);
}

export async function fetchBootstrap(): Promise<BootstrapData> {
  if (bootstrapCache) {
    traceUi("bootstrap", {
      phase: "end",
      spawned_python: false,
      source: "memory_cache",
      elapsed_ms: 0,
    });
    return bootstrapCache;
  }
  const raw = await invokeIpc<IpcResponse<BootstrapData>>("bootstrap", "ipc_bootstrap");
  const data = assertOk(raw);
  bootstrapCache = data;
  return data;
}

export async function fetchDashboardProjects(): Promise<DashboardProject[]> {
  const raw = await invoke<IpcResponse<{ projects: DashboardProject[] }>>("ipc_dashboard");
  return assertOk(raw).projects;
}

export interface AddProjectResult {
  project: DashboardProject;
  message: string;
}

export async function addProject(
  name: string,
  path: string,
  category?: string
): Promise<AddProjectResult> {
  const raw = await invoke<IpcResponse<AddProjectResult>>("ipc_add_project", {
    name,
    path,
    category: category ?? null,
  });
  return assertOk(raw);
}

export interface RemoveProjectResult {
  project_id: number;
  project_name: string;
  message: string;
}

export interface UpdateProjectInput {
  name?: string;
  path?: string;
  category?: string;
  status?: string;
  notes?: string;
}

export interface UpdateProjectResult {
  project: DashboardProject;
  message: string;
}

export async function updateProject(
  projectId: number,
  input: UpdateProjectInput
): Promise<UpdateProjectResult> {
  const raw = await invoke<IpcResponse<UpdateProjectResult>>("ipc_update_project", {
    projectId,
    name: input.name ?? null,
    path: input.path ?? null,
    category: input.category ?? null,
    status: input.status ?? null,
    notes: input.notes ?? null,
  });
  return assertOk(raw);
}

export async function removeProject(projectId: number): Promise<RemoveProjectResult> {
  const raw = await invoke<IpcResponse<RemoveProjectResult>>("ipc_remove_project", {
    projectId,
  });
  return assertOk(raw);
}

export interface CloseSessionInput {
  exit_note?: string;
  unfinished?: string;
  blocker?: string;
  next_step?: string;
  skip_notes?: boolean;
}

export interface CloseSessionResult {
  project: DashboardProject;
  resume_panel: ResumePanelData;
  message: string;
}

export async function closeProjectSession(
  projectId: number,
  input: CloseSessionInput
): Promise<CloseSessionResult> {
  const raw = await invoke<IpcResponse<CloseSessionResult>>("ipc_close_session", {
    projectId,
    exitNote: input.exit_note ?? null,
    unfinished: input.unfinished ?? null,
    blocker: input.blocker ?? null,
    nextStep: input.next_step ?? null,
    skipNotes: input.skip_notes ?? false,
  });
  return assertOk(raw);
}

export interface RefreshResumeResult extends Pick<ProjectDetailData, "project" | "resume_panel"> {
  refresh?: RefreshContract;
  scan_health?: ScanHealth;
  last_refreshed_at?: string;
}

export async function refreshProjectResume(
  projectId: number,
  options?: { gitOnly?: boolean }
): Promise<RefreshResumeResult> {
  const raw = await invokeIpc<IpcResponse<RefreshResumeResult>>(
    "refresh.context",
    "ipc_refresh_resume",
    {
      projectId,
      gitOnly: options?.gitOnly ?? false,
    }
  );
  const data = assertOk(raw);
  if (bootstrapCache) {
    const idx = bootstrapCache.projects.findIndex((p) => p.id === projectId);
    if (idx >= 0) {
      const prev = bootstrapCache.projects[idx];
      bootstrapCache.projects[idx] = {
        ...prev,
        ...data.project,
        resume_panel: data.resume_panel,
      };
    }
  }
  return data;
}

export async function fetchProjectDetail(
  projectId: number
): Promise<ProjectDetailData> {
  const started = performance.now();
  const bootstrap = await fetchBootstrap();
  const project = bootstrap.projects.find((p) => p.id === projectId) ?? null;
  const panel = project?.resume_panel ?? null;
  const history = project?.history ?? [];
  if (project && panel) {
    traceUi("project.select", {
      phase: "end",
      spawned_python: false,
      source: "bootstrap_cache",
      project_id: projectId,
      elapsed_ms: Math.round(performance.now() - started),
    });
    return { project, resume_panel: panel, history };
  }
  // Fallback for older backends; should not happen in the packaged app.
  const raw = await invokeIpc<IpcResponse<ProjectDetailData>>(
    "project.select",
    "ipc_project_detail",
    { projectId }
  );
  return assertOk(raw);
}

export async function fetchProjectHistory(
  projectId: number
): Promise<HistoryRow[]> {
  const bootstrap = await fetchBootstrap();
  const project = bootstrap.projects.find((p) => p.id === projectId) ?? null;
  if (project?.history) {
    return project.history;
  }
  // Fallback for older backends; should not happen in the packaged app.
  const raw = await invoke<IpcResponse<{ history: HistoryRow[] }>>("ipc_project_history", {
    projectId,
  });
  return assertOk(raw).history;
}

/** Open Project: Python IPC for session, editor, and launch metadata. */
export async function openProjectWorkflow(
  projectId: number
): Promise<OpenProjectResult> {
  const raw = await invokeIpc<IpcResponse<Record<string, unknown>>>(
    "open.project",
    "ipc_open_project",
    { projectId }
  );
  try {
    const result = normalizeOpenProjectResult(assertOk(raw));
    if (bootstrapCache) {
      const idx = bootstrapCache.projects.findIndex((p) => p.id === projectId);
      if (idx >= 0) {
        const prev = bootstrapCache.projects[idx];
        bootstrapCache.projects[idx] = {
          ...prev,
          ...result.project,
        };
      }
    }
    return result;
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    if (detail.startsWith("launch_failed:")) {
      throw err;
    }
    throw new Error(`launch_failed: ${detail}`);
  }
}

/**
 * Open Folder: Rust-only Explorer for the registered project root path.
 * Do not route the desktop Open Folder button through ipc_open_folder.
 */
export async function openProjectFolderPath(path: string): Promise<void> {
  await invoke("open_project_folder", { path });
}

/** Open Project workflow state (Python IPC). See openProjectWorkflow. */
export async function openProjectFolder(projectId: number): Promise<OpenFolderResult> {
  const raw = await invoke<IpcResponse<OpenFolderResult>>("ipc_open_folder", {
    projectId,
  });
  return assertOk(raw);
}

export async function openProjectTerminal(path: string): Promise<void> {
  await invoke("open_project_terminal", { path });
}

export async function fetchResumePreview(
  projectId: number
): Promise<ResumePanelData> {
  const raw = await invoke<IpcResponse<{ resume_preview: ResumePanelData }>>(
    "ipc_resume_preview",
    { projectId }
  );
  return assertOk(raw).resume_preview;
}

export async function dismissStartupSummary(
  projectId: number,
  startupSummaryId: number | null
): Promise<DismissStartupResult> {
  const raw = await invoke<IpcResponse<DismissStartupResult>>("ipc_dismiss_startup", {
    projectId,
    startupSummaryId,
  });
  return assertOk(raw);
}
