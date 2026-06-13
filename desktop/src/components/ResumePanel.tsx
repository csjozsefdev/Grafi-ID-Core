import { GrafiHelper } from "./GrafiHelper";
import type { ResumePanelData } from "../ipc/types";
import {
  formatTimeSince,
  formatWhen,
  hasText,
  isStaleProject,
  recommendedAction,
} from "../utils/continuity";
import {
  gitContextLabel,
  scanContextLabel,
  sessionContextLabel,
  taskMarkerLabel,
} from "../utils/selectedProjectCard";

interface ResumePanelProps {
  panel: ResumePanelData | null;
  loading: boolean;
  error: string | null;
  refreshing?: boolean;
  scanHealthNotice?: string | null;
  onRetry?: () => void;
  onRefreshResume?: () => void;
}

function ContextBlock({
  title,
  children,
  tone = "default",
}: {
  title: string;
  children: React.ReactNode;
  tone?: "default" | "primary" | "supporting";
}) {
  const toneClass =
    tone === "primary"
      ? " resume-panel__block--primary"
      : tone === "supporting"
        ? " resume-panel__block--supporting"
        : "";

  return (
    <div className={`resume-panel__block${toneClass}`}>
      <h4>{title}</h4>
      {children}
    </div>
  );
}

function FieldRow({
  label,
  value,
  empty,
}: {
  label: string;
  value: string | null;
  empty: string;
}) {
  return (
    <div>
      <span className="label">{label}</span>
      <p>{value ?? <span className="muted">{empty}</span>}</p>
    </div>
  );
}

