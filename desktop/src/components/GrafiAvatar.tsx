import type { GrafiIconState } from "../ipc/types";

interface GrafiAvatarProps {
  iconState: GrafiIconState;
}

/** Static Grafi head placeholder (no animation in Milestone 9). */
export function GrafiAvatar({ iconState }: GrafiAvatarProps) {
  return (
    <div className="grafi-avatar" data-state={iconState} aria-hidden="true">
      <svg viewBox="0 0 64 64" width="56" height="56" role="img" aria-label="Grafi">
        <circle cx="32" cy="32" r="30" fill="#3c4043" stroke="#5f6368" strokeWidth="2" />
        <circle cx="24" cy="28" r="4" fill="#e8eaed" />
        <circle cx="40" cy="28" r="4" fill="#e8eaed" />
        <path
          d="M 22 40 Q 32 48 42 40"
          fill="none"
          stroke="#e8eaed"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle
          cx="50"
          cy="14"
          r="6"
          fill={iconState === "attention" ? "#f9ab00" : iconState === "ready" ? "#81c995" : "#5f6368"}
        />
      </svg>
    </div>
  );
}
