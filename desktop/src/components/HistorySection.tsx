import type { DashboardProject, HistoryRow } from "../ipc/types";

import { EmptyState } from "./EmptyState";



interface HistorySectionProps {

  project: DashboardProject | null;

  rows: HistoryRow[];

  loading: boolean;

  error: string | null;

  onRetry?: () => void;

}



export function HistorySection({

  project,

  rows,

  loading,

  error,

  onRetry,

}: HistorySectionProps) {

  if (!project) {

    return (

      <EmptyState

        title="History"

        message="Select a project from the dashboard to view scan history."

      />

    );

  }



  return (

    <section className="history-section" aria-label="Scan history">

      <h2>History — {project.name}</h2>

      <p className="muted">Scan snapshots from the local database (read-only).</p>



      {loading ? (

        <div className="panel-loading" aria-busy="true">

          <span className="panel-loading__spinner" aria-hidden="true" />

          <p className="muted">Loading history…</p>

        </div>

      ) : null}



      {error ? (

        <div className="history-section__error">

          <p className="error-text">{error}</p>

          {onRetry ? (

            <button type="button" className="startup__button" onClick={onRetry}>

              Retry

            </button>

          ) : null}

        </div>

      ) : null}



      {!loading && !error && rows.length === 0 ? (

        <EmptyState

          title="No scans yet"

          message="Run graf-id scan <project> from a terminal to capture snapshot history."

        />

      ) : null}



      {!loading && rows.length > 0 ? (

        <table className="history-section__table">

          <thead>

            <tr>

              <th>Snapshot</th>

              <th>Scanned at</th>

              <th>Findings</th>

              <th>Files</th>

              <th>Git</th>

            </tr>

          </thead>

          <tbody>

            {rows.map((row) => (

              <tr key={row.snapshot_id}>

                <td>#{row.snapshot_id}</td>

                <td>{row.scanned_at.replace("T", " ").slice(0, 19)}</td>

                <td>{row.findings_count}</td>

                <td>{row.scanned_files_count}</td>

                <td>

                  {row.is_git_repo

                    ? `${row.git_branch ?? "?"} · ${row.git_dirty ? "dirty" : "clean"}`

                    : "n/a"}

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      ) : null}

    </section>

  );

}

