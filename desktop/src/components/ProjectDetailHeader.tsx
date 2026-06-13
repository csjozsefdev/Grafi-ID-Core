import type { DashboardProject } from "../ipc/types";
import { formatTimeSince, formatWhen, isStaleProject } from "../utils/continuity";
import { statusLabel } from "../utils/projectStatus";
import { taskMarkerLabel } from "../utils/selectedProjectCard";

function formatCompactPath(path: string): string {
  const trimmed = path.trim();
  if (trimmed.length <= 56) {
    return trimmed;
  }
  const parts = trimmed.replace(/\\/g, "/").split("/").filter(Boolean);
  if (parts.length >= 2) {
    const tail = parts.slice(-2).join("/");
    if (tail.length <= 52) {
      return `…/${tail}`;
    }
  }
  return `…${trimmed.slice(-52)}`;
}

function sessionStateLabel(project: DashboardProject): string {
  const session = project.latest_session;
  if (!session) {
    return "None yet";
  }
  return session.is_active ? "Still open" : "Ended";
}

interface ProjectDetailHeaderProps {
  project: DashboardProject;
}

export function ProjectDetailHeader({ project }: ProjectDetailHeaderProps) {
  const stale = isStaleProject(project.last_opened_at);
  const session = project.latest_session;
  const git = project.git_status;

  return (
    <header className="project-detail__header">
      <div className="project-detail__intro">
        <h2>{project.name}</h2>
        <p className="muted project-detail__path-short" title={project.path}>
          {formatCompactPath(project.path)}
        </p>
      </div>

      <details className="project-detail__more">
        <summary className="project-detail__more-summary">More details</summary>
        <div className="project-detail__more-body">
          {stale ? (
            <p className="project-detail__stale">
              This project has not been opened in over two weeks.
            </p>
          ) : null}

          <dl className="project-detail__facts">
            <div>
              <dt>Path</dt>
              <dd>{project.path}</dd>
            </div>
            <div>
              <dt>Last opened</dt>
              <dd>
                {formatWhen(project.last_opened_at)}
                {formatTimeSince(project.last_opened_at)
                  ? ` (${formatTimeSince(project.last_opened_at)})`
                  : ""}
              </dd>
            </div>
            <div>
              <dt>Session</dt>
              <dd>
                {sessionStateLabel(project)}
                {session?.started_at
                  ? ` — started ${formatWhen(session.started_at)}`
                  : ""}
                {session && !session.is_active && session.ended_at
                  ? ` — ended ${formatWhen(session.ended_at)}`
                  : ""}
              </dd>
            </div>
            <div>
              <dt>Git</dt>
              <dd>
                <span
                  className={`badge badge--git badge--${git?.state ?? "unknown"}`}
                >
                  {git?.label ?? "Unknown"}
                  {git?.branch ? ` (${git.branch})` : ""}
                </span>
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className="project-detail__status-badge">
                  {statusLabel(project.status ?? "active")}
                </span>
              </dd>
            </div>
            <div>
              <dt>Task markers</dt>
              <dd>{taskMarkerLabel(project.open_task_count)}</dd>
            </div>
          </dl>
        </div>
      </details>
    </header>
  );
}
