/** Static Grafi presence — no chat, no animation. */
export function GrafiHelper() {
  return (
    <aside className="grafi-helper" aria-label="Grafi helper">
      <span className="grafi-helper__icon" aria-hidden="true">
        ◆
      </span>
      <p className="grafi-helper__text muted">
        Local continuity only — summaries come from your notes, handoff files, and scans.
      </p>
    </aside>
  );
}
