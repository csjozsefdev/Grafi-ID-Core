import { useMemo, useState } from "react";
import type { DashboardProject } from "../ipc/types";
import {
  formatTimeSince,
  sidebarGitChip,
  sidebarSessionChip,
  sidebarSummaryPreviewText,
  sortProjectsByRecency,
  summaryPreviewText,
} from "../utils/continuity";
import {
  PROJECT_CATEGORIES,
  groupProjectsByCategory,
} from "../utils/projectCategories";
import { PROJECT_STATUSES, statusLabel } from "../utils/projectStatus";

interface ProjectDashboardProps {
  projects: DashboardProject[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onAddProject: () => void;
}

function ProjectListItem({
  project,
  isSelected,
  onSelect,
}: {
  project: DashboardProject;
  isSelected: boolean;
  onSelect: (id: number) => void;
}) {
  const summary = sidebarSummaryPreviewText(project);
  const summaryTitle = summaryPreviewText(project);
  const sessionChip = sidebarSessionChip(project.latest_session);
  const gitChip = sidebarGitChip(project.git_status?.state);
  const lastOpened = formatTimeSince(project.last_opened_at);

  return (
    <button
      type="button"
      role="option"
      aria-selected={isSelected}
      className={
        isSelected
          ? "project-dashboard__item project-dashboard__item--active"
          : "project-dashboard__item"
      }
      onClick={() => onSelect(project.id)}
    >
      <span className="project-dashboard__item-name">{project.name}</span>
      <span className="project-dashboard__item-summary" title={summaryTitle}>
        {summary}
      </span>
      <span className="sidebar__project-meta" aria-label="Project status">
        <span
          className={`sidebar__project-chip sidebar__project-chip--session${
            sessionChip === "Active" ? " sidebar__project-chip--session-active" : ""
          }`}
        >
          {sessionChip}
        </span>
        <span
          className={`sidebar__project-chip sidebar__project-chip--git sidebar__project-chip--git-${gitChip === "Dirty" ? "dirty" : gitChip === "Clean" ? "clean" : "none"}`}
        >
          {gitChip}
        </span>
        {lastOpened ? (
          <span className="sidebar__project-chip sidebar__project-chip--time">{lastOpened}</span>
        ) : null}
      </span>
    </button>
  );
}

export function ProjectDashboard({
  projects,
  selectedId,
  onSelect,
  onAddProject,
}: ProjectDashboardProps) {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const grouped = useMemo(() => groupProjectsByCategory(projects), [projects]);

  const visibleProjects = useMemo(() => {
    let list =
      activeCategory === "all"
        ? projects
        : (grouped.get(activeCategory) ?? []);
    if (statusFilter !== "all") {
      list = list.filter((p) => (p.status ?? "active") === statusFilter);
    }
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.path.toLowerCase().includes(q) ||
          (p.category ?? "").toLowerCase().includes(q)
      );
    }
    return sortProjectsByRecency(list);
  }, [activeCategory, grouped, projects, searchQuery, statusFilter]);

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const category of PROJECT_CATEGORIES) {
      counts.set(category, grouped.get(category)?.length ?? 0);
    }
    return counts;
  }, [grouped]);

  if (projects.length === 0) {
    return null;
  }

  return (
    <div className="sidebar__projects" aria-label="Project picker">
      <div className="sidebar__projects-head">
        <h2>Projects</h2>
        <button type="button" className="sidebar__add-project" onClick={onAddProject}>
          Add project
        </button>
      </div>

      <div className="project-dashboard__filters sidebar__project-filters">
        <label className="project-dashboard__search">
          Search
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Name or path"
          />
        </label>
        <label>
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All statuses</option>
            {PROJECT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div
        className="project-dashboard__categories sidebar__project-categories"
        role="tablist"
        aria-label="Project categories"
      >
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === "all"}
          className={
            activeCategory === "all"
              ? "project-dashboard__category project-dashboard__category--active"
              : "project-dashboard__category"
          }
          onClick={() => setActiveCategory("all")}
        >
          All ({projects.length})
        </button>
        {PROJECT_CATEGORIES.map((category) => {
          const count = categoryCounts.get(category) ?? 0;
          if (count === 0 && activeCategory !== category) {
            return null;
          }
          return (
            <button
              key={category}
              type="button"
              role="tab"
              aria-selected={activeCategory === category}
              className={
                activeCategory === category
                  ? "project-dashboard__category project-dashboard__category--active"
                  : "project-dashboard__category"
              }
              onClick={() => setActiveCategory(category)}
            >
              {category} ({count})
            </button>
          );
        })}
      </div>

      <div
        className="project-dashboard__list-wrap sidebar__project-list-wrap"
        role="listbox"
        aria-label="Project list"
      >
        {visibleProjects.length === 0 ? (
          <p className="muted project-dashboard__empty-category sidebar__empty">
            No projects in {activeCategory === "all" ? "any category" : activeCategory}.
          </p>
        ) : (
          <div className="project-dashboard__list">
            {visibleProjects.map((project) => (
              <ProjectListItem
                key={project.id}
                project={project}
                isSelected={project.id === selectedId}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
