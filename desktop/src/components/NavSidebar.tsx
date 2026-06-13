import type { DashboardProject, NavSection } from "../ipc/types";
import { ProjectDashboard } from "./ProjectDashboard";

interface NavSidebarProps {
  section: NavSection;
  onNav: (section: NavSection) => void;
  hasProjects: boolean;
  projects: DashboardProject[];
  selectedId: number | null;
  onSelectProject: (id: number) => void;
  onAddProject: () => void;
}

const NAV_ITEMS: { id: NavSection; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "history", label: "History" },
  { id: "settings", label: "Settings" },
];

export function NavSidebar({
  section,
  onNav,
  hasProjects,
  projects,
  selectedId,
  onSelectProject,
  onAddProject,
}: NavSidebarProps) {
  return (
    <aside className="sidebar" aria-label="Navigation">
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              section === item.id ? "sidebar__nav-btn sidebar__nav-btn--active" : "sidebar__nav-btn"
            }
            onClick={() => onNav(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {hasProjects ? (
        <ProjectDashboard
          projects={projects}
          selectedId={selectedId}
          onSelect={onSelectProject}
          onAddProject={onAddProject}
        />
      ) : (
        <p className="sidebar__hint muted">
          Add a project to start tracking where you left off.
        </p>
      )}
    </aside>
  );
}
