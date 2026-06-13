import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  AppLoadState,
  DashboardProject,
  HistoryRow,
  NavSection,
  ProjectDetailData,
} from "../ipc/types";
import {
  fetchProjectDetail,
  fetchProjectHistory,
  getUserErrorMessage,
  openProjectFolderPath,
  openProjectWorkflow,
  refreshProjectResume,
  removeProject,
} from "../ipc/client";
import { AddProjectDialog } from "./AddProjectDialog";
import { EndSessionDialog } from "./EndSessionDialog";
import { RemoveProjectDialog } from "./RemoveProjectDialog";
import { EmptyState } from "./EmptyState";
import { HistorySection } from "./HistorySection";
import { NavSidebar } from "./NavSidebar";
import { ProjectActions } from "./ProjectActions";
import { ProjectDetailHeader } from "./ProjectDetailHeader";
import { ResumePanel } from "./ResumePanel";
import { WakePanel } from "./WakePanel";
import { Settings } from "./SettingsPlaceholder";
import { StartupScreen } from "./StartupScreen";
import { sortProjectsByRecency } from "../utils/continuity";
import { hideToTray } from "../utils/hideToTray";
import { mergeDashboardProject } from "../utils/projectMerge";

interface AppShellProps {
  state: AppLoadState;
  onRetry: () => void;
  onProjectAdded: (project: DashboardProject) => void;
  onProjectRemoved: (projectId: number) => void;
}

