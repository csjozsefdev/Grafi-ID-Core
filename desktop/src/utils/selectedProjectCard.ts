import type { DashboardProject, ResumePanelData, StartupCardData } from "../ipc/types";
import { hasText, recommendedAction } from "./continuity";

/** Build the top “Where you left off” card from the currently selected project. */
export function buildSelectedProjectCard(
  project: DashboardProject,
  panel: ResumePanelData
): StartupCardData {
  const session = panel.latest_session;
  const startup = panel.startup_summary;
  const nextStep = hasText(panel.next_step) ? panel.next_step!.trim() : null;
  const blocker = hasText(panel.blocker) ? panel.blocker!.trim() : null;
  const exitNote = hasText(panel.exit_note) ? panel.exit_note!.trim() : null;

  const headline =
    (startup?.headline && hasText(startup.headline) ? startup.headline.trim() : null) ??
    (nextStep ? `Next: ${nextStep}` : null) ??
    (blocker ? `Blocker: ${blocker}` : null) ??
    "Where you left off";

  const summaryText = (() => {
    if (startup?.summary_text && hasText(startup.summary_text)) {
      return startup.summary_text.trim();
    }
    if (startup?.source === "human_context") {
      return startup.headline?.trim() || "Where you left off";
    }
    return recommendedAction({
      next_step: nextStep,
      blocker,
      exit_note: exitNote,
      has_unfinished_session: session?.is_active,
    });
  })();

  const scroll =
    startup?.scroll_excerpt?.trim() ||
    (startup?.summary_text && startup.summary_text !== startup.headline
      ? startup.summary_text
      : "") ||
    summaryText;

  return {
    visible: true,
    is_dismissed: false,
    reason: null,
    message: null,
    project_id: project.id,
    project_name: project.name,
    startup_summary_id: null,
    session_id: session?.id ?? null,
    icon_state: startup?.grifi_icon_state ?? "ready",
    headline,
    summary_text: summaryText,
    scroll_content: scroll,
    has_unfinished_session: Boolean(session?.is_active),
    is_empty: !session && !startup && !nextStep && !exitNote && !blocker,
    latest_session: session,
    last_opened_at: panel.last_opened_at ?? project.last_opened_at,
    open_task_count: panel.open_task_count,
    latest_scan_at: panel.latest_scan_at,
    blocker,
    next_step: nextStep,
    exit_note: exitNote,
    modified_files: panel.modified_files,
    git_status: panel.git_status,
    startup_summary: startup,
  };
}

export function scanContextLabel(latestScanAt: string | null | undefined): string {
  if (!latestScanAt) {
    return "No scan has been run for this project yet.";
  }
  return "Latest scan recorded.";
}

export function taskMarkerLabel(count: number | null | undefined): string {
  if (count === null || count === undefined) {
    return "Use Refresh context to scan the project and update TODO/FIXME data.";
  }
  if (count === 0) {
    return "No open TODO/FIXME markers in the latest scan.";
  }
  return `${count} open TODO/FIXME marker${count === 1 ? "" : "s"} in the latest scan.`;
}

export function gitContextLabel(
  git: { state: string; label: string; branch: string | null } | undefined
): string {
  if (!git || git.state === "unknown") {
    return "No git information from the latest scan.";
  }
  return git.branch ? `${git.label} — branch ${git.branch}` : git.label;
}

export function sessionContextLabel(
  session: { is_active: boolean; ended_at: string | null } | null | undefined
): string {
  if (!session) {
    return "No work session recorded yet.";
  }
  if (session.is_active) {
    return "Session is still open.";
  }
  return "Last session has ended.";
}
