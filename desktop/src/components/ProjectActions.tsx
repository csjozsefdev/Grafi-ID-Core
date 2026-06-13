interface ProjectActionsProps {
  disabled: boolean;
  hasActiveSession: boolean;
  onOpenProject: () => void;
  onOpenFolder: () => void;
  onEndSession: () => void;
  onViewHistory: () => void;
  onRemoveProject: () => void;
}

export function ProjectActions({
  disabled,
  hasActiveSession,
  onOpenProject,
  onOpenFolder,
  onEndSession,
  onViewHistory,
  onRemoveProject,
}: ProjectActionsProps) {
  return (
    <div className="project-actions" role="toolbar" aria-label="Project actions">
      <div className="project-actions__secondary">
        <button type="button" disabled={disabled} onClick={onOpenFolder}>
          Open folder
        </button>
        <button
          type="button"
          disabled={disabled || !hasActiveSession}
          onClick={onEndSession}
        >
          End session
        </button>
        <button type="button" disabled={disabled} onClick={onViewHistory}>
          View history
        </button>
        <button
          type="button"
          className="project-actions__remove"
          disabled={disabled}
          onClick={onRemoveProject}
        >
          Remove from Graf-Id
        </button>
      </div>
      <button
        type="button"
        className="project-actions__primary"
        disabled={disabled}
        onClick={onOpenProject}
      >
        Open project
      </button>
    </div>
  );
}