export function ResumePanel({
  panel,
  loading,
  error,
  refreshing = false,
  scanHealthNotice = null,
  onRetry,
  onRefreshResume,
}: ResumePanelProps) {
  if (loading) {
    return (
      <section className="resume-panel" aria-label="Resume panel" aria-busy="true">
        <h3>Resume</h3>
        <div className="panel-loading">
          <span className="panel-loading__spinner" aria-hidden="true" />
          <p className="muted">Loading…</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="resume-panel resume-panel--error" aria-label="Resume panel">
        <h3>Resume</h3>
        <p className="error-text">{error}</p>
        {onRetry ? (
          <button type="button" className="startup__button" onClick={onRetry}>
            Retry
          </button>
        ) : null}
      </section>
    );
  }

  if (!panel) {
    return (
      <section className="resume-panel" aria-label="Resume panel">
        <h3>Resume</h3>
        <p className="muted">No resume context loaded for this project.</p>
      </section>
    );
  }

  const blocker = hasText(panel.blocker) ? panel.blocker!.trim() : null;
  const nextStep = hasText(panel.next_step) ? panel.next_step!.trim() : null;
  const exitNote = hasText(panel.exit_note) ? panel.exit_note!.trim() : null;
  const session = panel.latest_session;
  const startup = panel.startup_summary;
  const humanContext =
    (startup?.source === "human_context" || startup?.source === "summary_engine") &&
    hasText(startup.summary_text);
  const action = humanContext
    ? startup!.summary_text!.trim()
    : recommendedAction({
        next_step: nextStep,
        blocker,
        exit_note: exitNote,
        has_unfinished_session: session?.is_active,
      });
  const stale = isStaleProject(panel.last_opened_at);
  const git = panel.git_status;

  return (
    <section className="resume-panel resume-panel--calm" aria-label="Resume panel">
      <div className="resume-panel__toolbar">
        <h3>Resume</h3>
        {onRefreshResume ? (
          <button
            type="button"
            className="startup__button resume-panel__refresh"
            onClick={onRefreshResume}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh context"}
          </button>
        ) : null}
      </div>

      <div className="resume-panel__meta">
        <p className="muted">
          Last opened: {formatWhen(panel.last_opened_at)}
          {formatTimeSince(panel.last_opened_at)
            ? ` (${formatTimeSince(panel.last_opened_at)})`
            : ""}
        </p>
        {session ? (
          <p className="muted">
            {sessionContextLabel(session)}
            {!session.is_active && session.ended_at
              ? ` — ended ${formatWhen(session.ended_at)}`
              : ""}
          </p>
        ) : (
          <p className="muted">{sessionContextLabel(session)}</p>
        )}
        <p className="muted">
          {panel.latest_scan_at
            ? `Latest scan: ${formatWhen(panel.latest_scan_at)}${
                formatTimeSince(panel.latest_scan_at)
                  ? ` (${formatTimeSince(panel.latest_scan_at)})`
                  : ""
              }`
            : scanContextLabel(panel.latest_scan_at)}
        </p>
      </div>

      {stale ? (
        <p className="resume-panel__stale">
          This project has not been opened in over two weeks.
        </p>
      ) : null}

      {session?.is_active && !humanContext ? (
        <p className="resume-panel__active">Session is still open.</p>
      ) : null}

      {panel.last_refreshed_at ? (
        <p className="muted resume-panel__refreshed">
          Last refreshed: {formatWhen(panel.last_refreshed_at)}
          {formatTimeSince(panel.last_refreshed_at)
            ? ` (${formatTimeSince(panel.last_refreshed_at)})`
            : ""}
        </p>
      ) : null}

      {scanHealthNotice ? (
        <p className="resume-panel__scan-health" role="status">
          {scanHealthNotice}
        </p>
      ) : null}

      {(panel.timeline ?? startup?.timeline)?.length ? (
        <ContextBlock title="Recent sessions" tone="supporting">
          <ul className="resume-panel__timeline">
            {(panel.timeline ?? startup?.timeline ?? []).map((entry) => (
              <li key={entry.session_id}>
                <span className="resume-panel__timeline-when">
                  {formatWhen(entry.ended_at ?? entry.started_at)}
                </span>
                {entry.duration_label ? (
                  <span className="muted"> · {entry.duration_label}</span>
                ) : null}
                {entry.exit_note_preview ? (
                  <p className="resume-panel__timeline-note">{entry.exit_note_preview}</p>
                ) : (
                  <p className="muted">No exit note</p>
                )}
              </li>
            ))}
          </ul>
        </ContextBlock>
      ) : null}

      {panel.attributed_lines && panel.attributed_lines.length > 0 ? (
        <ContextBlock title="Context (sources)" tone="supporting">
          <ul className="resume-panel__attributed">
            {panel.attributed_lines.map((line) => (
              <li key={`${line.source}-${line.text}`}>
                <span className="resume-panel__source-tag">[{line.source}]</span> {line.text}
              </li>
            ))}
          </ul>
        </ContextBlock>
      ) : null}

      {startup?.mvp_sections && startup.mvp_sections.length > 0 ? (
        <div className="resume-panel__primary-zone">
          {startup.mvp_sections.map((section) => (
            <ContextBlock key={section.title} title={section.title} tone="primary">
              <p className="resume-panel__answer resume-panel__section-body">{section.body}</p>
            </ContextBlock>
          ))}
        </div>
      ) : (
        <ContextBlock title={humanContext ? "Context" : "Recommended next"} tone="primary">
          <p className="resume-panel__answer">{action}</p>
          {humanContext && panel.sources_used && panel.sources_used.length > 0 ? (
            <p className="muted resume-panel__sources">Sources: {panel.sources_used.join(", ")}</p>
          ) : null}
        </ContextBlock>
      )}

      <div className="resume-panel__grid resume-panel__grid--compact">
        <FieldRow label="Blocker" value={blocker} empty="No blocker recorded." />
        <FieldRow label="Next step" value={nextStep} empty="No next step recorded." />
        <FieldRow label="Last completed" value={exitNote} empty="No exit note recorded yet." />
      </div>

      <ContextBlock title="Git" tone="supporting">
        <p>{gitContextLabel(git)}</p>
      </ContextBlock>

      <ContextBlock title="Task markers" tone="supporting">
        <p className="muted">{taskMarkerLabel(panel.open_task_count)}</p>
      </ContextBlock>

      {panel.modified_files.length > 0 ? (
        <ContextBlock title="Modified files (last scan)" tone="supporting">
          <ul className="resume-panel__files">
            {panel.modified_files.slice(0, 3).map((file) => (
              <li key={file}>{file}</li>
            ))}
          </ul>
          {panel.modified_files.length > 3 ? (
            <p className="muted">+{panel.modified_files.length - 3} more</p>
          ) : null}
        </ContextBlock>
      ) : git.is_git_repo ? (
        <p className="muted">No modified files recorded at last scan.</p>
      ) : null}

      {startup && hasText(startup.headline) && !humanContext ? (
        <ContextBlock title="Workflow context" tone="supporting">
          <p className="resume-panel__headline">{startup.headline}</p>
          {panel.sources_used && panel.sources_used.length > 0 ? (
            <p className="muted">Sources: {panel.sources_used.join(", ")}</p>
          ) : null}
          {startup.generated_at ? (
            <p className="muted">
              Summary generated {formatWhen(startup.generated_at)}
              {formatTimeSince(startup.generated_at)
                ? ` (${formatTimeSince(startup.generated_at)})`
                : ""}
            </p>
          ) : null}
          {hasText(startup.summary_text) && startup.summary_text !== startup.headline ? (
            <p className="muted">{startup.summary_text}</p>
          ) : null}
        </ContextBlock>
      ) : (
        <p className="muted">No previous session summary yet.</p>
      )}

      {panel.stored_resume_excerpt ? (
        <details className="resume-panel__details">
          <summary>Technical details</summary>
          <pre className="resume-panel__excerpt">{panel.stored_resume_excerpt}</pre>
        </details>
      ) : !panel.has_stored_resume ? (
        <p className="muted">No saved resume details available.</p>
      ) : null}

      <GrafiHelper />
    </section>
  );
}