export function AppShell({ state, onRetry, onProjectAdded, onProjectRemoved }: AppShellProps) {
  const [nav, setNav] = useState<NavSection>("dashboard");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detailCache, setDetailCache] = useState<Record<number, ProjectDetailData>>({});
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [historyRows, setHistoryRows] = useState<HistoryRow[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [projectPatches, setProjectPatches] = useState<Record<number, DashboardProject>>({});
  const [resumeRefreshing, setResumeRefreshing] = useState(false);
  const [openProjectBusy, setOpenProjectBusy] = useState(false);
  const [addProjectOpen, setAddProjectOpen] = useState(false);
  const [endSessionOpen, setEndSessionOpen] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [removeBusy, setRemoveBusy] = useState(false);
  const [removeError, setRemoveError] = useState<string | null>(null);
  const [wakeDismissed, setWakeDismissed] = useState<Record<number, boolean>>({});
  const [scanHealthNotice, setScanHealthNotice] = useState<string | null>(null);

  const bootstrap = state.status === "ready" ? state.bootstrap : null;

  const projects = useMemo(() => {
    const base = bootstrap?.projects ?? [];
    return base.map((project) => {
      const patch = projectPatches[project.id];
      return patch ? mergeDashboardProject(project, patch) : project;
    });
  }, [bootstrap?.projects, projectPatches]);
  const hasProjects = projects.length > 0;

  useEffect(() => {
    if (bootstrap && hasProjects && selectedId === null) {
      const sorted = sortProjectsByRecency(projects);
      setSelectedId(sorted[0]?.id ?? null);
    }
  }, [bootstrap, hasProjects, projects, selectedId]);

  const selectedProject = useMemo(
    () => projects.find((p) => p.id === selectedId) ?? null,
    [projects, selectedId]
  );

  const loadDetail = useCallback(
    async (projectId: number, force = false) => {
      if (!force && detailCache[projectId]) {
        return;
      }
      setDetailLoading(true);
      setDetailError(null);
      try {
        const data = await fetchProjectDetail(projectId);
        setDetailCache((prev) => ({ ...prev, [projectId]: data }));
        setProjectPatches((prev) => {
          const base = bootstrap?.projects.find((p) => p.id === data.project.id);
          return {
            ...prev,
            [data.project.id]: mergeDashboardProject(base, data.project),
          };
        });
      } catch (err) {
        setDetailError(getUserErrorMessage(err));
      } finally {
        setDetailLoading(false);
      }
    },
    [detailCache, bootstrap?.projects]
  );

  const handleRefreshResume = useCallback(async () => {
    if (selectedId === null) return;
    setResumeRefreshing(true);
    setDetailError(null);
    try {
      const data = await refreshProjectResume(selectedId);
      setProjectPatches((prev) => {
        const base = bootstrap?.projects.find((p) => p.id === data.project.id);
        return {
          ...prev,
          [data.project.id]: mergeDashboardProject(base, data.project),
        };
      });
      setDetailCache((prev) => {
        const existing = prev[selectedId];
        return {
          ...prev,
          [selectedId]: {
            project: data.project,
            resume_panel: data.resume_panel,
            history: existing?.history ?? [],
          },
        };
      });
      const health = data.scan_health;
      if (health?.messages?.length) {
        setScanHealthNotice(health.messages.join(" · "));
      } else if (data.refresh && !data.refresh.scan_ok) {
        setScanHealthNotice(data.refresh.scan_error ?? "Scan did not complete.");
      } else {
        setScanHealthNotice(null);
      }
      setActionNotice("Project context updated.");
    } catch (err) {
      setDetailError(getUserErrorMessage(err));
    } finally {
      setResumeRefreshing(false);
    }
  }, [selectedId, bootstrap?.projects]);

  useEffect(() => {
    if (selectedId !== null) {
      setDetailError(null);
      void loadDetail(selectedId, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refresh when selection changes only
  }, [selectedId]);

  const loadHistory = useCallback(async (projectId: number) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const rows = await fetchProjectHistory(projectId);
      setHistoryRows(rows);
    } catch (err) {
      setHistoryError(getUserErrorMessage(err));
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (nav === "history" && selectedId !== null) {
      void loadHistory(selectedId);
    }
  }, [nav, selectedId, loadHistory]);

  const detail = selectedId !== null ? detailCache[selectedId] : undefined;
  const resumePanel = detail?.resume_panel ?? null;
  const showWake =
    selectedId !== null &&
    resumePanel &&
    !wakeDismissed[selectedId] &&
    Boolean(
      resumePanel.away_label ??
        resumePanel.startup_summary?.away_label
    );

  const handleSessionEnded = useCallback(() => {
    if (selectedId !== null) {
      void loadDetail(selectedId, true);
      setActionNotice("Session ended. Resume context updated.");
    }
  }, [loadDetail, selectedId]);

  if (state.status === "loading") {
    return (
      <div className="app-shell app-shell--centered">
        <StartupScreen
          loading
          errorTitle={null}
          errorMessage={null}
          onRetry={onRetry}
        />
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="app-shell app-shell--centered">
        <StartupScreen
          loading={false}
          errorTitle={state.title}
          errorMessage={state.message}
          onRetry={onRetry}
        />
      </div>
    );
  }

  // Open Project: Python workflow + optional single Rust Explorer (see launch.open_explorer).
  const handleOpenProject = async () => {
    if (!selectedId || !selectedProject || openProjectBusy) return;
    setOpenProjectBusy(true);
    setActionNotice(null);
    setDetailError(null);
    try {
      const result = await openProjectWorkflow(selectedId);
      setProjectPatches((prev) => {
        const base = bootstrap?.projects.find((p) => p.id === result.project.id);
        return {
          ...prev,
          [result.project.id]: mergeDashboardProject(base, result.project),
        };
      });
      const launch = result.launch;
      const editorLaunched =
        launch.success !== false &&
        launch.editor_launched &&
        !launch.fallback_used;

      if (launch.explorer_opened && !editorLaunched) {
        await openProjectFolderPath(selectedProject.path);
      }

      if (editorLaunched) {
        await hideToTray();
        return;
      }

      const notice =
        launch.fallback_used && launch.message
          ? `Warning: ${launch.message}`
          : launch.message;
      setActionNotice(notice);
      await loadDetail(selectedId, true);
    } catch (err) {
      setActionNotice(`Open project failed: ${getUserErrorMessage(err)}`);
    } finally {
      setOpenProjectBusy(false);
    }
  };

  const handleProjectAdded = (project: DashboardProject, message: string) => {
    onProjectAdded(project);
    setProjectPatches((prev) => {
      const base = bootstrap?.projects.find((p) => p.id === project.id);
      return {
        ...prev,
        [project.id]: mergeDashboardProject(base, project),
      };
    });
    setSelectedId(project.id);
    setNav("dashboard");
    setActionNotice(message);
    void loadDetail(project.id, true);
  };

  const handleRemoveProject = async () => {
    if (!selectedId || !selectedProject) return;
    setRemoveBusy(true);
    setRemoveError(null);
    try {
      const result = await removeProject(selectedId);
      const removedId = selectedId;
      onProjectRemoved(removedId);
      setProjectPatches((prev) => {
        const next = { ...prev };
        delete next[removedId];
        return next;
      });
      setDetailCache((prev) => {
        const next = { ...prev };
        delete next[removedId];
        return next;
      });
      const remaining = projects.filter((p) => p.id !== removedId);
      const nextSelected = sortProjectsByRecency(remaining)[0]?.id ?? null;
      setSelectedId(nextSelected);
      setRemoveDialogOpen(false);
      setActionNotice(result.message);
    } catch (err) {
      setRemoveError(getUserErrorMessage(err));
    } finally {
      setRemoveBusy(false);
    }
  };

  return (
    <div className={`app-shell${!hasProjects ? " app-shell--no-projects" : ""}`}>
      <header className="app-shell__titlebar">
        <span className="app-shell__logo">Graf-Id</span>
        <span className="app-shell__tag">Local workflow continuity · Passive runtime</span>
      </header>
      <div className="app-shell__body">
        <NavSidebar
          section={nav}
          onNav={setNav}
          hasProjects={hasProjects}
          projects={projects}
          selectedId={selectedId}
          onSelectProject={setSelectedId}
          onAddProject={() => setAddProjectOpen(true)}
        />
        <main className="app-shell__main">
          {!hasProjects && nav === "dashboard" ? (
            <EmptyState
              title="No projects yet"
              message="Register a project folder to start tracking where you left off. Graf-Id remembers sessions, scans, and resume context for registered projects."
              dataFolder={bootstrap?.config_dir}
              hint="Add a project folder to get started. Use Open project to launch your editor."
              onAddProject={() => setAddProjectOpen(true)}
            />
          ) : null}

          {actionNotice ? (
            <p className="app-shell__notice" role="status">
              {actionNotice}
            </p>
          ) : null}

          {hasProjects && nav === "dashboard" ? (
            selectedProject ? (
              <section className="project-detail">
                <ProjectDetailHeader project={selectedProject} />

                <ProjectActions
                  disabled={openProjectBusy || resumeRefreshing}
                  hasActiveSession={Boolean(selectedProject.latest_session?.is_active)}
                  onOpenProject={() => void handleOpenProject()}
                  onOpenFolder={() => {
                    void openProjectFolderPath(selectedProject.path).catch((err) =>
                      setActionNotice(getUserErrorMessage(err))
                    );
                  }}
                  onEndSession={() => setEndSessionOpen(true)}
                  onViewHistory={() => setNav("history")}
                  onRemoveProject={() => {
                    setRemoveError(null);
                    setRemoveDialogOpen(true);
                  }}
                />

                {showWake && resumePanel ? (
                  <WakePanel
                    panel={resumePanel}
                    onContinue={() =>
                      setWakeDismissed((prev) => ({
                        ...prev,
                        [selectedId!]: true,
                      }))
                    }
                  />
                ) : null}

                <ResumePanel
                  panel={resumePanel}
                  loading={detailLoading && !detail}
                  error={detailError}
                  refreshing={resumeRefreshing}
                  scanHealthNotice={scanHealthNotice}
                  onRetry={
                    selectedId !== null
                      ? () => void loadDetail(selectedId, true)
                      : undefined
                  }
                  onRefreshResume={
                    selectedId !== null
                      ? () => void handleRefreshResume()
                      : undefined
                  }
                />
              </section>
            ) : (
              <EmptyState
                title="Select a project"
                message="Choose a project from the sidebar to view resume context and continue where you left off."
              />
            )
          ) : null}

          {hasProjects && nav === "history" ? (
            <HistorySection
              project={selectedProject}
              rows={historyRows}
              loading={historyLoading}
              error={historyError}
              onRetry={
                selectedId !== null ? () => void loadHistory(selectedId) : undefined
              }
            />
          ) : null}

          {nav === "settings" ? <Settings /> : null}
        </main>
      </div>

      <AddProjectDialog
        open={addProjectOpen}
        onClose={() => setAddProjectOpen(false)}
        onAdded={handleProjectAdded}
      />

      <EndSessionDialog
        open={endSessionOpen}
        projectId={selectedId}
        onClose={() => setEndSessionOpen(false)}
        onEnded={handleSessionEnded}
      />

      {selectedProject ? (
        <RemoveProjectDialog
          open={removeDialogOpen}
          projectName={selectedProject.name}
          removing={removeBusy}
          error={removeError}
          onConfirm={() => void handleRemoveProject()}
          onCancel={() => {
            if (!removeBusy) {
              setRemoveDialogOpen(false);
              setRemoveError(null);
            }
          }}
        />
      ) : null}
    </div>
  );
}
